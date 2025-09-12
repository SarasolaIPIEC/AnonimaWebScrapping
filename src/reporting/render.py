import csv
import os
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright


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
            if str(r.get('promo_flag', '')).lower() in ('1', 'true', 'yes', 'si', 'sí'):
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


def render_report(out_path: str, period: str, series_path: str, breakdown_path: str) -> None:
    series = _read_series(series_path)
    breakdown = _read_breakdown(breakdown_path)
    series_sorted = sorted(series, key=lambda r: r['period'])
    latest = series_sorted[-1] if series_sorted else {}
    svg = _svg_line(series_sorted)

    # Aggregates
    s = _summarize_breakdown(breakdown)
    top_cost = sorted(breakdown, key=lambda r: float(r.get('cost_item_ae') or 0), reverse=True)[:8]

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
        m = _re.match(r"([A-Za-zÁÉÍÓÚÜÑ&' ]+)", t)
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

    def row_html(r: Dict[str, Any]) -> str:
        url = r.get('url') or ''
        title = r.get('title') or ''
        if title.lower().strip() in ('almacén', 'almacen', 'producto') or len(title.strip()) < 4:
            title = r.get('name') or title
        brand = derive_brand(title)
        name = (brand + ' ' if brand else '') + (r.get('name') or '')
        qty = r.get('qty_base') or ''
        unit = r.get('unit') or ''
        cost = fmt_money(r.get('cost_item_ae') or 0)
        promo = 'Sí' if str(r.get('promo_flag', '')).lower() in ('1', 'true', 'yes', 'si', 'sí') else 'No'
        stock = 'Sí' if str(r.get('in_stock', '1')).lower() in ('1', 'true', 'yes', 'si', 'sí') else 'No'
        link = f"<a href='{url}' target='_blank' rel='noopener'>{title or '(ver producto)'}</a>" if url else title
        return f"<tr><td>{name}</td><td>{link}</td><td class='num'>{price_cell(r)}</td><td class='num'>{qty}</td><td>{unit}</td><td class='num'>{cost}</td><td>{promo}</td><td>{stock}</td></tr>"

    breakdown_rows = '\n'.join(row_html(r) for r in breakdown)

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
    @media (max-width: 900px) {{ .grid {{ grid-template-columns:1fr; }} .kpis {{ grid-template-columns: repeat(2, 1fr); }} }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>IPC Ushuaia — Canasta Básica Alimentaria</h1>
      <div class="period">Reporte del período {period}</div>
    </header>

    <section class="kpis">
      <div class="card kpi"><div class="label">CBA AE</div><div class="value">{fmt_money(latest.get('cba_ae', 0))}</div></div>
      <div class="card kpi"><div class="label">CBA Familia (×3,09)</div><div class="value">{fmt_money(latest.get('cba_family', 0))}</div></div>
      <div class="card kpi"><div class="label">Índice (base=100)</div><div class="value">{float(latest.get('idx', 0) or 0):.2f}</div></div>
      <div class="card kpi"><div class="label">m/m</div><div class="value">{latest.get('mom','') if latest.get('mom') else '—'}%</div></div>
      <div class="card kpi"><div class="label">i.a.</div><div class="value">{latest.get('yoy','') if latest.get('yoy') else '—'}%</div></div>
    </section>

    <section class="grid">
      <div class="chart card">
        <div class="section-title">Serie del índice (base=100)</div>
        {svg}
      </div>
      <div class="card">
        <div class="section-title">Resumen del período</div>
        <table>
          <tbody>
            <tr><th>Total ítems</th><td class="num">{s['total_items']}</td></tr>
            <tr><th>Con precio válido</th><td class="num">{s['valid_items']} ({s['valid_ratio']*100:.1f}%)</td></tr>
            <tr><th>En promoción</th><td class="num">{s['promo_count']}</td></tr>
            <tr><th>Sin stock</th><td class="num">{s['oos_count']}</td></tr>
            <tr><th>Suma costo AE</th><td class="num">{fmt_money(s['cba_ae_sum'])}</td></tr>
          </tbody>
        </table>
        <div class="muted" style="margin-top:8px">Fuente: La Anónima Online (sucursal Ushuaia). Precios finales (promos vigentes incluidas).</div>
      </div>
    </section>

    <section style="margin-top:16px;">
      <div class="section-title">Top aportes al costo (AE)</div>
      <table>
        <thead><tr><th>Ítem</th><th>Producto</th><th>Precio</th><th>Qty base</th><th>Unidad</th><th>Costo AE</th><th>Promo</th><th>Stock</th></tr></thead>
        <tbody>
          {''.join(row_html(r) for r in top_cost)}
        </tbody>
      </table>
    </section>

    <section style="margin-top:16px;">
      <div class="section-title">Desglose completo</div>
      <table>
        <thead><tr><th>Ítem</th><th>Producto</th><th>Precio</th><th>Qty base</th><th>Unidad</th><th>Costo AE</th><th>Promo</th><th>Stock</th></tr></thead>
        <tbody>
          {breakdown_rows}
        </tbody>
      </table>
    </section>

    <footer>
      <div>Índice base=100 en el primer período. Canasta fija; sustituciones documentadas ante faltantes. Unidades normalizadas a kg/L/unidad.</div>
      <div>Este reporte se generó automáticamente con IPC Ushuaia.</div>
    </footer>
  </div>
</body>
</html>
"""
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

