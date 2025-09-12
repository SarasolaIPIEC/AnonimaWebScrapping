import os
import re
from typing import Dict, Any, Optional

from urllib.parse import urljoin


def _page_first(page, specs):
    import re as _re
    for spec in specs:
        if 'css' in spec:
            l = page.locator(spec['css'])
        elif 'role' in spec:
            name = _re.compile(spec['name']) if spec.get('name') else None
            l = page.get_by_role(spec['role'], name=name)
        elif 'text' in spec:
            l = page.get_by_text(_re.compile(spec['text']))
        elif 'placeholder' in spec:
            l = page.get_by_placeholder(_re.compile(spec['placeholder']))
        else:
            continue
        try:
            if l and l.count() > 0:
                return l.first
        except Exception:
            continue
    return None


def _parse_price(text: str) -> Optional[float]:
    m = re.search(r"\$\s*([\d\.]+,\d{2})", text)
    if not m:
        return None
    return float(m.group(1).replace('.', '').replace(',', '.'))


def extract_product_page(page, url: str, selectors: Dict[str, Any], evidence_dir: str = '', html_dump_dir: str = '', save_basename: str = '') -> Dict[str, Any]:
    page.goto(url, wait_until='domcontentloaded')
    page.wait_for_timeout(1000)

    # Title (prefer og:title, then h1, then configured selectors)
    title = ''
    try:
        og = page.locator('meta[property="og:title"]').first
        if og.count() > 0:
            t = og.get_attribute('content')
            if t:
                title = t.strip()
    except Exception:
        pass
    if not title:
        try:
            h1 = page.locator('h1').first
            if h1 and h1.count() > 0:
                title = h1.inner_text().strip()
        except Exception:
            pass
    if not title:
        try:
            title_specs = selectors.get('title', [])
            tl = _page_first(page, title_specs)
            if tl:
                title = tl.inner_text().strip()
        except Exception:
            pass

    # Price: prefer "Ahora" and capture "Antes"
    price_final = None
    price_original = None
    try:
        full = page.content()
        m_now = re.search(r"Ahora[^$]*\$\s*([\d\.,]+)", full, re.I)
        m_before = re.search(r"Antes[^$]*\$\s*([\d\.,]+)", full, re.I)
        if m_now:
            price_final = _parse_price(f"$ {m_now.group(1)}")
        pl = _page_first(page, selectors.get('price_now', []))
        if pl and not price_final:
            price_final = _parse_price(pl.inner_text())
        if m_before:
            price_original = _parse_price(f"$ {m_before.group(1)}")
        if not price_original:
            pol = _page_first(page, selectors.get('price_original', []))
            if pol:
                price_original = _parse_price(pol.inner_text())
        if price_final and not price_original:
            price_original = price_final
    except Exception:
        pass

    # OOS via button
    in_stock = True
    try:
        btn = _page_first(page, selectors.get('add_to_cart_button', []))
        if btn:
            try:
                enabled = btn.is_enabled()
                visible = btn.is_visible()
                in_stock = bool(enabled and visible)
            except Exception:
                in_stock = True
    except Exception:
        pass
    try:
        if _page_first(page, selectors.get('oos_flag', [])):
            in_stock = False
    except Exception:
        pass

    promo_flag = False
    try:
        promo_flag = page.get_by_text(re.compile(r'Antes', re.I)).count() > 0 or (price_original and price_final and price_original > price_final)
    except Exception:
        pass

    # Evidence
    if evidence_dir and save_basename:
        try:
            page.screenshot(path=os.path.join(evidence_dir, f'{save_basename}.png'), full_page=True)
        except Exception:
            pass
    if html_dump_dir and save_basename:
        try:
            with open(os.path.join(html_dump_dir, f'{save_basename}.html'), 'w', encoding='utf-8') as f:
                f.write(page.content())
        except Exception:
            pass

    return {
        'title': title,
        'price_final': price_final,
        'price_original': price_original,
        'price_promo': price_final if promo_flag else None,
        'promo_flag': promo_flag,
        'in_stock': in_stock,
        'url': url,
    }
