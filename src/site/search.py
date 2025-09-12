import os
import re
from typing import Dict, Any, List
from urllib.parse import urljoin

from .extract import parse_price_ar, extract_card_fields
from .utils import json_log
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
        # fallback: nombre sin tamaños
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


def _score_card(row: Dict[str, Any], title: str, in_stock: bool, unit_price: float, qty_base: float, exclude_keywords: List[str]) -> float:
    score = 0.0
    for kw in row['preferred_keywords']:
        if kw and re.search(re.escape(kw), title, re.I):
            score += 2.0
    for ex in exclude_keywords:
        if ex and re.search(re.escape(ex), title, re.I):
            score -= 2.0
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


def run_searches(page, period: str, catalog: List[Dict[str, Any]], selectors: Dict[str, Any], evidence_dir: str, html_dump_dir: str, exclude_keywords: List[str], log_path: str, base_url: str = "") -> List[Dict[str, Any]]:
    search_input_specs = selectors.get('search_input', [])
    card_specs = selectors.get('product_card_root', [])

    results: List[Dict[str, Any]] = []

    for row in catalog:
        query = _build_query(row)
        sinput = _try_loc(page, search_input_specs)
        if not sinput:
            raise RuntimeError('No se encontró input de búsqueda (search_input).')
        sinput.click()
        sinput.fill('')
        sinput.type(query)
        sinput.press('Enter')

        # wait basic grid content
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_timeout(1000)

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
                # Build absolute URL if relative
                if fields.get('url') and base_url and fields['url'].startswith('/'):
                    fields['url'] = urljoin(base_url, fields['url'])
                title = fields.get('title', '')
                price = fields.get('price_final')
                in_stock = fields.get('in_stock', True)
                qty_base, unit = parse_title_size(title)
                unit_price = (price / qty_base) if price and qty_base else None
                score = _score_card(row, title, in_stock, unit_price if unit_price else 0, qty_base or 0, exclude_keywords)
                candidates.append((score, unit_price if unit_price else 1e12, fields, qty_base or 0.0, unit or ''))
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
