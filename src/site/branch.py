import os
import re
from typing import Dict, Any

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError


def _first_locator(page, spec: Dict[str, Any]):
    import re as _re
    if 'role' in spec:
        name = spec.get('name', '')
        rx = _re.compile(name) if name else None
        return page.get_by_role(spec['role'], name=rx)
    if 'placeholder' in spec:
        rx = _re.compile(spec['placeholder'])
        return page.get_by_placeholder(rx)
    if 'text' in spec:
        rx = _re.compile(spec['text'])
        return page.get_by_text(rx)
    if 'css' in spec:
        return page.locator(spec['css'])
    return None


def _try_first(page, specs):
    for spec in specs:
        loc = _first_locator(page, spec)
        try:
            if loc:
                loc.first.wait_for(state='attached', timeout=2000)
                return loc.first
        except Exception:
            continue
    # return first anyway (may wait later)
    return _first_locator(page, specs[0]) if specs else None


def _save_evidence(page, screenshot_path: str, html_path: str):
    try:
        page.screenshot(path=screenshot_path, full_page=True)
    except Exception:
        pass
    try:
        content = page.content()
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception:
        pass


def ensure_branch(base_url: str, postal_code: str, branch_name: str, selectors: Dict[str, Any], evidence_dir: str, html_dump_dir: str, log_path: str, headless: bool = True, strict_verify: bool = True):
    from datetime import datetime
    from .utils import json_log

    p = sync_playwright().start()
    browser = p.chromium.launch(headless=headless)
    # Persist storage state globally under data/ to reuse branch selection
    os.makedirs('data', exist_ok=True)
    storage_state_path = os.path.join('data', 'storage_state.json')
    if os.path.exists(storage_state_path):
        context = browser.new_context(storage_state=storage_state_path)
    else:
        context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(10000)

    page.goto(base_url, wait_until='domcontentloaded')
    json_log(log_path, 'nav', {'url': base_url})

    # If already set (from storage), validate header and return early
    try:
        if page.get_by_text(re.compile(r'Ushuaia', re.I)).first.is_visible():
            _save_evidence(page, os.path.join(evidence_dir, 'header_after_branch_cached.png'), os.path.join(html_dump_dir, 'header_after_branch_cached.html'))
            return page
    except Exception:
        pass

    # Cookie/banner accept (best effort)
    try:
        cab = selectors.get('cookie_accept_button', [])
        btnc = _try_first(page, cab)
        if btnc:
            btnc.click()
            page.wait_for_timeout(300)
    except Exception:
        pass

    # Click location button
    loc_specs = selectors.get('location_button', [])
    postal_specs = selectors.get('postal_input', [])
    branch_specs = selectors.get('branch_option', [])
    confirm_specs = selectors.get('confirm_button', [])

    # Allow a couple retries for the branch flow
    header_ok = False
    for attempt in range(3):
        try:
    btn = _try_first(page, loc_specs)
    if not btn:
        # No location button found; proceed with warning if not strict
        json_log(log_path, 'branch_warning', {'message': 'No se encontró botón de ubicación; se continúa'})
        _save_evidence(page, os.path.join(evidence_dir, 'no_location_button.png'), os.path.join(html_dump_dir, 'no_location_button.html'))
        return page
            try:
                btn.click()
            except PWTimeoutError:
                btn.click(force=True)

            # Wait for postal input
            pin = _try_first(page, postal_specs)
            if not pin:
                raise RuntimeError('No se encontró input de código postal.')
            pin.fill('')
            pin.type(postal_code)

            # Evidence modal
            _save_evidence(page, os.path.join(evidence_dir, f'modal_cp_{attempt}.png'), os.path.join(html_dump_dir, f'modal_cp_{attempt}.html'))

            # Click branch option
            page.wait_for_timeout(800)
            opt = _try_first(page, branch_specs)
            if not opt:
                # try generic text search
                opt = page.get_by_text(re.compile(branch_name, re.I))
            opt.first.wait_for(state='visible', timeout=5000)
            opt.first.click()

            # Confirm if button exists
            try:
                cbtn = _try_first(page, confirm_specs)
                if cbtn and cbtn.is_enabled():
                    cbtn.click()
            except Exception:
                pass

            # Verify header shows Ushuaia (try to target the location button)
            page.wait_for_timeout(1500)
            loc_btn = _try_first(page, selectors.get('location_button', []))
            if loc_btn:
                header_ok = re.search(r'Ushuaia', loc_btn.inner_text(), re.I) is not None
            else:
                header_ok = page.get_by_text(re.compile(r'Ushuaia', re.I)).first.is_visible()

            _save_evidence(page, os.path.join(evidence_dir, f'header_after_branch_{attempt}.png'), os.path.join(html_dump_dir, f'header_after_branch_{attempt}.html'))
            if header_ok:
                break
        except Exception:
            page.wait_for_timeout(1000 * (attempt + 1))
            page.goto(base_url, wait_until='domcontentloaded')

    if not header_ok:
        json_log(log_path, 'branch_verify_fail', {'expected': 'Ushuaia'})
        if strict_verify:
            raise RuntimeError('No se validó la sucursal en header (no aparece "Ushuaia").')
        else:
            # proceed but warn
            json_log(log_path, 'branch_warning', {'message': 'Sucursal no verificada, se continúa de todos modos'})

    # Persist storage state for future runs
    try:
        context.storage_state(path=storage_state_path)
    except Exception:
        pass
    json_log(log_path, 'branch_ok', {'branch': branch_name, 'postal_code': postal_code})
    return page
