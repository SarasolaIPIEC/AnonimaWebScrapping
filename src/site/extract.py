import re
from typing import Dict, Any


def parse_price_ar(text: str):
    if not text:
        return None
    t = text.strip().replace('\u00A0', ' ').replace(' ', '')  # remove nbsp/spaces
    # Accept patterns like $1.400,00 or $2100.00 or $1400
    m = re.search(r"\$\s*([\d\.,]+)", t)
    if not m:
        # sometimes text may already be just a number
        m = re.search(r"([\d\.,]+)", t)
        if not m:
            return None
    num = m.group(1)
    if ',' in num and '.' in num:
        # assume dot thousands, comma decimals
        num = num.replace('.', '').replace(',', '.')
    elif ',' in num and '.' not in num:
        # assume comma decimals
        num = num.replace('.', '').replace(',', '.')
    # else dot decimals or integer
    try:
        return float(num)
    except Exception:
        return None


def _loc_try(card, page, specs):
    import re as _re
    for spec in specs:
        if 'css' in spec:
            l = card.locator(spec['css'])
        elif 'text' in spec:
            l = card.get_by_text(_re.compile(spec['text']))
        elif 'role' in spec:
            name = _re.compile(spec['name']) if spec.get('name') else None
            l = card.get_by_role(spec['role'], name=name)
        else:
            continue
        try:
            if l and l.count() > 0:
                return l.first
        except Exception:
            continue
    return None


def extract_card_fields(page, card, selectors: Dict[str, Any]) -> Dict[str, Any]:
    title_specs = selectors.get('title', [])
    price_specs = selectors.get('price_now', [])
    oos_specs = selectors.get('oos_flag', [])
    add_specs = selectors.get('add_to_cart_button', [])

    title_text = ''
    try:
        tl = _loc_try(card, page, title_specs)
        if tl:
            title_text = tl.inner_text().strip()
    except Exception:
        title_text = ''

    # Prefer "Ahora" price if both Antes/Ahora present
    price_text = ''
    price_original_text = ''
    try:
        # Look for explicit "Ahora" and "Antes" in full card text
        full = card.inner_text()
        m_now = re.search(r"Ahora[^$]*\$\s*([\d\.,]+)", full, re.I)
        m_before = re.search(r"Antes[^$]*\$\s*([\d\.,]+)", full, re.I)
        if m_now:
            price_text = f"$ {m_now.group(1)}"
        pl = _loc_try(card, page, price_specs)
        if not price_text and pl:
            price_text = pl.inner_text().strip()
        if m_before:
            price_original_text = f"$ {m_before.group(1)}"
        if not price_original_text:
            pol = _loc_try(card, page, selectors.get('price_original', []))
            if pol:
                price_original_text = pol.inner_text().strip()
    except Exception:
        price_text = ''

    in_stock = True
    try:
        if _loc_try(card, page, oos_specs):
            in_stock = False
    except Exception:
        pass
    # Add-to-cart button heuristic
    try:
        btn = _loc_try(card, page, add_specs)
        if btn:
            try:
                if not btn.is_enabled() or not btn.is_visible():
                    in_stock = False
            except Exception:
                pass
    except Exception:
        pass

    promo_flag = False
    try:
        # Heuristic: presence of Antes price or class
        if card.get_by_text(re.compile(r'Antes', re.I)).count() > 0:
            promo_flag = True
    except Exception:
        pass

    url = ''
    try:
        a = card.locator('a').first
        href = a.get_attribute('href')
        url = href or ''
    except Exception:
        url = ''

    price = parse_price_ar(price_text) if price_text else None
    price_original = parse_price_ar(price_original_text) if price_original_text else None
    if price and not price_original:
        price_original = price

    return {
        'title': title_text,
        'price_final': price,
        'promo_flag': promo_flag or (price_original and price and price_original > price),
        'in_stock': in_stock,
        'url': url,
        'price_original': price_original,
        'price_promo': price if promo_flag else None,
    }
