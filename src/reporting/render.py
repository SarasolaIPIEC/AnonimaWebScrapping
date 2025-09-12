import csv


def render_report(out_path: str, period: str, series_path: str, breakdown_path: str, write_by_category: bool = False) -> None:
    """Render del reporte mensual (Jinja2 si está disponible, si no fallback)."""
    env = _build_jinja_env()
    if env is not None:
        series, breakdown, prev = load_data(series_path, breakdown_path, period)
        v = validate(breakdown)
        rows = v["rows"]
        enriched = enrich(rows, period, prev)
        series_svg = _svg_line(sorted(series, key=lambda r: r["period"]))
        ctx = build_context(period, series, enriched, series_svg)
        rel_breakdown = os.path.relpath(breakdown_path, start=os.path.dirname(out_path) or ".")
        ctx["links"]["breakdown"] = rel_breakdown.replace("\\","/")
        tpl = env.get_template("report.html")
        html = tpl.render(**ctx)
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        if write_by_category:
            _export_by_category(enriched, period)
        return
    # fallback heredado
    _legacy_report_impl(out_path, period, series_path, breakdown_path)

"""Reporting HTML (Jinja2) para IPC Ushuaia.

Este módulo consume `series_cba.csv` y `breakdown_<period>.csv` y produce
`reports/<period>.html` con dos vistas conmutables.

Modelo de datos esperado por `enrich()`/plantillas (por fila del breakdown):
- item_id, title, url, category, brand_tier ('premium'|'estandar'|'segunda'), cba_flag ('si'|'no'|'')
- presentation_text (p.ej. 'docena', 'lata 473 cc', '1,5 L', 'x 1 kg')
- base_equiv_value (float) y base_equiv_unit ('kg'|'l'|'un')
- price_final (ARS), price_list (opcional para tachado), promo_flag (bool), in_stock (bool)
- qty_AE (float mensual para AE), contrib_AE_$ (float), contrib_AE_pct (float 0..100)
- variation_mom_pct (float|None), variation_yoy_pct (float|None), variation_mom_unit_pct (float|None)
- basket_version, period, metadatos globales (source, branch, tz, family_ae)

Si faltan campos en exports, `enrich()` los deriva (presentación, unitario, flags).
Las validaciones en `validate()` no interrumpen: acumulan advertencias.
"""

import csv
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from playwright.sync_api import sync_playwright
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except Exception:  # optional dependency
    Environment = None
    FileSystemLoader = None
    select_autoescape = None

# === Helpers y pipeline Jinja2 (nuevo) ===

def _period_minus(period: str, months: int) -> str:
    y, m = period.split('-')
    y = int(y)
    m = int(m)
    total = y * 12 + (m - 1) - months
    ny = total // 12
    nm = (total % 12) + 1
    return f"{ny:04d}-{nm:02d}"


def _fmt_currency_ar(value):
    try:
        x = float(value)
    except Exception:
        x = 0.0
    s = f"{x:,.2f}"
    s = s.replace(',', '_').replace('.', ',').replace('_', '.')
    return f"${s}"


def _fmt_number_ar(value, ndigits: int = 3):
    try:
        x = float(value)
    except Exception:
        x = 0.0
    s = f"{x:.{ndigits}f}"
    s = s.replace('.', ',')
    while s.endswith('0') and ',' in s:
        s = s[:-1]
    if s.endswith(','):
        s = s[:-1]
    return s


def _fmt_pct_ar(value):
    try:
        if value in (None, '', 'N/D'):
            return 'N/D'
        x = float(value)
    except Exception:
        return 'N/D'
    s = f"{x:.1f}%"
    return s.replace('.', ',')


def _ensure_float(x):
    try:
        return float(x)
    except Exception:
        return None


def _read_csv(path: str):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def load_data(series_path: str, breakdown_path: str, period: str):
    series = _read_csv(series_path)
    breakdown = _read_csv(breakdown_path)
    prev_path = os.path.join(os.path.dirname(breakdown_path) or 'exports', f"breakdown_{_period_minus(period,1)}.csv")
    prev = _read_csv(prev_path)
    return series, breakdown, prev


def validate(rows):
    warnings = []
    valid_rows = []
    for r in rows:
        url = (r.get('url') or '').strip()
        pf = _ensure_float(r.get('price_final')) or 0.0
        if not url or ('laanonima' not in url.lower() and 'supermercado' not in url.lower()):
            warnings.append(f"URL sospechosa u omitida en item_id={r.get('item_id')}")
        if pf <= 0:
            warnings.append(f"Precio final inválido en item_id={r.get('item_id')}")
        valid_rows.append(r)
    return {'rows': valid_rows, 'warnings': warnings}


def enrich(rows, period: str, prev_rows):
    from ..normalize.units import parse_title_size
    prev_map = {r.get('item_id'): r for r in prev_rows if r.get('item_id')}
    total_cba = 0.0
    for r in rows:
        try:
            total_cba += float(r.get('cost_item_ae') or 0)
        except Exception:
            pass
    out = []
    for r in rows:
        title = r.get('title') or r.get('name') or ''
        qty = r.get('qty_base')
        unit = r.get('unit')
        if not qty or not unit:
            q, u = parse_title_size(title)
            qty = qty or q
            unit = unit or u
        presentation_text = f"{_fmt_number_ar(qty)} {('u' if unit in ('unit','un') else unit)}".strip()
        price_final = _ensure_float(r.get('price_final')) or 0.0
        price_original = _ensure_float(r.get('price_original')) or 0.0
        price_list = price_original if (price_original > price_final > 0) else None
        unit_price = (price_final / qty) if (price_final and qty) else None
        contrib_ae = _ensure_float(r.get('cost_item_ae')) or (unit_price * (_ensure_float(r.get('monthly_qty_base')) or 0.0) if unit_price else 0.0)
        contrib_pct = (contrib_ae / total_cba * 100.0) if total_cba else 0.0
        prev = prev_map.get(r.get('item_id'))
        var_mom = None
        var_mom_unit = None
        if prev:
            pf_prev = _ensure_float(prev.get('price_final'))
            up_prev = _ensure_float(prev.get('unit_price_base'))
            if pf_prev and price_final:
                var_mom = (price_final / pf_prev - 1.0) * 100.0
            if up_prev and unit_price:
                var_mom_unit = (unit_price / up_prev - 1.0) * 100.0
        brand_tier = (r.get('brand_tier') or '').strip().lower()
        if brand_tier not in ('premium','estandar','segunda'):
            brand_tier = 'estandar'
        cba_flag = (r.get('cba_flag') or '').strip().lower()
        in_stock = str(r.get('in_stock') or '1').strip().lower() in ('1','true','yes','si','s')
        promo_flag = str(r.get('promo_flag') or '').strip().lower() in ('1','true','yes','si','s')
        qty_ae = _ensure_float(r.get('monthly_qty_base')) or 0.0
        out.append({
            'period': period,
            'item_id': r.get('item_id'),
            'title': title,
            'url': r.get('url') or '',
            'category': (r.get('category') or '').lower(),
            'brand_tier': brand_tier,
            'cba_flag': 'si' if cba_flag in ('si','sí','s','1',True) else ('no' if cba_flag else ''),
            'presentation_text': presentation_text,
            'base_equiv_value': qty or 0.0,
            'base_equiv_unit': ('un' if unit in ('unit','un') else unit) or '',
            'price_final': price_final,
            'price_list': price_list,
            'promo_flag': promo_flag,
            'in_stock': in_stock,
            'qty_AE': qty_ae,
            'contrib_AE_$': contrib_ae,
            'contrib_AE_pct': contrib_pct,
            'unit_price': unit_price or 0.0,
            'variation_mom_pct': var_mom,
            'variation_yoy_pct': None,
            'variation_mom_unit_pct': var_mom_unit,
            'basket_version': r.get('basket_version') or 'v1',
        })
    return out


