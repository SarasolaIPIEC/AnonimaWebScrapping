import os
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Dict, Any, List, Optional, Set

from .extract import parse_price_ar, extract_card_fields
from .utils import json_log, build_product_url, DEFAULT_SITE_BASE
from ..normalize.units import parse_title_size


def _try_loc(page, specs):
    import re as _re
    for spec in specs:
        loc = None
        if 'placeholder' in spec:
            loc = page.get_by_placeholder(_re.compile(spec['placeholder']))
        elif 'role' in spec:
            name = _re.compile(spec['name']) if spec.get('name') else None
            loc = page.get_by_role(spec['role'], name=name)
        elif 'text' in spec:
            loc = page.get_by_text(_re.compile(spec['text']))
        elif 'css' in spec:
            loc = page.locator(spec['css'])
        if loc:
            try:
                loc.first.wait_for(state='attached', timeout=2000)
                return loc.first
            except Exception:
                continue
    return None


def _dismiss_overlays(page):
    try:
        page.evaluate("document.querySelectorAll('[data-modal], .modal-overlay, .reveal-overlay').forEach(el => el.style.display='none')")
    except Exception:
        pass
    try:
        page.evaluate("document.querySelectorAll('#onesignal-slidedown-container, .onesignal-slidedown-container').forEach(el => el.remove())")
    except Exception:
        pass
    close_specs = [
        {"css": "[data-modal-close], .modal-close, .onesignal-slidedown-close-button"},
        {"role": "button", "name": "(?i)(no gracias|no, gracias|cerrar|rechazar|cerrar mensaje|ahora no)"},
    ]
    for spec in close_specs:
        try:
            loc = _try_loc(page, [spec])
            if loc and loc.is_visible():
                loc.click()
                page.wait_for_timeout(200)
        except Exception:
            continue


def _build_query(row: Dict[str, Any]) -> str:
    # Objetivo: "arroz 1 kg", "aceite girasol 1.5 l", "leche 1 l", "huevos docena"
    exp_unit = row.get('expected_unit', '').lower()
    exp_qty = row.get('expected_qty', '')
    try:
        exp_qty = float(exp_qty)
    except Exception:
        exp_qty = 0
    # base por keywords preferidas
    kws = [s for s in row.get('preferred_keywords', []) if s]
    if kws:
        base = ' '.join(kws[:2])
    else:
        # fallback: nombre sin tamaÃ±os
        base = re.sub(r"\b\d+[\.,]?\d*\s*(kg|kilo|g|gr|l|lt|ml|cc|unidad|docena)\b", "", row['name'], flags=re.I).strip()
    unit_str = ''
    if exp_unit in ('kg', 'l') and exp_qty:
        if exp_unit == 'kg' and exp_qty < 1:
            unit_str = f" {int(exp_qty*1000)} g"
        elif exp_unit == 'l' and exp_qty < 1:
            unit_str = f" {int(exp_qty*1000)} ml"
        else:
            unit_str = f" {exp_qty:g} {exp_unit}"
    elif exp_unit == 'unit' and exp_qty == 12:
        unit_str = " docena"
    return f"{base}{unit_str}".strip()


STOPWORDS = {
    "kg",
    "g",
    "gr",
    "gramos",
    "l",
    "lt",
    "litro",
    "ml",
    "cc",
    "x",
    "con",
    "de",
    "del",
    "la",
    "el",
    "los",
    "las",
    "para",
    "por",
    "sin",
    "en",
    "y",
    "al",
    "docena",
    "pack",
    "bolsa",
    "bolsita",
    "unidad",
    "un",
    "una",
    "granel",
}

CATEGORY_HINTS = {
    "carnes": {"carne", "pollo", "vacuna", "cerdo", "picada"},
    "panaderia": {"pan", "fresco"},
    "lÃ¡cteos": {"leche", "queso", "cremoso"},
    "lacteos": {"leche", "queso", "cremoso"},
    "huevos": {"huevo"},
    "verduras": {"papa", "verdura"},
    "frutas": {"manzana", "fruta"},
    "fideos": {"fideo", "pasta"},
    "arroz": {"arroz"},
    "legumbres": {"lenteja", "legumbre"},
    "azÃºcar": {"azucar"},
    "azucar": {"azucar"},
    "aceite": {"aceite"},
    "bebidas": {"gaseosa", "bebida"},
}

MIN_ACCEPT_SCORE = 0.25


def _normalize_text(value: str) -> str:
    if not value:
        return ""
    nfkd = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    return ascii_text.lower().strip()


