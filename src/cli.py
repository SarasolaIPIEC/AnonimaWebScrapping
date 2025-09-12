import argparse
import re
import csv
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

from pathlib import Path

from .site.search import run_searches
from .normalize.pricing import compute_item_costs
from .metrics.cba import compute_cba_values
from .metrics.index import update_series
from .reporting.render import render_report
from .site.utils import json_log


def load_selectors(config_path: str) -> Dict[str, Any]:
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def ensure_dirs(paths: List[str]) -> None:
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)


def ensure_catalog(path: str) -> None:
    if os.path.exists(path):
        return
    rows = [
        # item_id,name,preferred_keywords,fallback_keywords,expected_unit,expected_qty,monthly_qty_base
        ["arroz_1kg","Arroz 1 kg","arroz, largo fino","arroz","kg",1.0,2.0],
        ["harina000_1kg","Harina 000 1 kg","harina 000","harina","kg",1.0,2.0],
        ["fideos_1kg","Fideos 1 kg","fideos, tallarin, spaghetti","fideos","kg",1.0,1.5],
        ["aceite_girasol_1_5l","Aceite girasol 1.5 l","aceite, girasol","aceite girasol","l",1.5,1.0],
        ["azucar_1kg","AzÃºcar 1 kg","azucar","azucar","kg",1.0,1.5],
        ["yerba_1kg","Yerba mate 1 kg","yerba","yerba","kg",1.0,0.75],
        ["leche_1l","Leche 1 l","leche, entera","leche","l",1.0,10.0],
        ["huevos_docena","Huevos docena","huevos, docena","huevos","unit",12.0,2.0],
        ["carne_picada_1kg","Carne picada 1 kg","carne, picada","carne picada","kg",1.0,2.0],
        ["pollo_1kg","Pollo 1 kg","pollo","pollo","kg",1.0,2.0],
        ["pan_1kg","Pan 1 kg","pan","pan","kg",1.0,2.0],
        ["queso_cremoso_1kg","Queso cremoso 1 kg","queso, cremoso","queso cremoso","kg",1.0,0.8],
        ["manzana_1kg","Manzana 1 kg","manzana","manzana","kg",1.0,2.0],
        ["papa_1kg","Papa 1 kg","papa","papa","kg",1.0,3.0],
    ]
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'item_id','name','preferred_keywords','fallback_keywords','expected_unit','expected_qty','monthly_qty_base','size_tolerance'
        ])
        writer.writerows(rows)


def load_config_toml(path: str) -> Dict[str, Any]:
    # simple TOML reader for basic key=val pairs and [section] nesting
    if not os.path.exists(path):
        return {
            'base_url': 'https://supermercado.laanonimaonline.com/',
            'evidence_dir': 'evidence',
            'exports_dir': 'exports',
            'reports_dir': 'reports',
            'html_dump_dir': 'evidence/html',
            'branch_name': 'USHUAIA 5',
            'postal_code': '9410',
            'min_valid_price_ratio': 0.8,
            'family_ae': 3.09,
            'exclude_keywords': 'sabor,premium,light,oliva extra,integral,sin azÃºcar',
        }
    cfg: Dict[str, Any] = {}
    section = None
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('[') and line.endswith(']'):
                section = line[1:-1].strip()
                cfg.setdefault(section, {})
                continue
            if '=' in line:
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip().strip('"')
                if section:
                    cfg[section][k] = v
                else:
                    cfg[k] = v
    # flatten known keys
    flat = {}
    for d in [cfg, cfg.get('paths', {}), cfg.get('scraping', {}), cfg.get('business', {})]:
        flat.update(d)
    # types
    if 'min_valid_price_ratio' in flat:
        try:
            flat['min_valid_price_ratio'] = float(flat['min_valid_price_ratio'])
        except ValueError:
            flat['min_valid_price_ratio'] = 0.8
    if 'family_ae' in flat:
        try:
            flat['family_ae'] = float(flat['family_ae'])
        except ValueError:
            flat['family_ae'] = 3.09
    return flat