def compute_kpis(series_rows, enriched_rows):
    series_sorted = sorted(series_rows, key=lambda r: r['period'])
    latest = series_sorted[-1] if series_sorted else {}
    try:
        cba_ae = float(latest.get('cba_ae') or 0)
    except Exception:
        cba_ae = 0.0
    try:
        cba_family = float(latest.get('cba_family') or (cba_ae * 3.09))
    except Exception:
        cba_family = 0.0
    idx = _ensure_float(latest.get('idx')) or 0.0
    mom = _ensure_float(latest.get('mom'))
    yoy = _ensure_float(latest.get('yoy'))
    total_cba = sum((r.get('contrib_AE_$') or 0.0) for r in enriched_rows)
    summary = {
        'total_items': len(enriched_rows),
        'valid_items': sum(1 for r in enriched_rows if (r.get('price_final') or 0) > 0),
        'promo_count': sum(1 for r in enriched_rows if r.get('price_list') and r.get('price_final') and r['price_list'] > r['price_final']),
        'oos_count': sum(1 for r in enriched_rows if not r.get('in_stock')),
        'cba_ae_sum': total_cba,
        'valid_ratio': (sum(1 for r in enriched_rows if (r.get('price_final') or 0) > 0) / max(1, len(enriched_rows))) if enriched_rows else 0.0,
    }
    return {
        'series_sorted': series_sorted,
        'kpis': {
            'cba_ae': cba_ae,
            'cba_family': cba_family,
            'idx': idx,
            'mom': mom,
            'yoy': yoy,
        },
        'summary': summary,
    }


def build_context(period: str, series_rows, enriched_rows, series_svg: str):
    k = compute_kpis(series_rows, enriched_rows)
    categories = sorted({r["category"] for r in enriched_rows if r.get("category")})
    brand_tiers = ["premium","estandar","segunda"]
    viewA = sorted([
        {
            "item_id": r["item_id"], "title": r["title"], "url": r["url"], "category": r["category"],
            "brand_tier": r["brand_tier"], "cba_flag": r["cba_flag"],
            "presentation_text": r["presentation_text"], "price_final": r["price_final"], "price_list": r["price_list"],
            "contrib_AE_$": r["contrib_AE_$"], "contrib_AE_pct": r["contrib_AE_pct"],
            "variation_mom_pct": r["variation_mom_pct"], "in_stock": r["in_stock"], "promo_flag": r["promo_flag"]
        } for r in enriched_rows
    ], key=lambda x: x["contrib_AE_pct"], reverse=True)
    viewB = sorted([
        {
            "item_id": r["item_id"], "title": r["title"], "url": r["url"], "category": r["category"],
            "brand_tier": r["brand_tier"], "cba_flag": r["cba_flag"],
            "base_equiv_value": r["base_equiv_value"], "base_equiv_unit": r["base_equiv_unit"],
            "unit_price": r["unit_price"], "contrib_AE_pct": r["contrib_AE_pct"],
            "variation_mom_unit_pct": r["variation_mom_unit_pct"]
        } for r in enriched_rows
    ], key=lambda x: (x["unit_price"] if x["unit_price"] else float("inf")))
    return {
        "title": f"IPC Ushuaia — Reporte {period}",
        "header": "IPC Ushuaia — Canasta Básica Alimentaria",
        "period": period,
        "kpis": k["kpis"],
        "summary": k["summary"],
        "chart_index": series_svg,
        "viewA": viewA,
        "viewB": viewB,
        "filters": {"categories": categories, "brand_tiers": brand_tiers},
        "links": {},
        "meta": {"source": "La Anónima – Online", "branch": "Ushuaia 5", "tz": "America/Argentina/Ushuaia", "family_ae": 3.09, "generated_at": datetime.now().isoformat(timespec="seconds")}
    }


def _build_jinja_env():
    if Environment is None:
        return None
    loader = FileSystemLoader(os.path.join('src', 'reporting', 'templates'))
    env = Environment(loader=loader, autoescape=select_autoescape(['html']))
    env.filters['currency'] = _fmt_currency_ar
    env.filters['number'] = _fmt_number_ar
    env.filters['pct'] = _fmt_pct_ar
    return env


def _export_by_category(rows: List[Dict[str, Any]], period: str) -> None:
    bydir = os.path.join('by_category')
    os.makedirs(bydir, exist_ok=True)
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        cat = r.get('category') or 'sin_categoria'
        buckets.setdefault(cat, []).append(r)
    fields = ['period','item_id','title','url','brand_tier','cba_flag','category']
    for cat, items in buckets.items():
        path = os.path.join(bydir, f"{cat}.csv")
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for r in items:
                w.writerow({
                    'period': period,
                    'item_id': r.get('item_id'),
                    'title': r.get('title'),
                    'url': r.get('url'),
                    'brand_tier': r.get('brand_tier'),
                    'cba_flag': r.get('cba_flag'),
                    'category': r.get('category'),
                })