def _tokenize(value: str) -> List[str]:
    norm = _normalize_text(value)
    return [tok for tok in re.split(r"[^a-z0-9]+", norm) if tok]


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _essential_tokens(row: Dict[str, Any]) -> Set[str]:
    essentials: Set[str] = set()
    for kw in row.get('preferred_keywords', []):
        norm = _normalize_text(kw)
        if norm:
            essentials.add(norm)
    for token in _tokenize(row.get('name', '')):
        if token and token not in STOPWORDS and not token.isdigit():
            essentials.add(token)
    category = (row.get('category') or '').lower()
    if category:
        essentials.update(CATEGORY_HINTS.get(category, set()))
    return essentials


def _prepare_search_input(page, specs):
    sinput = _try_loc(page, specs)
    if not sinput:
        raise RuntimeError('No se encontrÃ³ input de bÃºsqueda (search_input)')
    for _ in range(3):
        try:
            sinput.click()
            return sinput
        except Exception:
            _dismiss_overlays(page)
            page.wait_for_timeout(100)
    try:
        sinput.click(force=True)
    except Exception:
        _dismiss_overlays(page)
    return sinput


def _locate_cards(page, card_specs):
    cards_loc = None
    for spec in card_specs:
        try:
            cand = page.locator(spec.get('css') or '[data-product-card]') if 'css' in spec else None
            if cand and cand.count() > 0:
                cand.first.wait_for(state='attached', timeout=5000)
                cards_loc = cand
                break
        except Exception:
            continue
    if not cards_loc:
        cards_loc = page.locator('article')
    return cards_loc


def _score_card(row: Dict[str, Any], title: str, in_stock: bool, unit_price: float, qty_base: float, exclude_keywords: List[str]) -> Optional[float]:
    score = 0.0
    title_norm = _normalize_text(title)
    name_tokens = _tokenize(row.get('name', ''))
    title_tokens = _tokenize(title)
    essentials = _essential_tokens(row)
    essential_hits = len(essentials & set(title_tokens))
    if essentials and essential_hits == 0:
        return None

    for kw in row['preferred_keywords']:
        kw_norm = _normalize_text(kw)
        if not kw_norm:
            continue
        if kw_norm in title_norm:
            score += 2.0
            continue
        if _similarity(kw_norm, title_norm) >= 0.65:
            score += 1.0
    if row.get('fallback_keywords'):
        for kw in row['fallback_keywords']:
            kw_norm = _normalize_text(kw)
            if not kw_norm:
                continue
            if kw_norm in title_norm:
                score += 0.5
            elif _similarity(kw_norm, title_norm) >= 0.7:
                score += 0.25

    shared = len(set(name_tokens) & set(title_tokens))
    if shared:
        score += 1.5 * (shared / max(1, len(name_tokens)))

    for ex in exclude_keywords:
        ex_norm = _normalize_text(ex)
        if ex_norm and ex_norm in title_norm:
            score -= 2.0
    if essentials and essential_hits:
        score += 1.5 * essential_hits
    # size proximity
    exp_qty = float(row.get('expected_qty') or 0)
    tol = float(row.get('size_tolerance') or 0.85)
    if qty_base and exp_qty:
        ratio = min(qty_base, exp_qty) / max(qty_base, exp_qty)
        if ratio >= tol:
            score += 2.0
        elif ratio >= min(0.75, tol - 0.15):
            score += 1.0
    # stock
    if not in_stock:
        score -= 3.0
    # lower unit price better (we don't add to score, used for tiebreak)
    return score


