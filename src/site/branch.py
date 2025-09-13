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
    for spec in specs or []:
        loc = _first_locator(page, spec)
        try:
            if loc:
                loc.first.wait_for(state='attached', timeout=2000)
                return loc.first
        except Exception:
            continue
    return _first_locator(page, (specs or [None])[0]) if specs else None


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


def _verify_header_ushuaia(page, selectors: Dict[str, Any]) -> bool:
    try:
        # explicit nodes
        for node in selectors.get('verify_nodes', []):
            try:
                loc = _first_locator(page, node)
                if loc and loc.count() > 0:
                    txt = loc.first.inner_text()
                    if re.search(r'Ushuaia', txt, re.I):
                        return True
            except Exception:
                continue
        # fallback location button
        loc_btn = _try_first(page, selectors.get('location_button', []))
        if loc_btn:
            txt = loc_btn.inner_text()
            if re.search(r'Ushuaia', txt, re.I):
                return True
        # fallback: any mention
        try:
            if page.get_by_text(re.compile(r'Ushuaia', re.I)).first.is_visible():
                return True
        except Exception:
            pass
        # last resort: search in full page text
        try:
            present = page.evaluate("() => document.documentElement && document.documentElement.innerText && document.documentElement.innerText.toLowerCase().includes('ushuaia')")
            if present:
                return True
        except Exception:
            pass
        return False
    except Exception:
        return False


def ensure_branch(base_url: str, postal_code: str, branch_name: str, selectors: Dict[str, Any], evidence_dir: str, html_dump_dir: str, log_path: str, headless: bool = True, strict_verify: bool = True):
    from .utils import json_log

    p = sync_playwright().start()
    browser = p.chromium.launch(headless=headless)
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
    if _verify_header_ushuaia(page, selectors):
        _save_evidence(page, os.path.join(evidence_dir, 'header_after_branch_cached.png'), os.path.join(html_dump_dir, 'header_after_branch_cached.html'))
        return page

    # Cookie/banner accept (best effort)
    try:
        cab = selectors.get('cookie_accept_button', [])
        btnc = _try_first(page, cab)
        if btnc:
            btnc.click()
            page.wait_for_timeout(300)
    except Exception:
        pass

    loc_specs = selectors.get('location_button', [])
    postal_specs = selectors.get('postal_input', [])
    branch_specs = selectors.get('branch_option', [])
    confirm_specs = selectors.get('confirm_button', [])

    header_ok = False
    for attempt in range(3):
        try:
            btn = _try_first(page, loc_specs)
            if not btn:
                json_log(log_path, 'branch_warning', {'message': 'No se encontró botón de ubicación; se continúa'})
                _save_evidence(page, os.path.join(evidence_dir, 'no_location_button.png'), os.path.join(html_dump_dir, 'no_location_button.html'))
                break
            try:
                btn.click()
            except PWTimeoutError:
                btn.click(force=True)

            # If callout is visible (suggests other location), click 'Cambiar'
            try:
                chg = _try_first(page, selectors.get('change_location_link', []))
                if chg and chg.is_visible():
                    chg.click()
                    page.wait_for_timeout(400)
            except Exception:
                pass

            pin = _try_first(page, postal_specs)
            if not pin:
                raise RuntimeError('No se encontró input de código postal.')
            pin.fill('')
            pin.type(postal_code)

            _save_evidence(page, os.path.join(evidence_dir, f'modal_cp_{attempt}.png'), os.path.join(html_dump_dir, f'modal_cp_{attempt}.html'))

            page.wait_for_timeout(800)
            opt = _try_first(page, branch_specs) or page.get_by_text(re.compile(branch_name, re.I))
            opt.first.wait_for(state='visible', timeout=5000)
            opt.first.click()

            try:
                cbtn = _try_first(page, confirm_specs)
                if cbtn and cbtn.is_enabled():
                    cbtn.click()
            except Exception:
                pass

            page.wait_for_timeout(1500)
            # force reload to ensure header reflects selection
            try:
                page.reload(wait_until='domcontentloaded')
                page.wait_for_timeout(800)
            except Exception:
                pass
            header_ok = _verify_header_ushuaia(page, selectors)
            _save_evidence(page, os.path.join(evidence_dir, f'header_after_branch_{attempt}.png'), os.path.join(html_dump_dir, f'header_after_branch_{attempt}.html'))
            if header_ok:
                break
        except Exception:
            page.wait_for_timeout(1000 * (attempt + 1))
            page.goto(base_url, wait_until='domcontentloaded')

    if not header_ok:
        json_log(log_path, 'branch_verify_fail', {'expected': 'Ushuaia'})
        if strict_verify:
            raise RuntimeError('No se verificó la sucursal en header (no aparece "Ushuaia").')
        else:
            json_log(log_path, 'branch_warning', {'message': 'Sucursal no verificada, se continúa de todos modos'})

    try:
        context.storage_state(path=storage_state_path)
    except Exception:
        pass
    json_log(log_path, 'branch_ok', {'branch': branch_name, 'postal_code': postal_code})
    return page