def _read_series(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def _read_breakdown(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def _svg_line(series: List[Dict[str, Any]], width=960, height=240, margin=40) -> str:
    if not series:
        return ''
    xs = list(range(len(series)))
    ys = [float(r['idx']) for r in series]
    miny, maxy = min(ys), max(ys)
    if maxy == miny:
        maxy += 1

    def sx(i):
        return margin + i * (width - 2 * margin) / max(1, len(xs) - 1)

    def sy(y):
        return height - margin - (y - miny) * (height - 2 * margin) / (maxy - miny)

    pts = ' '.join(f"{sx(i):.1f},{sy(y):.1f}" for i, y in zip(xs, ys))
    dots = '\n'.join(f"<circle cx='{sx(i):.1f}' cy='{sy(y):.1f}' r='3' fill='#1976d2' />" for i, y in enumerate(ys))
    labels = '\n'.join(
        f"<text x='{sx(i):.1f}' y='{sy(y)-8:.1f}' font-size='10' text-anchor='middle' fill='#333'>{series[i]['period']}</text>"
        for i, y in enumerate(ys)
    )
    return f"""
<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="0" width="{width}" height="{height}" fill="#fff" />
  <polyline fill="none" stroke="#1976d2" stroke-width="2" points="{pts}" />
  {dots}
  <line x1="{margin}" y1="{height-margin}" x2="{width-margin}" y2="{height-margin}" stroke="#bbb" stroke-width="1" />
  <line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height-margin}" stroke="#bbb" stroke-width="1" />
  {labels}
</svg>
"""


def _summarize_breakdown(breakdown: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_items = len(breakdown)
    valid = 0
    promo = 0
    oos = 0
    cba_ae = 0.0
    for r in breakdown:
        price = r.get('price_final') or r.get('price') or r.get('price_now')
        try:
            pval = float(price) if price not in (None, '', '0') else 0.0
        except Exception:
            pval = 0.0
        if pval > 0:
            valid += 1
        try:
            if str(r.get('promo_flag', '')).lower() in ('1', 'true', 'yes', 'si', 'sÃ­'):
                promo += 1
        except Exception:
            pass
        try:
            if str(r.get('in_stock', '')).lower() in ('0', 'false', 'no'):
                oos += 1
        except Exception:
            pass
        try:
            cba_ae += float(r.get('cost_item_ae') or 0)
        except Exception:
            pass
    ratio = (valid / total_items) if total_items else 0
    return {
        'total_items': total_items,
        'valid_items': valid,
        'valid_ratio': ratio,
        'promo_count': promo,
        'oos_count': oos,
        'cba_ae_sum': cba_ae,
    }


def _legacy_report_impl(out_path: str, period: str, series_path: str, breakdown_path: str) -> None:
    series = _read_series(series_path)
    breakdown = _read_breakdown(breakdown_path)
    series_sorted = sorted(series, key=lambda r: r['period'])
    latest = series_sorted[-1] if series_sorted else {}
    svg = _svg_line(series_sorted)
    chart_html = svg if (len(series_sorted) > 1) else ("<div class='muted'>Sin suficiente historial; el gr&aacute;fico aparece desde el 2.&ordm; mes.</div>")

    # Aggregates
    s = _summarize_breakdown(breakdown)
    # Recompute promo_count robustly (flag or list price > final)
    try:
        _promo_count = 0
        for _r in breakdown:
            try:
                _pfv = float(_r.get('price_final') or 0)
                _pov = float(_r.get('price_original') or 0)
            except Exception:
                _pfv = _pov = 0.0
            try:
                _flag = str(_r.get('promo_flag','')).strip().lower() in ('1','true','yes','y','si','s')
            except Exception:
                _flag = False
            if _flag or (_pov > _pfv and _pfv > 0):
                _promo_count += 1
        s['promo_count'] = _promo_count
    except Exception:
        pass
    top_cost = sorted(breakdown, key=lambda r: float(r.get('cost_item_ae') or 0), reverse=True)[:8]

    # Enrich dataset for template
    def _fmt_qty_unit(q, u):
        try:
            qf = float(q or 0)
        except Exception:
            qf = 0
        uu = (u or '').lower()
        if uu in ('unit','un'): uu='u'
        if abs(qf-round(qf))<1e-6:
            qstr = str(int(round(qf)))
        else:
            qstr = (f"{qf:.3f}").rstrip('0').rstrip('.')
        if qf==12 and (uu in ('u','')):
            return '12 u'
        return (qstr + (' ' + uu if uu else '')).strip()

    def _presentation_text(r):
        import re as _re
        title = r.get('title') or ''
        m = _re.search(r"(\d+[\.,]?\d*)\s*(cc|ml|l|lt|g|kg|docena|u|unid)", title, _re.I)
        if m:
            q = m.group(1); u = m.group(2).lower();
            if u=='lt': u='l'
            if u=='unid': u='u'
            return f"{q} {u}"
        return _fmt_qty_unit(r.get('qty_base'), r.get('unit'))

    def _unit_price(r):
        up = r.get('unit_price_base')
        try:
            return float(up) if up not in (None,'') else None
        except Exception:
            return None

    def _price_list(r):
        try:
            pl = float(r.get('price_original') or 0)
            pf = float(r.get('price_final') or 0)
            return pl if pl>pf else None
        except Exception:
            return None

    total_cba = float(s.get('cba_ae_sum') or 0)
    def _contrib_pct(r):
        try:
            v = float(r.get('cost_item_ae') or 0)
        except Exception:
            v = 0.0
        return (v/total_cba*100.0) if total_cba else 0.0

    def _normalize_tier(t):
        tl = (t or '').strip().lower()
        return tl if tl in ('premium','estandar','segunda') else 'estandar'

    def _row_enriched(r):
        return {
            'item_id': r.get('item_id'),
            'title': (r.get('title') or r.get('name') or ''),
            'name': r.get('name') or '',
            'url': r.get('url') or '',
            'category': (r.get('category') or '').lower(),
            'brand_tier': _normalize_tier(r.get('brand_tier')),
            'cba_flag': (r.get('cba_flag') or '').strip().lower(),
            'presentation_text': _presentation_text(r),
            'price_final': float(r.get('price_final') or 0),
            'price_list': _price_list(r),
            'unit_price': _unit_price(r) or 0,
            'contrib_$': float(r.get('cost_item_ae') or 0),
            'contrib_pct': _contrib_pct(r),
        }

    rows_en = [_row_enriched(r) for r in breakdown]
    top_en = [_row_enriched(r) for r in top_cost]

    def fmt_money(x):
        try:
            return f"${float(x):,.2f}"
        except Exception:
            return "$0.00"

    def derive_brand(title: str) -> str:
        if not title:
            return ''
        t = title.strip()
        for sep in [' - ', ' | ']:
            if sep in t:
                t = t.split(sep)[0]
                break
        # grab initial letters-only segment as "brand"
        import re as _re
        m = _re.match(r"([A-Za-zÃÃ‰ÃÃ“ÃšÃœÃ‘&' ]+)", t)
        if m:
            cand = m.group(1).strip()
            return cand[:40]
        return ''

    def price_cell(r: Dict[str, Any]) -> str:
        try:
            pf = float(r.get('price_final') or 0)
        except Exception:
            pf = 0.0
        try:
            po = float(r.get('price_original') or pf)
        except Exception:
            po = pf
        if po > pf and pf > 0:
            return f"<span class='orig'>{fmt_money(po)}</span> <span class='promo'>{fmt_money(pf)}</span>"
        return fmt_money(pf)

    def row_html_compact(r: Dict[str, Any]) -> str:
        """Fila compacta con 6 columnas visibles y data-attrs para filtros.
        Columnas: Ítem, Precio final, Tamaño presentación, Equivalencia base, Precio unitario, Part. AE (%)
        """
        url = r.get('url') or ''
        title = r.get('title') or ''
        if title.lower().strip() in ('almacï¿½ï¿½n', 'almacen', 'producto') or len(title.strip()) < 4:
            title = r.get('name') or title
        name = r.get('name') or ''
        brand_tier = (r.get('brand_tier') or '').strip().lower()
        cba_flag = str(r.get('cba_flag') or '').lower()
        qty = r.get('qty_base') or ''
        unit = r.get('unit') or ''
        unit_price = r.get('unit_price_base')
        unit_price_val = ''
        try:
            if unit_price not in (None, ''):
                unit_price_val = f"${float(unit_price):,.2f}"
        except Exception:
            unit_price_val = ''
        cost_val = r.get('cost_item_ae') or 0
        # Tamaño de presentación (extraído del título cuando es posible)
        import re as _re
        size_display = ''
        msize = _re.search(r"(lata|doy\s*pack|doypack|sachet|pack|botella)\b.*?(\d+[\.,]?\d*)\s*(cc|ml|l|lt|g|kg|docena|u|unid)", title, _re.I)
        if msize:
            size_display = (msize.group(1) + ' ' + msize.group(2) + ' ' + msize.group(3)).strip()
        else:
            m2 = _re.search(r"(\d+[\.,]?\d*)\s*(cc|ml|l|lt|g|kg|docena|u|unid)", title, _re.I)
            if m2:
                size_display = (m2.group(1) + ' ' + m2.group(2)).strip()
            else:
                size_display = (f"{qty} {unit}").strip()
        # Equivalencia base formateada (kg/l/un)
        eq_unit = (unit or '').lower()
        eq_qty = qty or 0
        try:
            eq_qty = float(eq_qty)
        except Exception:
            eq_qty = 0
        eq_str = (f"{eq_qty:.3f}".rstrip('0').rstrip('.') + ' ' + (eq_unit or '')).strip()
        link = f"<a href='{url}' target='_blank' rel='noopener'>{title or '(ver producto)'}</a>" if url else (title or name)
        # Chips
        chips = []
        if cba_flag in ('si', 'sï¿½ï¿½', 'sÃ­'):
            chips.append("<span class='chip chip-cba'>CBA</span>")
        if brand_tier in ('premium', 'estandar', 'segunda'):
            label = {'premium': 'Premium', 'estandar': 'EstÃ¡ndar', 'segunda': 'Segunda'}.get(brand_tier, brand_tier.title())
            chips.append(f"<span class='chip chip-tier'>{label}</span>")
        chips_html = (" ".join(chips)) if chips else ''
        item_cell = f"<span class='item-main'>{name}</span> &mdash; {link}"
        if chips_html:
            item_cell += f"<div class='item-meta'>{chips_html}</div>"

        # sanitize attributes outside f-string expressions to avoid backslashes in {..}
        _title_attr = (title or '').replace('"','').strip()
        _name_attr = (name or '').replace('"','').strip()
        _cat_attr = (r.get('category') or '').lower()
        _pf_attr = r.get('price_final') or ''
        _upb_attr = unit_price or ''
        data_attrs = (
            f" data-item-id=\"{r.get('item_id') or ''}\""
            f" data-title=\"{_title_attr}\""
            f" data-name=\"{_name_attr}\""
            f" data-url=\"{url}\""
            f" data-brand-tier=\"{brand_tier}\""
            f" data-cba-flag=\"{cba_flag}\""
            f" data-category=\"{_cat_attr}\""
            f" data-price-final=\"{_pf_attr}\""
            f" data-unit-price-base=\"{_upb_attr}\""
            f" data-cost-ae=\"{cost_val}\""
        )

        # Participación en CBA AE (%)
        try:
            total_cba = float(s.get('cba_ae_sum') or 0)
        except Exception:
            total_cba = 0
        part_pct = (float(cost_val or 0) / total_cba * 100.0) if total_cba else 0.0

        return (
            f"<tr class='data-row' {data_attrs}>"
            f"<td>{item_cell}</td>"
            f"<td class='num'>{price_cell(r)}</td>"
            f"<td>{size_display}</td>"
            f"<td class='num'>{unit_price_val}</td>"
            f"<td class='num'>{part_pct:.1f}%</td>"
            f"</tr>"
        )

    def row_html_enhanced(r: Dict[str, Any]) -> str:
        """Fila HTML con atributos data-* para filtros/ordenamiento.
        No rompe el look&feel existente; es compatible con el render estÃ¡tico.
        """
        url = r.get('url') or ''
        title = r.get('title') or ''
        if title.lower().strip() in ('almacÇ¸n', 'almacen', 'producto') or len(title.strip()) < 4:
            title = r.get('name') or title
        brand = derive_brand(title)
        name = (brand + ' ' if brand else '') + (r.get('name') or '')
        qty = r.get('qty_base') or ''
        unit = r.get('unit') or ''
        cost_val = r.get('cost_item_ae') or 0
        cost = fmt_money(cost_val)
        promo = 'Sï¿½ï¿½' if str(r.get('promo_flag', '')).lower() in ('1', 'true', 'yes', 'si', 'sï¿½ï¿½') else 'No'
        stock = 'Sï¿½ï¿½' if str(r.get('in_stock', '1')).lower() in ('1', 'true', 'yes', 'si', 'sï¿½ï¿½') else 'No'
        link = f"<a href='{url}' target='_blank' rel='noopener'>{title or '(ver producto)'}</a>" if url else title

        item_id = r.get('item_id') or ''
        brand_tier = r.get('brand_tier') or ''
        cba_flag = r.get('cba_flag') or ''
        category = r.get('category') or ''
        price_final = r.get('price_final') or ''
        unit_price_base = r.get('unit_price_base') or ''
        _title_attr = (title or '').replace('"','').strip()
        _name_attr = (name or '').replace('"','').strip()
        data_attrs = (
            f" data-item-id=\"{item_id}\""
            f" data-title=\"{_title_attr}\""
            f" data-name=\"{_name_attr}\""
            f" data-url=\"{url}\""
            f" data-brand-tier=\"{brand_tier}\""
            f" data-cba-flag=\"{cba_flag}\""
            f" data-category=\"{category}\""
            f" data-price-final=\"{price_final}\""
            f" data-unit-price-base=\"{unit_price_base}\""
            f" data-cost-ae=\"{cost_val}\""
        )

        # Columnas simplificadas: Ãtem (Ãºnico, con link), Precio, TamaÃ±o, Precio unitario, Costo AE
        unit_price_display = ''
        try:
            upb = float(unit_price_base) if unit_price_base not in (None, '') else None
            if upb is not None:
                unit_price_display = f"${upb:,.2f}"
        except Exception:
            unit_price_display = ''
        size_display = f"{qty} {unit}".strip()
        return (
            f"<tr class='data-row' {data_attrs}>"
            f"<td>{name} â€” {link}</td>"
            f"<td class='num'>{price_cell(r)}</td>"
            f"<td class='num'>{size_display}</td>"
            f"<td class='num'>{unit_price_display}</td>"
            f"<td class='num'>{cost}</td>"
            f"</tr>"
        )

    def row_html(r: Dict[str, Any]) -> str:
        url = r.get('url') or ''
        title = r.get('title') or ''
        if title.lower().strip() in ('almacÃ©n', 'almacen', 'producto') or len(title.strip()) < 4:
            title = r.get('name') or title
        brand = derive_brand(title)
        name = (brand + ' ' if brand else '') + (r.get('name') or '')
        qty = r.get('qty_base') or ''
        unit = r.get('unit') or ''
        cost = fmt_money(r.get('cost_item_ae') or 0)
        promo = 'SÃ­' if str(r.get('promo_flag', '')).lower() in ('1', 'true', 'yes', 'si', 'sÃ­') else 'No'
        stock = 'SÃ­' if str(r.get('in_stock', '1')).lower() in ('1', 'true', 'yes', 'si', 'sÃ­') else 'No'
        link = f"<a href='{url}' target='_blank' rel='noopener'>{title or '(ver producto)'}</a>" if url else title
        return f"<tr><td>{name}</td><td>{link}</td><td class='num'>{price_cell(r)}</td><td class='num'>{qty}</td><td>{unit}</td><td class='num'>{cost}</td><td>{promo}</td><td>{stock}</td></tr>"

    def row_html_v2(r: Dict[str, Any]) -> str:
        url = r.get('url') or ''
        title = r.get('title') or ''
        name = r.get('name') or ''
        if title.lower().strip() in ('almacén','almacen','producto') or len(title.strip()) < 4:
            title = name or title
        qty = r.get('qty_base') or ''
        unit = r.get('unit') or ''
        unit_price = r.get('unit_price_base')
        unit_price_val = ''
        try:
            if unit_price not in (None, ''):
                unit_price_val = f"${float(unit_price):,.2f}"
        except Exception:
            unit_price_val = ''
        cost_val = r.get('cost_item_ae') or 0
        # tamaño legible (preferir magnitud + unidad estándar)
        import re as _re
        size_display = ''
        m = _re.search(r"(\d+[\.,]?\d*)\s*(cc|ml|l|lt|g|kg|docena|u|unid)", title, _re.I)
        if m:
            q = m.group(1)
            u = m.group(2).lower()
            if u == 'lt': u = 'l'
            if u == 'unid': u = 'u'
            size_display = f"{q} {u}".strip()
        else:
            # Fallback a qty/unit normalizados
            try:
                qf = float(qty or 0)
            except Exception:
                qf = 0
            u = (unit or '').lower()
            if u == 'un' or u == 'unit':
                u = 'u'
            if abs(qf - round(qf)) < 1e-6:
                qstr = str(int(round(qf)))
            else:
                qstr = (f"{qf:.3f}").rstrip('0').rstrip('.')
            # caso docena
            if qf == 12 and u in ('u',''):
                size_display = '12 u'
            else:
                size_display = (qstr + (' ' + u if u else '')).strip()
        # chips
        chips = []
        cba_flag = str(r.get('cba_flag') or '').strip().lower()
        if cba_flag in ('si','sí','s'):
            chips.append("<span class='chip chip-cba'>CBA</span>")
        brand_tier = (r.get('brand_tier') or '').strip().lower()
        if brand_tier in ('premium','estandar','segunda'):
            bt = {'premium':'Premium','estandar':'Estandar','segunda':'Segunda'}.get(brand_tier,brand_tier.title())
            chips.append(f"<span class='chip chip-tier'>{bt}</span>")
        chips_html = (" ".join(chips)) if chips else ''
        # evitar duplicidad nombre/título
        text_eq = (name.strip().lower() == title.strip().lower())
        meta_text = '' if text_eq else name
        link = f"<a href='{url}' target='_blank' rel='noopener'>{title or '(ver producto)'}</a>" if url else (title or name)
        meta_html = f"<div class='item-meta'>{meta_text} {chips_html}</div>" if (meta_text or chips_html) else ''
        # participación AE
        try:
            total_cba = float(s.get('cba_ae_sum') or 0)
        except Exception:
            total_cba = 0
        part_pct = (float(cost_val or 0) / total_cba * 100.0) if total_cba else 0.0
        item_id = r.get('item_id') or ''
        title_attr = (title or '').replace('"','').strip()
        name_attr = (name or '').replace('"','').strip()
        category_attr = (r.get('category') or '').lower()
        price_final_attr = r.get('price_final') or ''
        upb_attr = unit_price or ''
        data_attrs = (
            f" data-item-id=\"{item_id}\""
            f" data-title=\"{title_attr}\""
            f" data-name=\"{name_attr}\""
            f" data-url=\"{url}\""
            f" data-brand-tier=\"{brand_tier}\""
            f" data-cba-flag=\"{cba_flag}\""
            f" data-category=\"{category_attr}\""
            f" data-price-final=\"{price_final_attr}\""
            f" data-unit-price-base=\"{upb_attr}\""
            f" data-cost-ae=\"{cost_val}\""
        )
        return (
            f"<tr class='data-row' {data_attrs}>"
            f"<td><span class='item-main'>{link}</span>{meta_html}</td>"
            f"<td class='num'>{price_cell(r)}</td>"
            f"<td>{size_display}</td>"
            f"<td class='num'>{unit_price_val}</td>"
            f"<td class='num'>{part_pct:.1f}%</td>"
            f"</tr>"
        )

    breakdown_rows = '\n'.join(row_html_v2(r) for r in breakdown)

    # JS ligero para filtros/ordenamiento (sin dependencias). Se inyecta al final del HTML.
    script_js = r"""
  <script>
  // Filtros y ordenamiento (vanilla JS, sin dependencias)
  (function(){
    var $ = function(sel, root){ return (root||document).querySelector(sel); };
    var $$ = function(sel, root){ return Array.prototype.slice.call((root||document).querySelectorAll(sel)); };
    var table = document.getElementById('breakdown-table');
    if (!table) return;
    var tbody = table.querySelector('tbody');
    var searchInput = $('#search');
    var categorySel = $('#category');
    var brandBox = $('#brand-tier-options');
    var cbaBox = $('#cba-flag-options');
    var minPrice = $('#min-price');
    var maxPrice = $('#max-price');
    var sortBy = $('#sort-by');
    var sortDirBtn = $('#sort-dir');
    var statusEl = $('#filter-status');
    var resetBtn = $('#reset-filters');

    function inferCategoryFromUrl(url){
      try {
        var u = new URL(url);
        var segs = u.pathname.split('/').filter(function(s){return s;});
        if (segs.length) return segs[0].replace(/[-_]/g,' ').toLowerCase();
      } catch(e){}
      return '';
    }

    var rows = $$('.data-row', tbody).map(function(tr){
      var d = tr.dataset;
      var title = (d.title || '').toLowerCase();
      var name = (d.name || '').toLowerCase();
      var itemId = (d.itemId || '').toLowerCase();
      var url = d.url || '';
      var category = (d.category || inferCategoryFromUrl(url) || '').toLowerCase();
      var brandTier = (d.brandTier || '').toLowerCase();
      var cbaFlag = (d.cbaFlag || '').toLowerCase();
      var pf = parseFloat(d.priceFinal);
      var upb = parseFloat(d.unitPriceBase);
      var cae = parseFloat(d.costAe);
      return {
        tr: tr,
        data: {
          title: title,
          name: name,
          itemId: itemId,
          url: url,
          category: category,
          brandTier: brandTier,
          cbaFlag: cbaFlag,
          priceFinal: isFinite(pf) ? pf : NaN,
          unitPriceBase: isFinite(upb) ? upb : NaN,
          costAe: isFinite(cae) ? cae : NaN,
          haystack: (title + ' ' + name + ' ' + itemId).trim()
        }
      };
    });

    function distinct(arr){
      var out = [];
      arr.forEach(function(v){ if(v && out.indexOf(v)===-1) out.push(v); });
      return out;
    }
    function byFreq(vals){
      var m = Object.create(null);
      vals.forEach(function(v){ if(!v) return; m[v] = (m[v]||0)+1; });
      return Object.keys(m).sort(function(a,b){ return m[b]-m[a]; });
    }

    // Poblar facets
    byFreq(rows.map(function(r){return r.data.category;})).forEach(function(cat){
      var opt = document.createElement('option');
      opt.value = cat; opt.textContent = cat || 'â€”';
      categorySel.appendChild(opt);
    });

    var brandTiers = distinct(rows.map(function(r){return r.data.brandTier;})).sort();
    brandTiers.forEach(function(bt){
      var id = 'bt-' + (bt||'na');
      var label = document.createElement('label');
      var cb = document.createElement('input'); cb.type = 'checkbox'; cb.value = bt; cb.id = id;
      var span = document.createElement('span'); span.textContent = bt || 'N/D';
      label.htmlFor = id; label.appendChild(cb); label.appendChild(span);
      brandBox.appendChild(label);
    });
    if (!brandTiers.length) brandBox.parentElement.style.display = 'none';

    var cbaVals = distinct(rows.map(function(r){return r.data.cbaFlag;})).filter(function(v){return v==='si'||v==='no';});
    cbaVals.forEach(function(v){
      var id = 'cba-' + v;
      var label = document.createElement('label');
      var cb = document.createElement('input'); cb.type = 'checkbox'; cb.value = v; cb.id = id;
      var span = document.createElement('span'); span.textContent = v.toUpperCase();
      label.htmlFor = id; label.appendChild(cb); label.appendChild(span);
      cbaBox.appendChild(label);
    });
    if (!cbaVals.length) cbaBox.parentElement.style.display = 'none';

    // Rango sugerido
    var prices = rows.map(function(r){return r.data.priceFinal;}).filter(function(v){return isFinite(v);});
    if (prices.length){
      var minP = Math.min.apply(null, prices);
      var maxP = Math.max.apply(null, prices);
      minPrice.placeholder = minP.toFixed(2);
      maxPrice.placeholder = maxP.toFixed(2);
    }

    function getSelected(root){ return $$("input[type='checkbox']:checked", root).map(function(i){return i.value;}); }
    function getSortDir(){ return sortDirBtn.dataset.dir || 'asc'; }
    function toggleSortDir(){ sortDirBtn.dataset.dir = getSortDir()==='asc' ? 'desc' : 'asc'; sortDirBtn.textContent = getSortDir()==='asc' ? 'Asc' : 'Desc'; }

    function applyFilters(){
      var q = (searchInput.value || '').trim().toLowerCase();
      var cat = (categorySel.value || '').toLowerCase();
      var selBT = new Set(getSelected(brandBox));
      var selCBA = new Set(getSelected(cbaBox));
      var minV = minPrice.value !== '' ? parseFloat(minPrice.value) : null;
      var maxV = maxPrice.value !== '' ? parseFloat(maxPrice.value) : null;

      var visible = 0;
      var onlyCBA = false;
      var sc = document.getElementById('solo-cba');
      if (sc) { onlyCBA = !!sc.checked; }
      rows.forEach(function(row){
        var d = row.data; var ok = true;
        if (q) ok = ok && d.haystack.indexOf(q) !== -1;
        if (ok && cat) ok = ok && d.category === cat;
        if (ok && selBT.size) ok = ok && selBT.has(d.brandTier);
        if (ok && selCBA.size) ok = ok && selCBA.has(d.cbaFlag);
        if (ok && onlyCBA) ok = ok && d.cbaFlag === 'si';
        if (ok && (minV !== null)) ok = ok && isFinite(d.priceFinal) && d.priceFinal >= minV;
        if (ok && (maxV !== null)) ok = ok && isFinite(d.priceFinal) && d.priceFinal <= maxV;
        row.tr.style.display = ok ? '' : 'none';
        if (ok) visible += 1;
      });

      var key = sortBy.value;
      if (key){
        var dir = getSortDir();
        var prop = key==='price_final' ? 'priceFinal' : (key==='unit_price_base' ? 'unitPriceBase' : (key==='cost_item_ae' ? 'costAe' : null));
        if (prop){
          var vis = rows.filter(function(r){return r.tr.style.display !== 'none';});
          vis.sort(function(a,b){
            var av = a.data[prop], bv = b.data[prop];
            var aN = isFinite(av), bN = isFinite(bv);
            if (aN && !bN) return -1;
            if (!aN && bN) return 1;
            if (!aN && !bN) return 0;
            var cmp = av - bv; return dir==='asc' ? cmp : -cmp;
          });
          var frag = document.createDocumentFragment();
          vis.forEach(function(r){ frag.appendChild(r.tr); });
          tbody.appendChild(frag);
        }
      }

      statusEl.textContent = 'Mostrando ' + visible + ' de ' + rows.length + ' Ã­tems';
    }

    [searchInput, categorySel, minPrice, maxPrice, sortBy].forEach(function(el){ if(el) el.addEventListener('input', applyFilters); });
    [brandBox, cbaBox].forEach(function(root){ if(root) root.addEventListener('change', applyFilters); });
    sortDirBtn.addEventListener('click', function(){ toggleSortDir(); applyFilters(); });
    resetBtn.addEventListener('click', function(){
      searchInput.value = '';
      categorySel.value = '';
      minPrice.value = '';
      maxPrice.value = '';
      sortBy.value = '';
      sortDirBtn.dataset.dir = 'asc'; sortDirBtn.textContent = 'Asc';
      $$("input[type='checkbox']", brandBox).forEach(function(cb){ cb.checked = false; });
      $$( "input[type='checkbox']", cbaBox).forEach(function(cb){ cb.checked = false; });
      applyFilters();
    });

    applyFilters();

    // Insertar control "Solo CBA" junto al buscador y ajustar etiqueta
    var soloCBA = document.getElementById('solo-cba');
    (function(){
      var form = document.getElementById('filter-form');
      var grid = form ? form.querySelector('.controls-grid') : null;
      if (grid && !soloCBA){
        var wrap = document.createElement('div'); wrap.className = 'control';
        wrap.innerHTML = "<label for='solo-cba'>&nbsp;</label><div class='row'><label style='align-items:center; gap:8px; display:inline-flex;'><input type='checkbox' id='solo-cba'/> Solo CBA</label></div>";
        grid.insertBefore(wrap, grid.children[1] || null);
        soloCBA = wrap.querySelector('#solo-cba');
        soloCBA.addEventListener('input', applyFilters);
      }
      var lbl = form ? form.querySelector("label[for='search']") : null;
      if (lbl) lbl.textContent = 'Buscar';
    })();

    // Reescribir headers a columnas simplificadas
    function rewriteHeader(t){
      var thead = t && t.querySelector('thead'); if(!thead) return;
      thead.innerHTML = "<tr><th>&Iacute;tem</th><th>Precio final</th><th>Tama&ntilde;o</th><th>Precio unitario</th><th>Part. AE</th></tr>";
    }
    rewriteHeader(table);
    var allTables = document.querySelectorAll('section table');
    if (allTables.length){ for (var i=0;i<allTables.length;i++){ if (allTables[i] !== table){ rewriteHeader(allTables[i]); break; } } }
  })();
  // Ajuste de encabezados con tooltips y accesibilidad (fallback si hubo mojibake)
  (function(){
    function setHeader(t){
      if(!t) return; var thead=t.querySelector('thead'); if(!thead) return;
      var tr=document.createElement('tr');
      var cols=[
        {t:'Ítem', tip:'Título y enlace'},
        {t:'Precio final', tip:'Precio final al consumidor'},
        {t:'Tamaño', tip:'Tamaño de la presentación (g/ml/L/kg/cc/un)'},
        {t:'Precio unitario', tip:'Precio por kg/L/unidad'},
        {t:'Part. AE', tip:'Participación en CBA AE (%)'}
      ];
      cols.forEach(function(c){ var th=document.createElement('th'); th.setAttribute('scope','col'); th.title=c.tip; th.textContent=c.t; tr.appendChild(th); });
      thead.innerHTML=''; thead.appendChild(tr);
    }
    setHeader(document.getElementById('breakdown-table'));
    var all=document.querySelectorAll('section table'); if(all.length){ for(var i=0;i<all.length;i++){ if(all[i].id!=='breakdown-table'){ setHeader(all[i]); break; } } }

    // es-AR number formatting for currency and percent
    var fmtARS = new Intl.NumberFormat('es-AR',{style:'currency',currency:'ARS'});
    var fmtPct = new Intl.NumberFormat('es-AR',{minimumFractionDigits:1, maximumFractionDigits:1});
    function formatRow(r){
      if (!r || !r.tr || !r.tr.cells) return; var td=r.tr.cells;
      if (td.length >= 6){
        if (isFinite(r.data.priceFinal)) td[1].textContent = fmtARS.format(r.data.priceFinal);
        if (isFinite(r.data.unitPriceBase)) td[4].textContent = fmtARS.format(r.data.unitPriceBase);
        var txt = td[5].textContent || ''; var raw = parseFloat(txt.replace('%',''));
        if (isFinite(raw)) td[5].textContent = fmtPct.format(raw) + '%';
      }
    }
    rows.forEach(formatRow);

    // aria-sort according to current selection
    function updateAriaSort(){
      var thead = table.querySelector('thead'); if (!thead) return; var ths = thead.querySelectorAll('th');
      for (var i=0;i<ths.length;i++){ ths[i].removeAttribute('aria-sort'); }
      var key = (sortBy && sortBy.value) || '';
      var dir = (sortDirBtn && (sortDirBtn.dataset.dir||'asc')) || 'asc';
      var idx = null; if (key==='price_final') idx=1; else if (key==='unit_price_base') idx=4; else if (key==='cost_item_ae') idx=5;
      if (idx!=null && ths[idx]) ths[idx].setAttribute('aria-sort', dir==='asc'?'ascending':'descending');
    }
    updateAriaSort();
    if (sortBy) sortBy.addEventListener('change', updateAriaSort);
    if (sortDirBtn) sortDirBtn.addEventListener('click', updateAriaSort);

    // Category summary (participation in CBA AE)
    try {
      var totals = Object.create(null);
      rows.forEach(function(r){
        var cat = r.data.category || 'otros';
        var v = r.data.costAe; if (!isFinite(v) || v<=0) return;
        totals[cat] = (totals[cat]||0) + v;
      });
      var pairs = Object.keys(totals).map(function(k){ return [k, totals[k]]; }).sort(function(a,b){ return b[1]-a[1]; });
      var sum = pairs.reduce(function(acc,p){ return acc + p[1]; }, 0);
      var ul = document.createElement('ul'); ul.className = 'cat-summary';
      pairs.slice(0,8).forEach(function(p){
        var li = document.createElement('li');
        var lhs = document.createElement('span'); lhs.className = 'label'; lhs.textContent = p[0] || 'otros';
        var mid = document.createElement('span'); mid.className = 'num'; mid.textContent = fmtARS.format(p[1]);
        var rhs = document.createElement('span'); rhs.className = 'num'; rhs.textContent = fmtPct.format((p[1]/(sum||1))*100) + '%';
        li.appendChild(lhs); li.appendChild(mid); li.appendChild(rhs); ul.appendChild(li);
      });
      var cards = document.querySelectorAll('section.grid .card');
      if (cards && cards.length>=2){
        var right = cards[1];
        var title = document.createElement('div'); title.className='section-title'; title.textContent = 'Categorias (participacion)';
        right.appendChild(title); right.appendChild(ul);
      }
    } catch(e){}
  })();
  </script>
    """

    # If Jinja2 is available, render with templates
    if Environment is not None:
        env = Environment(
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
            autoescape=select_autoescape(['html'])
        )
        # filters
        def currency(v):
            try:
                s = f"${float(v):,.2f}"
            except Exception:
                s = "$0,00"
            # swap separators to es-AR
            s = s.replace(',', 'X').replace('.', ',').replace('X', '.')
            return s
        def number(v, nd=2):
            try:
                f = (f"{{:.{nd}f}}".format(float(v)))
            except Exception:
                f = "0"
            return f.replace('.', ',')
        def pct(v):
            try:
                return number(v,1) + '%'
            except Exception:
                return '0,0%'
        env.filters['currency'] = currency
        env.filters['number'] = number
        env.filters['pct'] = pct
        tpl = env.get_template('report.html')
        kpis = {
            'cba_ae': float(latest.get('cba_ae', 0) or 0),
            'cba_family': float(latest.get('cba_family', 0) or 0),
            'idx': float(latest.get('idx', 0) or 0),
            'mom': (str(latest.get('mom'))+'%') if latest.get('mom') else None,
            'yoy': (str(latest.get('yoy'))+'%') if latest.get('yoy') else None,
        }
        summary = {
            'total': s['total_items'],
            'valid': s['valid_items'],
            'valid_ratio': s['valid_ratio']*100.0,
            'promo': s['promo_count'],
            'oos': s['oos_count'],
            'cba_ae_sum': s['cba_ae_sum'],
        }
        source = "La An&oacute;nima &ndash; Suc. Ushuaia 5 (precios finales, promos incluidas)"
        html = tpl.render(title=f"IPC Ushuaia — Reporte {period}", period=period,
                          kpis=kpis, summary=summary, rows=rows_en, top=top_en,
                          chart_html=chart_html, source=source)
        # write with xmlcharrefreplace to avoid mojibake in any environment
        try:
            html = html.encode('ascii','xmlcharrefreplace').decode('ascii')
        except Exception:
            pass
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return

    # Fallback: old inline HTML (kept for compatibility)
    html = f"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>IPC Ushuaia — Reporte {period}</title>
  <style>
    :root {{ --bg:#f7f9fb; --card:#fff; --muted:#667085; --border:#e5e7eb; --ink:#0f172a; --accent:#1976d2; --strike:#9ca3af; --promo:#b91c1c; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--ink); font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Liberation Sans', sans-serif; }}
    .container {{ max-width:1100px; margin:0 auto; padding:24px; }}
    header {{ text-align:center; margin-bottom:16px; }}
    header h1 {{ margin:8px 0 4px; font-size:28px; }}
    header .period {{ color:var(--muted); font-size:14px; }}
    .kpis {{ display:grid; grid-template-columns: repeat(5, 1fr); gap:12px; margin:18px 0 8px; }}
    .card {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:14px; box-shadow:0 1px 2px rgba(16,24,40,.04); }}
    .kpi .label {{ color:var(--muted); font-size:12px; }}
    .kpi .value {{ font-size:20px; font-weight:700; margin-top:2px; }}
    .section-title {{ margin:14px 0 8px; font-size:18px; }}
    .chart {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:10px; text-align:center; }}
    .grid {{ display:grid; grid-template-columns: 1fr 1fr; gap:14px; align-items:start; }}
    table {{ border-collapse:collapse; width:100%; background:var(--card); border:1px solid var(--border); border-radius:10px; overflow:hidden; }}
    thead th {{ background:#f3f4f6; color:#111827; font-weight:600; font-size:13px; }}
    th, td {{ padding:8px 10px; border-bottom:1px solid var(--border); text-align:left; }}
    tbody tr:nth-child(even) {{ background:#fafafa; }}
    td.num {{ text-align:right; font-variant-numeric: tabular-nums; }}
    .muted {{ color:var(--muted); }}
    footer {{ margin:18px 0 6px; color:var(--muted); font-size:13px; text-align:center; }}
    a {{ color:var(--accent); text-decoration:none; }}
    a:hover {{ text-decoration:underline; }}
    .orig {{ color: var(--strike); text-decoration: line-through; margin-right: 6px; }}
    .promo {{ color: var(--promo); font-weight: 700; }}
    /* Helpers para celda de Ã­tem */
    .item-main {{ font-weight: 600; }}
    .item-meta {{ color: var(--muted); font-size: 12px; margin-top: 2px; }}
    .chip {{ display:inline-block; font-size:11px; padding:2px 6px; border-radius:999px; border:1px solid var(--border); background:#fff; margin-left:6px; }}
    .chip-cba {{ border-color:#16a34a; color:#166534; }}
    .chip-tier {{ border-color:#94a3b8; color:#334155; }}
    /* Filtros: diseÃ±o mÃ­nimo accesible */
    .filters {{ margin: 16px 0; }}
    .controls-grid {{ display:grid; grid-template-columns: 2fr 1fr 1fr; gap:12px; align-items:end; }}
    .control label {{ display:block; font-size:12px; color:var(--muted); margin-bottom:6px; }}
    .control .row {{ display:flex; gap:8px; align-items:center; }}
    .control input[type='search'],
    .control input[type='number'],
    .control select {{ width:100%; padding:8px 10px; border:1px solid var(--border); border-radius:8px; background:#fff; }}
    .option-row {{ display:flex; flex-wrap:wrap; gap:8px; }}
    .option-row label {{ display:inline-flex; align-items:center; gap:6px; border:1px solid var(--border); padding:6px 8px; border-radius:999px; cursor:pointer; background:#fff; }}
    button#sort-dir, button#reset-filters {{ border:1px solid var(--border); background:#fff; border-radius:8px; padding:8px 10px; cursor:pointer; }}
    button#sort-dir:focus, button#reset-filters:focus, .control input:focus, .control select:focus {{ outline:2px solid var(--accent); outline-offset:2px; }}
    @media (max-width: 900px) {{ .grid {{ grid-template-columns:1fr; }} .kpis {{ grid-template-columns: repeat(2, 1fr); }} .controls-grid {{ grid-template-columns:1fr; }} }}

    /* Columnas finales explícitas: no ocultamos columnas dinámicamente */

    /* Filtros visibles (categoria, marca, CBA, rangos). Header sticky */
    thead th {{ position: sticky; top: 0; z-index: 1; }}



  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>IPC Ushuaia &mdash; Canasta B&aacute;sica Alimentaria</h1>
      <div class="period">Reporte del per&iacute;odo {period}</div>
    </header>

    <section class="kpis">
      <div class="card kpi"><div class="label">CBA AE</div><div class="value">{fmt_money(latest.get('cba_ae', 0))}</div></div>
      <div class=" card kpi\><div class=\label\>CBA Familia (x3,09)</div><div class=\value\>{fmt_money(latest.get('cba_family', 0))}</div></div>
 <div class=\card kpi\><div class=\label\>&Iacute;ndice (base=100)</div><div class=\value\>{float(latest.get('idx', 0) or 0):.2f}</div></div>
 <div class=\card kpi\><div class=\label\>m/m</div><div class=\value\>{(str(latest.get('mom'))+'%') if latest.get('mom') else 'N/D'}</div></div>
 <div class=\card kpi\><div class=\label\>i.a.</div><div class=\value\>{(str(latest.get('yoy'))+'%') if latest.get('yoy') else 'N/D'}</div></div>
      <div class="muted" style="margin-top:6px">Nota: "Qty base" indica el tamaÃ±o de la presentaciÃ³n normalizado a kg/l/unidad y puede ser decimal (ej.: 0,47 l). Se usa para calcular el precio unitario y el costo por AE.</div>
    </section>

    <section class="grid">
        <div class=" section-title\>Serie del &iacute;ndice (base=100)</div>
 {chart_html}
        
      </div>
      <div class="card">
        <div class="section-title">Resumen del perÃ­odo</div>
        <table>
          <tbody>
            <tr><th>Total Ã­tems</th><td class="num">{s['total_items']}</td></tr>
            <tr><th>Con precio vÃ¡lido</th><td class="num">{s['valid_items']} ({s['valid_ratio']*100:.1f}%)</td></tr>
            <tr><th>En promociÃ³n</th><td class="num">{s['promo_count']}</td></tr>
            <tr><th>Sin stock</th><td class="num">{s['oos_count']}</td></tr>
            <tr><th>Suma costo AE</th><td class="num">{fmt_money(s['cba_ae_sum'])}</td></tr>
          </tbody>
        </table>
        <div class="muted" style="margin-top:8px">Fuente: La AnÃ³nima Online (sucursal Ushuaia). Precios finales (promos vigentes incluidas).</div>
      </div>
    </section>

    <div class="muted" style="margin:12px 0">
      <a href="../exports/breakdown_{period}.csv" download>Descargar breakdown CSV</a>
       · <a href="../docs/DATA_MODEL_GUIDE.md" target="_blank" rel="noopener">Diccionario de datos</a>
    </div>

    <section class="card filters" id="filters" role="region" aria-label="Filtros del desglose">
      <div class="section-title">Explorar desglose</div>
      <form id="filter-form" onsubmit="return false;">
        <div class="controls-grid">
          <div class="control">
            <label for="search">Buscar (tÃ­tulo o item_id)</label>
            <input type="search" id="search" placeholder="Ej: yerba 1 kg" />
          </div>
          <div class="control">
            <label for="category">CategorÃ­a</label>
            <select id="category"><option value="">Todas</option></select>
          </div>
          <div class="control">
            <label>Marca (nivel)</label>
            <div id="brand-tier-options" class="option-row" aria-label="Niveles de marca"></div>
          </div>
          <div class="control">
            <label>Incluido en CBA</label>
            <div id="cba-flag-options" class="option-row" aria-label="Incluido en CBA"></div>
          </div>
          <div class="control">
            <label for="min-price">Precio final ($)</label>
            <div class="row">
              <input type="number" id="min-price" step="0.01" inputmode="decimal" placeholder="mÃ­n" />
              <input type="number" id="max-price" step="0.01" inputmode="decimal" placeholder="mÃ¡x" />
            </div>
          </div>
          <div class="control">
            <label for="sort-by">Ordenar por</label>
            <div class="row">
              <select id="sort-by">
                <option value="">Relevancia</option>
                <option value="price_final">Precio final</option>
                <option value="unit_price_base">Precio unitario</option>
                <option value="cost_item_ae">Costo AE</option>
              </select>
              <button type="button" id="sort-dir" aria-label="Cambiar orden" title="Cambiar orden" data-dir="asc">Asc</button>
            </div>
          </div>
          <div class="control actions">
            <label>&nbsp;</label>
            <div class="row"><button type="button" id="reset-filters" title="Restablecer filtros">Reset</button></div>
          </div>
        </div>
        <div id="filter-status" class="muted" aria-live="polite" style="margin-top:8px">&nbsp;</div>
      </form>
      <noscript><div class="muted">Los filtros requieren JavaScript. La tabla funciona sin interacciÃ³n.</div></noscript>
    </section>

    <section style="margin-top:16px;">
      <div class="section-title">Top aportes al costo (AE)</div>
      <table>
        <thead><tr><th>&Iacute;tem</th><th>Precio final</th><th>Tama&ntilde;o</th><th>Precio unitario</th><th>Part. AE</th></tr></thead>
        <tbody>
          {''.join(row_html_v2(r) for r in top_cost)}
        </tbody>
      </table>
    </section>

    <section style="margin-top:16px;">
      <div class="section-title">Desglose completo</div>
      <table id="breakdown-table">
        <thead><tr><th>&Iacute;tem</th><th>Precio final</th><th>Tama&ntilde;o</th><th>Precio unitario</th><th>Part. AE</th></tr></thead>
        <tbody>
          {breakdown_rows}
        </tbody>
      </table>
    </section>

    <footer>
      <div>Ãndice base=100 en el primer perÃ­odo. Canasta fija; sustituciones documentadas ante faltantes. Unidades normalizadas a kg/L/unidad.</div>
      <div>Este reporte se generÃ³ automÃ¡ticamente con IPC Ushuaia.</div>
    </footer>
  </div>
  {script_js}
</body>
</html>
"""
    # Normalize common mojibake and ensure Spanish diacritics render via entities
    def _normalize_es(text: str) -> str:
        replacements = {
            # Common mojibake sequences -> HTML entities
            'B�sica': 'B&aacute;sica',
            'per��odo': 'per&iacute;odo',
            'per�odo': 'per&iacute;odo',
            'presentaci��n': 'presentaci&oacute;n',
            'tama��o': 'tama&ntilde;o',
            '��ndice': '&iacute;ndice',
            '�?�ndice': '&Iacute;ndice',
            '�?ndice': '&Iacute;ndice',
            '��tems': '&iacute;tems',
            'vǭlido': 'v&aacute;lido',
            'promoci��n': 'promoci&oacute;n',
            'Canasta B�sica': 'Canasta B&aacute;sica',
            'Índice': '&Iacute;ndice',  # safe fallback
            'índice': '&iacute;ndice',
            'ítems': '&iacute;tems',
            '—': '&mdash;',  # convert dash to entity to avoid encoding issues
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        return text

    html = _normalize_es(html)
    try:
        # Fallback: escape any remaining non-ASCII characters to HTML entities
        html = html.encode('ascii', 'xmlcharrefreplace').decode('ascii')
    except Exception:
        pass
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)


def export_pdf(html_path: str, pdf_path: str) -> None:
    """Render a local HTML file to PDF using Playwright/Chromium."""
    abs_html = os.path.abspath(html_path)
    file_url = 'file://' + abs_html.replace('\\', '/')
    os.makedirs(os.path.dirname(os.path.abspath(pdf_path)) or '.', exist_ok=True)
    p = sync_playwright().start()
    try:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(file_url, wait_until='load')
        page.pdf(path=pdf_path, format='A4', print_background=True)
        context.close()
        browser.close()
    finally:
        p.stop()


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='Renderiza reporte HTML a partir de exports existentes')
    ap.add_argument('--period', required=True, help='YYYY-MM')
    ap.add_argument('--in', dest='infile', required=False, help='Ruta a breakdown_<period>.csv (por defecto exports/breakdown_<period>.csv)')
    ap.add_argument('--series', dest='series', required=False, help='Ruta a series_cba.csv (por defecto exports/series_cba.csv)')
    ap.add_argument('--out', dest='out', required=False, default=None, help='Salida: directorio o archivo .html (default reports/<period>.html)')
    ap.add_argument('--outdir', dest='outdir', default=None, help='[DEPRECADO] Directorio de salida (usar --out)')
    ap.add_argument('--write-by-category', action='store_true', help='Escribe CSVs by_category/<categoria>.csv con brand_tier normalizado')
    args = ap.parse_args()
    period = args.period
    breakdown_path = args.infile or os.path.join('exports', f'breakdown_{period}.csv')
    series_path = args.series or os.path.join('exports', 'series_cba.csv')
    # Resolver salida
    out_arg = args.out or args.outdir or 'reports'
    if out_arg.lower().endswith('.html'):
        out_path = out_arg
    else:
        out_path = os.path.join(out_arg, f'{period}.html')
    render_report(out_path, period, series_path, breakdown_path, write_by_category=bool(args.write_by_category))