def run_searches(page, period: str, catalog: List[Dict[str, Any]], selectors: Dict[str, Any], evidence_dir: str, html_dump_dir: str, exclude_keywords: List[str], log_path: str, base_url: str = DEFAULT_SITE_BASE) -> List[Dict[str, Any]]:
    # SelecciÃ³n de sucursal Ushuaia (9410)
    location_btn = _try_loc(page, selectors.get('location_button', []))
    if location_btn:
        location_btn.click()
        page.wait_for_timeout(500)
        postal_input = _try_loc(page, selectors.get('postal_input', []))
        if postal_input:
            postal_input.fill('9410')
            page.wait_for_timeout(500)
        branch_opt = _try_loc(page, selectors.get('branch_option', []))
        if branch_opt:
            branch_opt.click()
            page.wait_for_timeout(300)
            confirm_btn = _try_loc(page, selectors.get('confirm_button', []))
            if confirm_btn:
                confirm_btn.click()
                page.wait_for_timeout(500)
    search_input_specs = selectors.get('search_input', [])
    card_specs = selectors.get('product_card_root', [])

    results: List[Dict[str, Any]] = []

    _dismiss_overlays(page)

    for row in catalog:
        _dismiss_overlays(page)
        query = _build_query(row)
        sinput = _try_loc(page, search_input_specs)
        if not sinput:
            raise RuntimeError('No se encontrÃ³ input de bÃºsqueda (search_input).')
        clicked = False
        try:
            sinput.click()
            clicked = True
        except Exception:
            _dismiss_overlays(page)
        if not clicked:
            try:
                sinput.click(force=True)
                clicked = True
            except Exception:
                _dismiss_overlays(page)
        if not clicked:
            try:
                page.evaluate("document.querySelectorAll('.reveal-overlay').forEach(el => el.remove())")
            except Exception:
                pass
            try:
                sinput.click(force=True)
            except Exception:
                pass
        sinput.fill('')
        sinput.type(query)
        sinput.press('Enter')

        # wait basic grid content
        page.wait_for_load_state('domcontentloaded')
        try:
            page.wait_for_selector("#productos-container .producto-item", timeout=6000)
        except Exception:
            pass
        page.wait_for_timeout(1000)
        _dismiss_overlays(page)

        # evidence
        safe_q = re.sub(r'[^a-z0-9]+', '_', query.lower())
        page.screenshot(path=os.path.join(evidence_dir, f'search_{safe_q}.png'), full_page=True)
        with open(os.path.join(html_dump_dir, f'search_{safe_q}.html'), 'w', encoding='utf-8') as f:
            f.write(page.content())

        # collect cards
        cards_loc = None
        for spec in card_specs:
            try:
                cand = page.locator(spec.get('css') or '[data-product-card]') if 'css' in spec else None
                if cand and cand.count() > 0:
                    cand.first.wait_for(state='attached', timeout=5000)
                    cards_loc = cand
                    break
            except Exception:
                continue
        if not cards_loc:
            # fallback to article
            cards_loc = page.locator('article')

        # attempt to load more results via infinite scroll if applicable
        try:
            prev = -1
            for _ in range(6):  # up to ~6 pages
                count = cards_loc.count()
                if count <= prev:
                    break
                prev = count
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(700)
        except Exception:
            pass

        candidates = []
        # current page + try next pages if available
        for _page_i in range(1, 4):
            total = min(cards_loc.count(), 60)
            for i in range(total):
                card = cards_loc.nth(i)
                fields = extract_card_fields(page, card, selectors)
                if fields.get('url'):
                    try:
                        normalized_url = build_product_url(fields['url'], base_url=base_url or None)
                        if normalized_url in seen_urls:
                            continue
                        fields['url'] = normalized_url
                        seen_urls.add(normalized_url)
                    except Exception:
                        pass
                title = fields.get('title', '')
                price = fields.get('price_final')
                in_stock = fields.get('in_stock', True)
                qty_base, unit = parse_title_size(title)
                unit_price = (price / qty_base) if price and qty_base else None
                score = _score_card(row, title, in_stock, unit_price if unit_price else 0, qty_base or 0, exclude_keywords)
                if score is None or score < MIN_ACCEPT_SCORE:
                    continue
                candidates.append((score if score is not None else 0.0, unit_price if unit_price else 1e12, fields, qty_base or 0.0, unit or ''))
            # try go next page
            pagination_next_specs = selectors.get('pagination_next', [])
            next_btn = _try_loc(page, pagination_next_specs)
            try:
                if next_btn and next_btn.is_enabled():
                    next_btn.click()
                    page.wait_for_load_state('domcontentloaded')
                    page.wait_for_timeout(800)
                    # refresh cards locator for new page
                    cards_loc = None
                    for spec in card_specs:
                        try:
                            cand = page.locator(spec.get('css') or '[data-product-card]') if 'css' in spec else None
                            if cand and cand.count() > 0:
                                cand.first.wait_for(state='attached', timeout=5000)
                                cards_loc = cand
                                break
                        except Exception:
                            continue
                    if not cards_loc:
                        cards_loc = page.locator('article')
                    # scroll again on new page
                    try:
                        prev = -1
                        for _ in range(6):
                            count = cards_loc.count()
                            if count <= prev:
                                break
                            prev = count
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            page.wait_for_timeout(700)
                    except Exception:
                        pass
                else:
                    break
            except Exception:
                break

        chosen = None
        if candidates:
            candidates.sort(key=lambda t: (-t[0], t[1]))
            best = candidates[0]
            fields = best[2]
            fields.update({
                'item_id': row['item_id'],
                'name': row['name'],
                'query': query,
                'qty_base': best[3],
                'unit': best[4],
                'expected_qty': row['expected_qty'],
                'monthly_qty_base': row['monthly_qty_base'],
                'substitution': ''
            })
            chosen = fields
        if not chosen and row['fallback_keywords']:
            json_log(log_path, 'substitution', {'item_id': row['item_id'], 'reason': 'no acceptable candidate'})
        if chosen:
            json_log(log_path, 'selected', {
                'item_id': chosen['item_id'],
                'title': chosen.get('title'),
                'price_final': chosen.get('price_final'),
                'qty_base': chosen.get('qty_base'),
                'unit': chosen.get('unit')
            })
            results.append(chosen)
    return results

