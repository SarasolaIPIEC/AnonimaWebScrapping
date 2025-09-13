import csv
import os
import math
from typing import List, Dict, Any, Tuple


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


def _period_minus(period: str, months: int = 1) -> str:
    y, m = period.split('-')
    y = int(y)
    m = int(m)
    total = y * 12 + (m - 1) - months
    ny = total // 12
    nm = (total % 12) + 1
    return f"{ny:04d}-{nm:02d}"


def _fmt_num_es_ar(value: Any, decimals: int = 2) -> str:
    try:
        n = float(value)
    except Exception:
        return 'N/D'
    if math.isnan(n) or math.isinf(n):
        return 'N/D'
    s = f"{n:,.{decimals}f}"
    # Convert en-US to es-AR (thousands dot, decimal comma)
    s = s.replace(',', 'X').replace('.', ',').replace('X', '.')
    return s


def _fmt_money_es_ar(value: Any) -> str:
    try:
        n = float(value)
    except Exception:
        return '$ N/D'
    # Flexible: sin decimales si .00
    cents = abs(round(n*100) - round(n)*100)
    if cents == 0:
        s = _fmt_num_es_ar(n, 0)
    else:
        s = _fmt_num_es_ar(n, 2)
    return f"$ {s}"


def _svg_line(series: List[Dict[str, Any]], width=960, height=240, margin=40) -> str:
    # Render only with 2+ points; else return empty string
    if not series or len(series) < 2:
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


def _parse_float_maybe(v: Any) -> float:
    if v in (None, ''):
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace('\u00A0', ' ').replace(' ', '')
    # remove currency symbol if any
    s = s.replace('$', '')
    # normalize decimal comma
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s and '.' not in s:
        s = s.replace('.', '').replace(',', '.')
    try:
        return float(s)
    except Exception:
        return 0.0