def read_catalog(path: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # split keywords lists
            row['preferred_keywords'] = [s.strip() for s in row.get('preferred_keywords','').split(',') if s.strip()]
            row['fallback_keywords'] = [s.strip() for s in row.get('fallback_keywords','').split(',') if s.strip()]
            row['expected_qty'] = float(row.get('expected_qty', '0') or 0)
            row['monthly_qty_base'] = float(row.get('monthly_qty_base', '0') or 0)
            try:
                row['size_tolerance'] = float(row.get('size_tolerance', '0.85') or 0.85)
            except Exception:
                row['size_tolerance'] = 0.85
            items.append(row)
    return items


def write_breakdown(path: str, period: str, rows: List[Dict[str, Any]]) -> None:
    fields = [
        'period','item_id','name','query','title','url','in_stock','promo_flag',
        'price_original','price_promo','price_final','unit_price_base','qty_base','expected_qty','cost_item_ae','substitution'
    ]
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            out = {k: r.get(k) for k in fields}
            writer.writerow(out)


def write_daily_prices(path: str, run_date: str, period: str, rows: List[Dict[str, Any]]) -> None:
    fields = [
        'date','period','item_id','name','query','title','url','price_original','price_promo','price_final','qty_base','unit','unit_price_base','in_stock','promo_flag'
    ]
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({
                'date': run_date,
                'period': period,
                'item_id': r.get('item_id'),
                'name': r.get('name'),
                'query': r.get('query'),
                'title': r.get('title'),
                'url': r.get('url'),
                'price_original': r.get('price_original'),
                'price_promo': r.get('price_promo'),
                'price_final': r.get('price_final'),
                'qty_base': r.get('qty_base'),
                'unit': r.get('unit'),
                'unit_price_base': r.get('unit_price_base'),
                'in_stock': r.get('in_stock'),
                'promo_flag': r.get('promo_flag'),
            })


def read_pins(path: str) -> Dict[str, Dict[str, Any]]:
    pins: Dict[str, Dict[str, Any]] = {}
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                pins[row['item_id']] = row
    return pins


def write_pins(path: str, results: List[Dict[str, Any]]) -> None:
    current = read_pins(path)
    for r in results:
        if r.get('item_id') and r.get('url') and r.get('title'):
            current[r['item_id']] = {
                'item_id': r['item_id'],
                'url': r['url'],
                'title': r['title']
            }
    os.makedirs(os.path.dirname(path) or 'data', exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['item_id','url','title'])
        w.writeheader()
        for v in current.values():
            w.writerow(v)


def parse_period(p: Optional[str]) -> str:
    if p:
        return p
    # default to current year-month
    return datetime.utcnow().strftime('%Y-%m')


def cmd_run(args: argparse.Namespace) -> int:
    period = parse_period(args.period)
    cfg = load_config_toml('config.toml')
    selectors = load_selectors('config/selectors.json')

    evidence_dir = cfg.get('evidence_dir', 'evidence')
    html_dump_dir = cfg.get('html_dump_dir', os.path.join(evidence_dir, 'html'))
    # Per-run evidence subfolder (period + local date)
    try:
        _now_local = datetime.now(ZoneInfo("America/Argentina/Ushuaia")) if ZoneInfo else datetime.utcnow()
        _date_str = _now_local.date().isoformat()
        evidence_dir = os.path.join(evidence_dir, f"{period}_{_date_str}")
        html_dump_dir = os.path.join(evidence_dir, 'html')
    except Exception:
        pass
    exports_dir = cfg.get('exports_dir', 'exports')
    reports_dir = cfg.get('reports_dir', 'reports')

    ensure_dirs([evidence_dir, html_dump_dir, exports_dir, reports_dir, 'data'])
    ensure_catalog('data/cba_catalog.csv')

    log_path = os.path.join(evidence_dir, f'run_{period}.jsonl')
    # Add checksums for traceability
    def _md5(path: str) -> str:
        import hashlib
        if not os.path.exists(path):
            return ''
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    json_log(log_path, 'start', {
        'period': period,
        'selectors_md5': _md5('config/selectors.json'),
        'catalog_md5': _md5('data/cba_catalog.csv'),
        'config_md5': _md5('config.toml')
    })

    # 1) Select branch via Playwright
    try:
        page = ensure_branch(
            base_url=cfg.get('base_url', 'https://supermercado.laanonimaonline.com/'),
            postal_code=cfg.get('postal_code', '9410'),
            branch_name=args.branch or cfg.get('branch_name', 'USHUAIA 5'),
            selectors=selectors,
            evidence_dir=evidence_dir,
            html_dump_dir=html_dump_dir,
            log_path=log_path,
            headless=(not args.debug),
            strict_verify=(not getattr(args, 'skip_branch_verify', False))
        )
    except Exception as e:
        json_log(log_path, 'error', {'stage': 'branch', 'error': str(e)})
        print(f"[FATAL] SelecciÃ³n de sucursal fallÃ³: {e}")
        return 1

    # 2) Read catalog and build queries
    catalog = read_catalog('data/cba_catalog.csv')
    exclude_keywords = [s.strip() for s in cfg.get('exclude_keywords', '').split(',') if s.strip()]

    # 3) Pinned SKUs first, then searches and extract
    try:
        results: List[Dict[str, Any]] = []
        # Pinned map
        pins_map: Dict[str, Dict[str, Any]] = {}
        if os.path.exists('data/sku_pins.csv'):
            with open('data/sku_pins.csv', 'r', encoding='utf-8') as f:
                for prow in csv.DictReader(f):
                    pins_map[prow['item_id']] = prow
        # Try pinned
        from .site.product import extract_product_page
        from .normalize.units import parse_title_size
        for row in catalog:
            pin = pins_map.get(row['item_id'])
            if not pin or not pin.get('url'):
                continue
            try:
                res = extract_product_page(
                    page,
                    url=pin['url'],
                    selectors=selectors,
                    evidence_dir=evidence_dir,
                    html_dump_dir=html_dump_dir,
                    save_basename=f"pinned_{row['item_id']}"
                )
                qb, un = parse_title_size(res.get('title') or '')
                res.update({
                    'item_id': row['item_id'],
                    'name': row['name'],
                    'query': 'PINNED',
                    'qty_base': qb,
                    'unit': un,
                    'expected_qty': row['expected_qty'],
                    'monthly_qty_base': row['monthly_qty_base'],
                    'substitution': ''
                })
                if res.get('price_final') and qb:
                    results.append(res)
            except Exception as e:
                json_log(log_path, 'pinned_error', {'item_id': row['item_id'], 'error': str(e)})

        remaining = [r for r in catalog if r['item_id'] not in {x['item_id'] for x in results}]
        search_results = run_searches(
            page=page,
            period=period,
            catalog=remaining,
            selectors=selectors,
            evidence_dir=evidence_dir,
            html_dump_dir=html_dump_dir,
            exclude_keywords=exclude_keywords,
            log_path=log_path,
            base_url=cfg.get('base_url', 'https://supermercado.laanonimaonline.com/')
        )
        results.extend(search_results)
    finally:
        # Keep the context open for post-mortem if debug; else close via page.context.close()
        try:
            if not args.debug:
                page.context.close()
                page.context.browser.close()
        except Exception:
            pass

    # 4) Normalize pricing and compute costs
    priced_rows = compute_item_costs(results)

    # 5) Aggregate CBA AE + Family
    family_ae = float(cfg.get('family_ae', 3.09))
    cba_ae, cba_family = compute_cba_values(priced_rows, family_ae)

    # 6) Update index series
    series_path = os.path.join(exports_dir, 'series_cba.csv')
    series_row = update_series(series_path, period, cba_ae, cba_family)

    # 7) Write breakdown
    breakdown_path = os.path.join(exports_dir, f'breakdown_{period}.csv')
    for r in priced_rows:
        r['period'] = period
    write_breakdown(breakdown_path, period, priced_rows)

    # 7b) Daily prices CSV (fecha del dÃ­a)
    run_date = (datetime.now(ZoneInfo("America/Argentina/Ushuaia")) if ZoneInfo else datetime.utcnow()).date().isoformat()
    daily_path = os.path.join(exports_dir, f'daily_prices_{run_date}.csv')
    write_daily_prices(daily_path, run_date, period, priced_rows)
    # 7c) Persist pins
    try:
        write_pins('data/sku_pins.csv', priced_rows)
    except Exception as e:
        json_log(log_path, 'pins_write_error', {'error': str(e)})

    # 8) Render report
    report_path = os.path.join(reports_dir, f'{period}.html')
    render_report(report_path, period, series_path, breakdown_path)

    # 9) Validations
    valid_prices = [r for r in priced_rows if isinstance(r.get('price_final'), (int, float)) and r['price_final'] > 0]
    ratio = len(valid_prices) / max(1, len(priced_rows))
    header_ok = series_row.get('period') == period and cba_ae > 0
    min_ratio = float(cfg.get('min_valid_price_ratio', 0.8))

    # 10) Summary
    print("=== Resumen IPC Ushuaia ===")
    print(f"Periodo: {period}")
    print(f"CBA AE: ${cba_ae:,.2f}")
    print(f"CBA Familia (x{family_ae}): ${cba_family:,.2f}")
    print(f"Series: {series_path}")
    print(f"Desglose: {breakdown_path}")
    print(f"Precios diarios: {daily_path}")
    print(f"Reporte: {report_path}")
    print(f"Evidencia: {evidence_dir}")
    print(f"% Ã­tems con precio vÃ¡lido: {ratio*100:.1f}%")

    if (not header_ok) or (ratio < min_ratio):
        print(f"[ERROR] Validaciones fallidas (header_ok={header_ok}, ratio={ratio:.2f} < {min_ratio:.2f})")
        return 1
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    period = parse_period(args.period)
    cfg = load_config_toml('config.toml')
    evidence_root = cfg.get('evidence_dir', 'evidence')
    exports_dir = cfg.get('exports_dir', 'exports')
    reports_dir = cfg.get('reports_dir', 'reports')
    catalog_path = 'data/cba_catalog.csv'

    # 1) Outputs existence
    breakdown_path = os.path.join(exports_dir, f'breakdown_{period}.csv')
    series_path = os.path.join(exports_dir, 'series_cba.csv')
    report_path = os.path.join(reports_dir, f'{period}.html')
    missing = [p for p in [breakdown_path, series_path, report_path] if not os.path.exists(p)]

    # 2) Evidence latest run for period
    latest_evd = None
    if os.path.isdir(evidence_root):
        subdirs = [d for d in os.listdir(evidence_root) if d.startswith(period + '_') and os.path.isdir(os.path.join(evidence_root, d))]
        subdirs.sort(reverse=True)
        if subdirs:
            latest_evd = os.path.join(evidence_root, subdirs[0])
    log_path = os.path.join(latest_evd, f'run_{period}.jsonl') if latest_evd else ''

    # 3) Read catalog and breakdown for coverage
    try:
        with open(catalog_path, 'r', encoding='utf-8') as f:
            cat_rows = list(csv.DictReader(f))
    except Exception:
        cat_rows = []
    try:
        with open(breakdown_path, 'r', encoding='utf-8') as f:
            brk_rows = list(csv.DictReader(f))
    except Exception:
        brk_rows = []
    expected = len(cat_rows)
    got = len(brk_rows)
    valid_prices = [r for r in brk_rows if r.get('price_final') not in (None, '', '0')]
    min_ratio = float(args.min_ratio) if getattr(args, 'min_ratio', None) is not None else float(cfg.get('min_valid_price_ratio', 0.8))
    ratio = (len(valid_prices) / max(1, got)) if got else 0.0

    # 4) Evidence checks
    branch_ok = False
    header_png = ''
    if latest_evd and os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        evt = json.loads(line)
                        if evt.get('event') == 'branch_ok':
                            branch_ok = True
                    except Exception:
                        continue
        except Exception:
            pass
        # find header screenshot
        for name in os.listdir(latest_evd):
            if name.startswith('header_after_branch') and name.endswith('.png'):
                header_png = os.path.join(latest_evd, name)
                break

    # 5) Print summary
    print('=== Verificación IPC Ushuaia ===')
    print(f"Periodo: {period}")
    print(f"Evidencia carpeta: {latest_evd or 'N/A'}")
    if missing:
        print(f"[FAIL] Faltan salidas: {', '.join(missing)}")
    else:
        print("[OK] Salidas principales presentes (breakdown/series/reporte)")
    print(f"Catálogo: {expected} ítems, Encontrados: {got}, Precios válidos: {len(valid_prices)} ({ratio*100:.1f}%)")
    print(f"Header Ushuaia verificado: {'Sí' if branch_ok else 'No'}")
    if header_png:
        print(f"Screenshot header: {header_png}")

    allow_missing = getattr(args, 'allow_missing_branch', False)
    ok = (not missing) and (branch_ok or allow_missing) and got >= max(1, int(expected * 0.6)) and ratio >= min_ratio
    if not ok:
        print(f"[ERROR] Verificación fallida (missing={bool(missing)}, branch_ok={branch_ok}, cobertura={got}/{expected}, ratio={ratio:.2f} < {min_ratio:.2f})")
        return 1
    print('[OK] Verificación exitosa')
    return 0


def cmd_pins_run(args: argparse.Namespace) -> int:
    period = parse_period(args.period)
    cfg = load_config_toml('config.toml')
    selectors = load_selectors('config/selectors.json')

    evidence_dir = cfg.get('evidence_dir', 'evidence')
    html_dump_dir = cfg.get('html_dump_dir', os.path.join(evidence_dir, 'html'))
    exports_dir = cfg.get('exports_dir', 'exports')
    reports_dir = cfg.get('reports_dir', 'reports')
    ensure_dirs([evidence_dir, html_dump_dir, exports_dir, reports_dir, 'data'])

    catalog = read_catalog('data/cba_catalog.csv')
    pins_map = read_pins('data/sku_pins.csv')
    missing = [row['item_id'] for row in catalog if not (pins_map.get(row['item_id']) or {}).get('url')]
    if missing:
        print(f"[FATAL] Faltan URLs en data/sku_pins.csv para: {', '.join(missing)}")
        return 1

    log_path = os.path.join(evidence_dir, f'run_{period}.jsonl')
    json_log(log_path, 'start_pins', {'period': period, 'mode': 'pins_only'})

    # Start Playwright minimal
    from playwright.sync_api import sync_playwright
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=(not args.debug))
    context = browser.new_context()
    page = context.new_page()

    from .site.product import extract_product_page
    from .normalize.units import parse_title_size
    results: List[Dict[str, Any]] = []
    for row in catalog:
        pin = pins_map.get(row['item_id'])
        url = pin.get('url') if pin else ''
        try:
            res = extract_product_page(
                page,
                url=url,
                selectors=selectors,
                evidence_dir=evidence_dir,
                html_dump_dir=html_dump_dir,
                save_basename=f"pinned_{row['item_id']}"
            )
            qb, un = parse_title_size(res.get('title') or '')
            res.update({
                'item_id': row['item_id'],
                'name': row['name'],
                'query': 'PINNED',
                'qty_base': qb,
                'unit': un,
                'expected_qty': row['expected_qty'],
                'monthly_qty_base': row['monthly_qty_base'],
                'substitution': ''
            })
            results.append(res)
        except Exception as e:
            json_log(log_path, 'pinned_error', {'item_id': row['item_id'], 'error': str(e)})

    # Close
    try:
        if not args.debug:
            context.close()
            browser.close()
    except Exception:
        pass

    # Pricing and exports
    priced_rows = compute_item_costs(results)
    family_ae = float(cfg.get('family_ae', 3.09))
    cba_ae, cba_family = compute_cba_values(priced_rows, family_ae)
    series_path = os.path.join(exports_dir, 'series_cba.csv')
    series_row = update_series(series_path, period, cba_ae, cba_family)
    breakdown_path = os.path.join(exports_dir, f'breakdown_{period}.csv')
    for r in priced_rows:
        r['period'] = period
    write_breakdown(breakdown_path, period, priced_rows)
    run_date = (datetime.now(ZoneInfo("America/Argentina/Ushuaia")) if ZoneInfo else datetime.utcnow()).date().isoformat()
    daily_path = os.path.join(exports_dir, f'daily_prices_{run_date}.csv')
    write_daily_prices(daily_path, run_date, period, priced_rows)
    report_path = os.path.join(reports_dir, f'{period}.html')
    render_report(report_path, period, series_path, breakdown_path)

    # Summary
    valid_prices = [r for r in priced_rows if isinstance(r.get('price_final'), (int, float)) and r['price_final'] > 0]
    ratio = len(valid_prices) / max(1, len(priced_rows))
    print("=== Resumen PINs IPC Ushuaia ===")
    print(f"Periodo: {period}")
    print(f"CBA AE: ${cba_ae:,.2f}")
    print(f"CBA Familia (x{family_ae}): ${cba_family:,.2f}")
    print(f"Series: {series_path}")
    print(f"Desglose: {breakdown_path}")
    print(f"Precios diarios: {daily_path}")
    print(f"Reporte: {report_path}")
    print(f"% ítems con precio válido: {ratio*100:.1f}%")
    return 0 if len(valid_prices) > 0 else 1
