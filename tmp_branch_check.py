import json
from pathlib import Path
from datetime import datetime

try:
    import tomllib
except ImportError:  # pragma: no cover
    import toml as tomllib  # type: ignore

from src.site.branch import ensure_branch

cfg_path = Path('config.toml')
with cfg_path.open('rb') as fh:
    cfg = tomllib.load(fh)

selectors_path = Path('config/selectors.json')
with selectors_path.open('r', encoding='utf-8') as fh:
    selectors = json.load(fh)

base_url = 'https://www.laanonima.com.ar/supermercado/'
postal_code = cfg.get('postal_code', '9410')
branch_name = cfg.get('branch_name', 'USHUAIA 5')
paths_cfg = cfg.get('paths', {})

run_id = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
base_evd = Path(paths_cfg.get('evidence_dir', 'evidence')) / f'_branch_check_{run_id}'
html_dump_dir = base_evd / 'html'
base_evd.mkdir(parents=True, exist_ok=True)
html_dump_dir.mkdir(parents=True, exist_ok=True)
log_path = base_evd / 'branch_check.jsonl'

page = None
try:
    page = ensure_branch(
        base_url=base_url,
        postal_code=postal_code,
        branch_name=branch_name,
        selectors=selectors,
        evidence_dir=str(base_evd),
        html_dump_dir=str(html_dump_dir),
        log_path=str(log_path),
        headless=True,
        strict_verify=True,
        force_refresh=True,
    )

    header_text = page.evaluate("() => (document.querySelector('a.seleccionar-sucursal .sucursal') || document.querySelector('.cabezal2 .sucursal.cortar-texto-1') || {}).innerText || ''")
    storage = page.context.storage_state()
    cookies = {c['name']: c['value'] for c in storage.get('cookies', []) if c['name'] in {'codigoPostal', 'Id-Sucursal-Super', 'descripcionLocalidadCabezal'}}

    print('=== Branch Check ===')
    print(f'Base URL: {base_url}')
    print(f'Postal code input: {postal_code}')
    print(f'Branch requested: {branch_name}')
    print(f'Header text: {header_text.strip() or "<empty>"}')
    if cookies:
        for k, v in cookies.items():
            print(f'Cookie {k}: {v}')
    else:
        print('Cookie snapshot: <no matching cookies>')
    print(f'Evidence dir: {base_evd}')
    if log_path.exists():
        with log_path.open('r', encoding='utf-8') as fh:
            events = [json.loads(line) for line in fh if line.strip()]
        branch_events = [e for e in events if e.get('event') in {'branch_option_selected', 'branch_ok'}]
        for ev in branch_events:
            print(f"Event {ev.get('event')}: {json.dumps(ev, ensure_ascii=False)}")
    else:
        print('No log file produced')
finally:
    if page is not None:
        try:
            context = getattr(page, '_branch_context', None) or page.context
            if context:
                context.close()
        except Exception:
            pass
        try:
            browser = getattr(page, '_branch_browser', None)
            if browser:
                browser.close()
        except Exception:
            pass
        try:
            play = getattr(page, '_branch_playwright', None)
            if play:
                play.stop()
        except Exception:
            pass