def _summarize_breakdown(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_items = len(rows)
    valid = sum(1 for r in rows if _parse_float_maybe(r.get('price_final')) > 0)
    promo = sum(1 for r in rows if str(r.get('promo_flag', '')).lower() in ('1', 'true', 'yes', 'si', 'sí'))
    oos = sum(1 for r in rows if str(r.get('in_stock', '1')).lower() in ('0', 'false', 'no'))
    cba_ae = 0.0
    for r in rows:
        if str(r.get('cba_flag','')).strip().lower() in ('si','true','1','yes'):
            cba_ae += _parse_float_maybe(r.get('cost_item_ae'))
    ratio = (valid / total_items) if total_items else 0.0
    return {
        'total_items': total_items,
        'valid_items': valid,
        'valid_ratio': ratio,
        'promo_count': promo,
        'oos_count': oos,
        'cba_ae_sum': cba_ae,
    }


def _enrich_rows(period: str, breakdown: List[Dict[str, Any]], breakdown_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[Dict[str, Any]], List[Tuple[str, float, float]]]:
    # Compute aporte %, var m/m, shrink, presentation, etc.
    s = _summarize_breakdown(breakdown)
    total_cba = float(s['cba_ae_sum'] or 0.0)
    prev_period = _period_minus(period, 1)
    prev_path = os.path.join(os.path.dirname(breakdown_path), f"breakdown_{prev_period}.csv")
    prev_rows = { (r.get('item_id') or ''): r for r in _read_breakdown(prev_path) }
    prev12_period = _period_minus(period, 12)
    prev12_path = os.path.join(os.path.dirname(breakdown_path), f"breakdown_{prev12_period}.csv")
    prev12_rows = { (r.get('item_id') or ''): r for r in _read_breakdown(prev12_path) }

    enriched: List[Dict[str, Any]] = []
    cat_totals: Dict[str, float] = {}
    for r in breakdown:
        r = dict(r)
        pid = r.get('item_id') or ''
        # normalize numeric
        r['price_final'] = _parse_float_maybe(r.get('price_final'))
        r['price_original'] = _parse_float_maybe(r.get('price_original'))
        r['unit_price_base'] = _parse_float_maybe(r.get('unit_price_base'))
        r['cost_item_ae'] = _parse_float_maybe(r.get('cost_item_ae'))
        r['qty_base'] = _parse_float_maybe(r.get('qty_base'))
        r['expected_qty'] = _parse_float_maybe(r.get('expected_qty'))
        # aporte %
        r['aporte_pct'] = (r['cost_item_ae'] / total_cba * 100.0) if (total_cba > 0 and r['cost_item_ae'] > 0) else None
        # shrinkflation flag
        try:
            prev = prev_rows.get(pid)
            q_prev = _parse_float_maybe(prev.get('qty_base')) if prev else 0.0
            r['shrink_flag'] = (r['qty_base'] > 0 and q_prev > 0 and abs(r['qty_base'] - q_prev) / q_prev >= 0.05)
        except Exception:
            r['shrink_flag'] = False
        # variaciones m/m
        try:
            prev = prev_rows.get(pid)
            u_prev = _parse_float_maybe(prev.get('unit_price_base')) if prev else 0.0
            p_prev = _parse_float_maybe(prev.get('price_final')) if prev else 0.0
            r['var_mom_unit_pct'] = ((r['unit_price_base'] / u_prev) - 1.0) * 100.0 if (r['unit_price_base'] > 0 and u_prev > 0) else None
            r['var_mom_price_pct'] = ((r['price_final'] / p_prev) - 1.0) * 100.0 if (r['price_final'] > 0 and p_prev > 0) else None
        except Exception:
            r['var_mom_unit_pct'] = None
            r['var_mom_price_pct'] = None
        # variación i.a. unitario (opcional)
        try:
            p12 = prev12_rows.get(pid)
            u12 = _parse_float_maybe(p12.get('unit_price_base')) if p12 else 0.0
            r['var_yoy_unit_pct'] = ((r['unit_price_base'] / u12) - 1.0) * 100.0 if (r['unit_price_base'] > 0 and u12 > 0) else None
        except Exception:
            r['var_yoy_unit_pct'] = None
        # presentation text
        pres = ''
        unit = (r.get('unit') or '').strip().lower()
        q = r['qty_base']
        try:
            if unit == 'kg' and q > 0:
                pres = f"x {_fmt_num_es_ar(q,2)} kg"
            elif unit in ('l', 'lt', 'litro', 'litros') and q > 0:
                pres = f"{_fmt_num_es_ar(q,2)} L"
            elif unit == 'unit' and abs(q-12.0) < 0.01:
                pres = 'docena'
            elif unit == 'unit' and q > 0:
                pres = f"{int(q)} u" if abs(q - round(q)) < 1e-6 else f"{_fmt_num_es_ar(q,2)} u"
        except Exception:
            pres = ''
        r['presentation_text'] = pres
        # atípico por tamaño
        atypical = ''
        try:
            eq = r['expected_qty']
            if q>0 and eq>0:
                ratio = min(q,eq)/max(q,eq)
                atypical = '1' if ratio < 0.85 else ''
        except Exception:
            atypical = ''
        r['atypical'] = atypical
        # chips flags (mantener texto fuente)
        r['promo_flag'] = str(r.get('promo_flag', '')).lower() in ('1','true','yes','si','sí')
        r['in_stock'] = str(r.get('in_stock', '1')).lower() in ('1','true','yes','si','sí')
        # price per kg/L (for display and filter)
        unit = (r.get('unit') or '').strip().lower()
        per = None
        per_txt = None
        if unit in ('kg','kilo','kilogramo') and r['qty_base']>0:
            per = r['price_final']/r['qty_base'] if r['price_final']>0 else None
            per_txt = (f"{_fmt_money_es_ar(per)} x Kg" if per else None)
        elif unit in ('l','lt','litro','litros') and r['qty_base']>0:
            per = r['price_final']/r['qty_base'] if r['price_final']>0 else None
            per_txt = (f"{_fmt_money_es_ar(per)} x L" if per else None)
        r['price_per_kgl'] = per
        r['price_per_kgl_text'] = per_txt
        # category totals
        cat = (r.get('category') or '').strip() or 'N/D'
        cat_totals[cat] = cat_totals.get(cat, 0.0) + r['cost_item_ae']
        enriched.append(r)

    # category summary rows
    cat_rows = []
    for cat, val in sorted(cat_totals.items(), key=lambda kv: kv[1], reverse=True):
        share = (val / total_cba * 100.0) if total_cba > 0 else 0.0
        cat_rows.append((cat, val, share))

    # top aportes
    top_cost = sorted(enriched, key=lambda r: float(r.get('cost_item_ae') or 0.0), reverse=True)[:8]
    return enriched, s, top_cost, cat_rows


def _kpis_from_series(series_sorted: List[Dict[str, Any]]) -> Dict[str, str]:
    latest = series_sorted[-1] if series_sorted else {}
    kpi = {
        'cba_ae': _fmt_money_es_ar(latest.get('cba_ae', 0) or 0),
        'cba_family': _fmt_money_es_ar(latest.get('cba_family', 0) or 0),
        'idx': _fmt_num_es_ar(latest.get('idx', 0) or 0, 2) if latest.get('idx') else 'N/D',
        'mom': (latest.get('mom') if latest.get('mom') not in (None, '') else 'N/D'),
        'yoy': (latest.get('yoy') if latest.get('yoy') not in (None, '') else 'N/D'),
    }
    return kpi


def _downloads(out_path: str, period: str, series_path: str, breakdown_path: str) -> Dict[str, str]:
    def rel(to_path: str) -> str:
        try:
            return os.path.relpath(to_path, start=os.path.dirname(out_path)).replace('\\', '/')
        except Exception:
            return to_path.replace('\\', '/')
    rel_breakdown = rel(breakdown_path)
    rel_series = rel(series_path)
    dict_path = os.path.join('docs', 'data_dictionary.csv')
    rel_dict = rel(dict_path) if os.path.exists(dict_path) else ''
    evid_root = 'evidence'
    rel_log = ''
    if os.path.isdir(evid_root):
        subdirs = [d for d in os.listdir(evid_root) if d.startswith(period + '_') and os.path.isdir(os.path.join(evid_root, d))]
        subdirs.sort(reverse=True)
        if subdirs:
            log_path = os.path.join(evid_root, subdirs[0], f"run_{period}.jsonl")
            if os.path.exists(log_path):
                rel_log = rel(log_path)
    return {
        'breakdown': rel_breakdown,
        'series': rel_series,
        'dict': rel_dict,
        'log': rel_log,
    }


def render_report(out_path: str, period: str, series_path: str, breakdown_path: str) -> None:
    # Load exports
    series = _read_series(series_path)
    series_sorted = sorted(series, key=lambda r: r['period'])
    breakdown = _read_breakdown(breakdown_path)

    # Enrich + metrics
    rows, s, top_cost, cat_rows = _enrich_rows(period, breakdown, breakdown_path)
    kpis = _kpis_from_series(series_sorted)
    chart_svg = _svg_line(series_sorted)
    downloads = _downloads(out_path, period, series_path, breakdown_path)

    # Embed JSON dataset for chart (oficial)
    def _float_or_none(v):
        try:
            return float(v)
        except Exception:
            return None
    series_json = [
        {
            'period': r.get('period'),
            'cba_ae': _float_or_none(r.get('cba_ae')),
            'cba_family': _float_or_none(r.get('cba_family')),
            'idx': _float_or_none(r.get('idx')),
            'mom': _float_or_none(r.get('mom')),
            'yoy': _float_or_none(r.get('yoy')),
        } for r in series_sorted
    ]


    # Prepare template context
    ctx = {
        'period': period,
        'kpi': kpis,
        'svg': chart_svg,
        'summary': {
            'total_items': s['total_items'],
            'valid_items': s['valid_items'],
            'valid_ratio_pct': f"{s['valid_ratio']*100:.1f}",
            'promo_count': s['promo_count'],
            'oos_count': s['oos_count'],
            'cba_ae_sum': _fmt_money_es_ar(s['cba_ae_sum']),
        },
        'rows': rows,
        'top_cost': top_cost,
        'category_summary': [{'category': c, 'subtotal': _fmt_money_es_ar(v), 'share_pct': _fmt_num_es_ar(p,2)} for c,v,p in cat_rows],
        'downloads': downloads,
        'no_series_msg': ('' if chart_svg else 'Aún no hay serie histórica'),
        'series_json': series_json,
        # no custom overlays
    }

    # Render with Jinja2
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except Exception as e:
        raise RuntimeError('Jinja2 no instalado. Instale dependencias con: pip install -r requirements.txt') from e

    tpl_dir = os.path.join(os.path.dirname(__file__), 'templates')
    env = Environment(
        loader=FileSystemLoader(tpl_dir),
        autoescape=select_autoescape(['html']),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters['money'] = _fmt_money_es_ar
    env.filters['num'] = _fmt_num_es_ar
    import json as _json
    env.filters['tojson'] = lambda v: _json.dumps(v, ensure_ascii=False)

    tpl = env.get_template('report.html')
    html = tpl.render(**ctx)
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)


def export_pdf(html_path: str, pdf_path: str) -> None:
    """Render a local HTML file to PDF using Playwright/Chromium."""
    from playwright.sync_api import sync_playwright
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


if __name__ == '__main__':  # Standalone regeneration
    import argparse
    parser = argparse.ArgumentParser(description='Renderiza reporte HTML desde CSVs exportados')
    parser.add_argument('--period', required=True, help='YYYY-MM')
    parser.add_argument('--series', default='exports/series_cba.csv', help='Ruta a series_cba.csv')
    parser.add_argument('--breakdown', help='Ruta a breakdown_<period>.csv (por defecto se infiere)')
    parser.add_argument('--out', help='Ruta de salida reports/<period>.html')
    args = parser.parse_args()
    period = args.period
    series_path = args.series
    breakdown_path = args.breakdown or os.path.join('exports', f'breakdown_{period}.csv')
    out_path = args.out or os.path.join('reports', f'{period}.html')
    render_report(out_path, period, series_path, breakdown_path)
    print(f"Reporte generado: {out_path}")