def cmd_dry_run(args: argparse.Namespace) -> int:
    period = parse_period(args.period)
    cfg = load_config_toml('config.toml')
    selectors = load_selectors('config/selectors.json')
    ensure_catalog('data/cba_catalog.csv')
    catalog = read_catalog('data/cba_catalog.csv')
    exclude_keywords = [s.strip() for s in cfg.get('exclude_keywords', '').split(',') if s.strip()]

    # Minimal HTML parser dry-run: regex scan for product-like blocks
    html_path = args.html
    if not html_path or not os.path.exists(html_path):
        print("[FATAL] Debe proveer --html con un archivo existente para dry-run")
        return 1
    with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()

    # Build simplistic card tuples by regex
    card_pat = re.compile(r"(<article[\s\S]*?</article>|<li[\s\S]*?</li>|<div[\s\S]*?</div>)", re.I)
    price_pat = re.compile(r"\$\s*([\d\.]+,\d{2})")
    title_pat = re.compile(r"title=\"([^\"]+)\"|<h3[^>]*>([^<]+)</h3>|<span[^>]*class=\"[^\"]*(?:title|name)[^\"]*\"[^>]*>([^<]+)</span>", re.I)

    cards: List[Dict[str, Any]] = []
    for m in card_pat.finditer(html):
        block = m.group(0)
        pm = price_pat.search(block)
        tm = title_pat.search(block)
        price_str = pm.group(0) if pm else ''
        title = next((g for g in (tm.group(1) if tm else None, tm.group(2) if tm else None, tm.group(3) if tm else None) if g), '') if tm else ''
        if price_str or title:
            cards.append({'title': title.strip(), 'price_text': price_str, 'in_stock': True, 'promo_flag': False, 'url': ''})

    from .site.extract import parse_price_ar
    from .normalize.units import parse_title_size
    results = []
    for row in catalog:
        query = f"{row['name']}"
        # score quickly
        scored = []
        for card in cards:
            title = card['title']
            price = parse_price_ar(card['price_text']) if card['price_text'] else None
            qty_base, unit = parse_title_size(title)
            unit_price = price / qty_base if price and qty_base else None
            score = 0
            for kw in row['preferred_keywords']:
                if kw and re.search(re.escape(kw), title, re.I):
                    score += 2
            for ex in exclude_keywords:
                if ex and re.search(re.escape(ex), title, re.I):
                    score -= 2
            # size proximity
            try:
                exp_qty = float(row['expected_qty'])
            except Exception:
                exp_qty = 0.0
            tol = 0.85
            try:
                tol = float(row.get('size_tolerance', tol))
            except Exception:
                pass
            if qty_base and exp_qty:
                ratio = min(qty_base, exp_qty) / max(qty_base, exp_qty)
                if ratio >= tol:
                    score += 2
            # tiebreaker
            scored.append((score, unit_price if unit_price else 1e12, {
                'item_id': row['item_id'], 'name': row['name'], 'query': query,
                'title': title, 'url': card['url'], 'in_stock': card['in_stock'], 'promo_flag': card['promo_flag'],
                'price_final': price, 'qty_base': qty_base, 'unit': unit,
                'expected_qty': row['expected_qty'], 'monthly_qty_base': row['monthly_qty_base'],
                'substitution': ''
            }))
        chosen = None
        if scored:
            scored.sort(key=lambda t: (-t[0], t[1]))
            chosen = scored[0][2]
        if chosen:
            results.append(chosen)

    priced_rows = compute_item_costs(results)
    family_ae = 3.09
    cba_ae, cba_family = compute_cba_values(priced_rows, family_ae)

    exports_dir = 'exports'
    reports_dir = 'reports'
    ensure_dirs([exports_dir, reports_dir, 'data'])
    series_path = os.path.join(exports_dir, 'series_cba.csv')
    series_row = update_series(series_path, period, cba_ae, cba_family)
    breakdown_path = os.path.join(exports_dir, f'breakdown_{period}.csv')
    for r in priced_rows:
        r['period'] = period
    write_breakdown(breakdown_path, period, priced_rows)
    report_path = os.path.join(reports_dir, f'{period}.html')
    render_report(report_path, period, series_path, breakdown_path)

    print("=== DRY-RUN OK ===")
    print(f"CBA AE: ${cba_ae:,.2f}")
    print(f"Serie: {series_path}")
    print(f"Reporte: {report_path}")
    # Daily CSV also in dry-run
    run_date = (datetime.now(ZoneInfo("America/Argentina/Ushuaia")) if ZoneInfo else datetime.utcnow()).date().isoformat()
    daily_path = os.path.join(exports_dir, f'daily_prices_{run_date}.csv')
    write_daily_prices(daily_path, run_date, period, priced_rows)
    print(f"Precios diarios: {daily_path}")
    return 0


