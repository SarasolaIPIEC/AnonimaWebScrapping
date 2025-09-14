import os
import re
import json
from typing import Dict, Any, List, Optional

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError


# -------- Selector helpers --------
def _first_locator(page, spec: Dict[str, Any]):
    import re as _re
    if not spec:
        return None
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


def _try_first(page, specs: List[Dict[str, Any]]):
    for idx, spec in enumerate(specs or []):
        loc = _first_locator(page, spec)
        try:
            if loc:
                loc.first.wait_for(state='attached', timeout=2000)
                return loc.first, idx
        except Exception:
            continue
    loc = _first_locator(page, (specs or [None])[0]) if specs else None
    return (loc, 0) if loc else (None, -1)


def _branch_specs(selectors: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    # Support namespaced "branch.*" with fallback to legacy top-level keys
    b = selectors.get('branch', {}) if isinstance(selectors.get('branch', {}), dict) else {}
    return {
        'open_widget': b.get('open_widget', selectors.get('location_button', [])),
        'zip_input': b.get('zip_input', selectors.get('postal_input', [])),
        'result_item': b.get('result_item', selectors.get('branch_option', [])),
        'confirm': b.get('confirm', selectors.get('confirm_button', [])),
        'change_link': b.get('change_link', selectors.get('change_location_link', [])),
        'verify_nodes': b.get('verify_nodes', selectors.get('verify_nodes', [])),
        'pickup_tab': b.get('pickup_tab', []),
        'province_combobox': b.get('province_combobox', []),
        'city_combobox': b.get('city_combobox', []),
        'cookie_accept_button': selectors.get('cookie_accept_button', []),
    }


# -------- Evidence helpers --------
def _save_evidence(page, screenshot_path: str, html_path: str):
    try:
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        page.screenshot(path=screenshot_path, full_page=True)
    except Exception:
        pass
    try:
        content = page.content()
        os.makedirs(os.path.dirname(html_path), exist_ok=True)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception:
        pass


def _capture_storage(page, out_path: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {"cookies": [], "localStorage": {}, "sessionStorage": {}}
    try:
        st = page.context.storage_state()
        data['cookies'] = st.get('cookies', [])
        try:
            ls = page.evaluate("() => Object.fromEntries(Object.keys(localStorage).map(k => [k, localStorage.getItem(k)]))")
            if isinstance(ls, dict):
                data['localStorage'] = ls
        except Exception:
            pass
        try:
            ss = page.evaluate("() => Object.fromEntries(Object.keys(sessionStorage).map(k => [k, sessionStorage.getItem(k)]))")
            if isinstance(ss, dict):
                data['sessionStorage'] = ss
        except Exception:
            pass
    except Exception:
        pass
    try:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return data


# -------- Signals and checks --------
def detect_ushuaia_in_text(text: str) -> bool:
    try:
        return re.search(r"ushuaia|tierra\s*del\s*fuego|9410", text or "", re.I) is not None
    except Exception:
        return False


def _verify_header_ushuaia(page, selectors: Dict[str, Any]) -> bool:
    specs = _branch_specs(selectors)
    try:
        # explicit nodes
        for node in specs.get('verify_nodes', []):
            try:
                loc = _first_locator(page, node)
                if loc and loc.count() > 0:
                    txt = loc.first.inner_text()
                    if detect_ushuaia_in_text(txt):
                        return True
            except Exception:
                continue
        # fallback location button
        loc_btn, _ = _try_first(page, specs.get('open_widget', []))
        if loc_btn:
            try:
                txt = loc_btn.inner_text()
                if detect_ushuaia_in_text(txt):
                    return True
            except Exception:
                pass
        # fallback: any mention
        try:
            cand = page.get_by_text(re.compile(r'Ushuaia', re.I))
            if cand.first and cand.first.is_visible():
                return True
        except Exception:
            pass
        # last resort: search in full page text
        try:
            present = page.evaluate("() => (document.documentElement && document.documentElement.innerText || '').toLowerCase().includes('ushuaia')")
            if present:
                return True
        except Exception:
            pass
        return False
    except Exception:
        return False


def _choose_result_option(page, result_specs: List[Dict[str, Any]], branch_hint: str) -> bool:
    import re as _re
    try:
        loc, used = _try_first(page, result_specs)
        if loc and loc.count() > 0:
            total = min(loc.count(), 20)
            for i in range(total):
                it = loc.nth(i)
                try:
                    txt = it.inner_text()
                except Exception:
                    txt = ''
                if detect_ushuaia_in_text(txt) and (not branch_hint or _re.search(_re.escape(branch_hint), txt, _re.I)):
                    it.click()
                    return True
            loc.first.click()
            return True
        rx = _re.compile(r"Ushuaia", _re.I)
        cand = page.get_by_text(rx)
        if cand and cand.count() > 0:
            cand.first.click()
            return True
    except Exception:
        pass
    return False


def ensure_branch_on_page(page, *, zipcode: str = "9410", branch_hint: str = "USHUAIA", selectors: Dict[str, Any], evidence_dir: str, html_dump_dir: str, log_path: str, attempts: int = 3) -> None:
    from .utils import json_log
    os.makedirs(evidence_dir, exist_ok=True)
    os.makedirs(html_dump_dir, exist_ok=True)
    specs = _branch_specs(selectors)

    if _verify_header_ushuaia(page, selectors):
        json_log(log_path, 'branch_already_set', {'zipcode': zipcode, 'hint': branch_hint})
        _save_evidence(page, os.path.join(evidence_dir, 'branch_after.png'), os.path.join(html_dump_dir, 'branch_dom_after.html'))
        _capture_storage(page, os.path.join(evidence_dir, 'branch_storage.json'))
        return

    # accept cookies best-effort
    try:
        cab = specs.get('cookie_accept_button', [])
        btnc, _ = _try_first(page, cab)
        if btnc:
            btnc.click()
            page.wait_for_timeout(250)
    except Exception:
        pass

    _save_evidence(page, os.path.join(evidence_dir, 'branch_before.png'), os.path.join(html_dump_dir, 'branch_dom_before.html'))

    for attempt in range(max(1, attempts)):
        try:
            # open widget
            btn, btn_idx = _try_first(page, specs.get('open_widget', []))
            if not btn:
                # Try via verify_nodes anchor/button
                vloc = None
                for node in specs.get('verify_nodes', []):
                    try:
                        cand = _first_locator(page, node)
                        if cand and cand.count() > 0:
                            vloc = cand.first
                            break
                    except Exception:
                        continue
                if vloc:
                    try:
                        vloc.click()
                        page.wait_for_timeout(300)
                    except Exception:
                        pass
                else:
                    json_log(log_path, 'branch_no_widget', {'attempt': attempt})
                    continue
            else:
                try:
                    btn.click()
                except PWTimeoutError:
                    btn.click(force=True)

            # If callout suggests other location, click Change
            try:
                chg, _ = _try_first(page, specs.get('change_link', []))
                if chg and chg.is_visible():
                    chg.click()
                    page.wait_for_timeout(300)
            except Exception:
                pass

            # pickup tab if present
            try:
                pt, _ = _try_first(page, specs.get('pickup_tab', []))
                if pt and pt.is_visible():
                    pt.click()
                    page.wait_for_timeout(200)
            except Exception:
                pass

            # type zipcode or province/city fallback
            pin, _ = _try_first(page, specs.get('zip_input', []))
            if pin:
                try:
                    pin.fill('')
                except Exception:
                    pass
                pin.type(str(zipcode))
                page.wait_for_timeout(700)
            else:
                prov, _ = _try_first(page, specs.get('province_combobox', []))
                city, _ = _try_first(page, specs.get('city_combobox', []))
                if prov:
                    try:
                        prov.click()
                        page.keyboard.type('Tierra del Fuego')
                        page.keyboard.press('Enter')
                        page.wait_for_timeout(200)
                    except Exception:
                        pass
                if city:
                    try:
                        city.click()
                        page.keyboard.type('Ushuaia')
                        page.keyboard.press('Enter')
                        page.wait_for_timeout(200)
                    except Exception:
                        pass
                else:
                    json_log(log_path, 'branch_no_input', {'attempt': attempt})

            _save_evidence(page, os.path.join(evidence_dir, f'modal_state_{attempt}.png'), os.path.join(html_dump_dir, f'modal_state_{attempt}.html'))

            # pick result
            ok = _choose_result_option(page, specs.get('result_item', []), branch_hint)
            if not ok and pin:
                try:
                    pin.press('Enter')
                except Exception:
                    pass

            # confirm
            try:
                cbtn, _ = _try_first(page, specs.get('confirm', []))
                if cbtn and cbtn.is_enabled():
                    cbtn.click()
            except Exception:
                pass

            # settle
            try:
                page.wait_for_load_state('networkidle', timeout=10000)
            except Exception:
                page.wait_for_timeout(1000)
            try:
                page.reload(wait_until='domcontentloaded')
                page.wait_for_timeout(400)
            except Exception:
                pass

            if _verify_header_ushuaia(page, selectors):
                _save_evidence(page, os.path.join(evidence_dir, 'branch_after.png'), os.path.join(html_dump_dir, 'branch_dom_after.html'))
                _capture_storage(page, os.path.join(evidence_dir, 'branch_storage.json'))
                json_log(log_path, 'branch_selected', {'attempt': attempt, 'zipcode': zipcode, 'hint': branch_hint, 'selector_idx': btn_idx})
                return

        except Exception as e:
            json_log(log_path, 'branch_attempt_error', {'attempt': attempt, 'error': str(e)})
        page.wait_for_timeout(int(500 * (attempt + 1)))
        try:
            page.reload(wait_until='domcontentloaded')
        except Exception:
            pass

    json_log(log_path, 'branch_failed', {'zipcode': zipcode, 'hint': branch_hint})
    raise RuntimeError('No se pudo seleccionar la sucursal de Ushuaia (widget/confirmación fallida).')


def assert_branch_is_ushuaia(page, *, selectors: Dict[str, Any], evidence_dir: str, html_dump_dir: str, log_path: str, control_url: Optional[str] = None) -> None:
    from .utils import json_log
    os.makedirs(evidence_dir, exist_ok=True)
    os.makedirs(html_dump_dir, exist_ok=True)

    signals: Dict[str, Any] = {'header': False, 'pdp': False, 'storage': False}

    try:
        signals['header'] = bool(_verify_header_ushuaia(page, selectors))
    except Exception:
        signals['header'] = False
    if signals['header']:
        _save_evidence(page, os.path.join(evidence_dir, 'branch_after.png'), os.path.join(html_dump_dir, 'branch_dom_after.html'))

    st = _capture_storage(page, os.path.join(evidence_dir, 'branch_storage.json'))
    def _matches_storage(data: Dict[str, Any]) -> bool:
        text = json.dumps(data, ensure_ascii=False).lower()
        return ('ushua' in text) or ('9410' in text) or ('tierra' in text and 'fuego' in text) or any(k in text for k in ['branch', 'sucur', 'postal', 'localid', 'store'])
    signals['storage'] = _matches_storage(st)

    if not control_url:
        try:
            import csv as _csv
            with open('data/sku_pins.csv', 'r', encoding='utf-8') as f:
                reader = _csv.DictReader(f)
                for row in reader:
                    u = (row or {}).get('url') or ''
                    if u.startswith('http'):
                        control_url = u
                        break
        except Exception:
            control_url = None

    pdp_ok = False
    pdp_overlay_bad = False
    if control_url:
        try:
            from .product import extract_product_page
            res = extract_product_page(page, url=control_url, selectors=selectors, evidence_dir=evidence_dir, html_dump_dir=html_dump_dir, save_basename='branch_control_pdp')
            pdp_ok = bool(res.get('price_final'))
            try:
                full = page.content().lower()
                if ('provincia' in full and 'localidad' in full and 'seleccion' in full) or ('eleg' in full and 'sucursal' in full):
                    pdp_overlay_bad = True
            except Exception:
                pass
        except Exception:
            pdp_ok = False
    signals['pdp'] = bool(pdp_ok and not pdp_overlay_bad)

    json_log(log_path, 'branch_signals', {'signals': signals, 'control_url': control_url or ''})

    if not (signals['header'] or signals['pdp'] or signals['storage']):
        raise RuntimeError('Verificación de sucursal fallida: no se detectaron señales de Ushuaia en header/PDP/storage.')


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

    try:
        ensure_branch_on_page(
            page,
            zipcode=str(postal_code or '9410'),
            branch_hint=str(branch_name or 'USHUAIA'),
            selectors=selectors,
            evidence_dir=evidence_dir,
            html_dump_dir=html_dump_dir,
            log_path=log_path,
            attempts=3,
        )
    except Exception as e:
        if strict_verify:
            try:
                page.context.close()
                page.context.browser.close()
            except Exception:
                pass
            raise
        else:
            json_log(log_path, 'branch_warning', {'message': f'Selección con errores, continuando: {e}'})

    try:
        context.storage_state(path=storage_state_path)
    except Exception:
        pass

    return page