def main():
    parser = argparse.ArgumentParser(description='IPC Ushuaia CLI')
    sub = parser.add_subparsers(dest='cmd')

    p_run = sub.add_parser('run', help='Ejecución E2E con Playwright')
    p_run.add_argument('--period', type=str, required=False, help='YYYY-MM')
    p_run.add_argument('--branch', type=str, required=False, help='Nombre de sucursal (ej. USHUAIA 5)')
    p_run.add_argument('--debug', action='store_true', help='No headless, no cierre automÃ¡tico')
    p_run.add_argument('--skip-branch-verify', action='store_true', help='No abortar si no se verifica Ushuaia en header')
    p_run.set_defaults(func=cmd_run)

    p_dr = sub.add_parser('dry-run', help='Prueba de parsing con HTML guardado')
    p_dr.add_argument('--period', type=str, required=False, help='YYYY-MM')
    p_dr.add_argument('--html', type=str, required=True, help='Ruta a HTML de resultados')
    p_dr.set_defaults(func=cmd_dry_run)

    p_v = sub.add_parser('verify', help='Verifica salidas y evidencias del período')
    p_v.add_argument('--period', type=str, required=False, help='YYYY-MM')
    p_v.add_argument('--min-ratio', type=float, required=False, help='Mínimo % de precios válidos (0-1)')
    p_v.add_argument('--allow-missing-branch', action='store_true', help='No falla si no se verificó sucursal en header')
    p_v.set_defaults(func=cmd_verify)

    p_pins = sub.add_parser('pins-run', help='Ejecuta extracción usando data/sku_pins.csv (sin sucursal)')
    p_pins.add_argument('--period', type=str, required=False, help='YYYY-MM')
    p_pins.add_argument('--debug', action='store_true', help='No headless, deja navegador abierto')
    p_pins.set_defaults(func=cmd_pins_run)

    args = parser.parse_args()
    if not getattr(args, 'func', None):
        parser.print_help()
        sys.exit(2)
    rc = args.func(args)
    sys.exit(rc)


if __name__ == '__main__':
    main()








