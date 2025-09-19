import os
import re
import time
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Locator,
    Page,
    TimeoutError as PWTimeoutError,
    sync_playwright,
)

from .utils import json_log

# ---------------------------------------------------------------------------
# Defaults & helpers
# ---------------------------------------------------------------------------

DEFAULT_USER_DATA_DIR = ".pw_profiles/anonima"
DEFAULT_STORAGE_STATE = Path("data/storage_state.json")
DEFAULT_HEADER_ASSERT = "Ushuaia"
DEFAULT_BROWSER_CHANNEL = (
    os.environ.get("PLAYWRIGHT_BROWSER_CHANNEL")
    or os.environ.get("PLAYWRIGHT_CHROME_CHANNEL")
    or ''
)
DEFAULT_EVIDENCE_PREFIX = "branch"


def _compile(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.I)


def _locator_from_spec(page: Page, spec: Dict[str, Any]) -> Optional[Locator]:
    import re as _re

    if not spec:
        return None

    if "role" in spec:
        kwargs: Dict[str, Any] = {}
        if spec.get("name"):
            kwargs["name"] = _re.compile(spec["name"], re.I)
        if spec.get("exact") is not None:
            kwargs["exact"] = bool(spec["exact"])
        loc = page.get_by_role(spec["role"], **kwargs)
        if spec.get("has_text"):
            loc = loc.filter(has_text=_re.compile(spec["has_text"], re.I))
        return loc

    if "placeholder" in spec:
        return page.get_by_placeholder(_re.compile(spec["placeholder"], re.I))

    if "text" in spec:
        return page.get_by_text(_re.compile(spec["text"], re.I))

    if "css" in spec:
        return page.locator(spec["css"])

    return None





def _locate_first(page: Page, specs: Sequence[Dict[str, Any]], *, timeout: float = 4000) -> Optional[Locator]:
    for spec in specs:
        try:
            loc = _locator_from_spec(page, spec)
            if not loc:
                continue
            loc.first.wait_for(state="attached", timeout=timeout)
            return loc.first
        except Exception:
            continue
    return None


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _merge_specs(selectors: Dict[str, Any], *keys: str) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    for key in keys:
        values = selectors.get(key) or []
        for value in values:
            if value not in merged:
                merged.append(value)
    return merged


def _capture(page: Page, target_path: Path) -> None:
    try:
        page.screenshot(path=str(target_path), full_page=True)
    except Exception:
        pass


def _dump_html(page: Page, target_path: Path) -> None:
    try:
        target_path.write_text(page.content(), encoding="utf-8")
    except Exception:
        pass


def _normalize_tokens(value: str) -> List[str]:
    raw = value or ""
    base = raw.strip()
    tokens = {base, base.upper(), base.lower()}
    parts = [p.strip() for p in re.split(r"\s+", base) if p.strip()]
    tokens.update(parts)
    if parts:
        tokens.add(" ".join(parts[:2]))
    return [t for t in tokens if t]


def _storage_snapshot(page: Page) -> Dict[str, str]:
    try:
        data = page.evaluate(
            """
            () => {
              const out = {};
              const collect = (store, prefix) => {
                if (!store) return;
                for (let i = 0; i < store.length; i += 1) {
                  const key = store.key(i);
                  const value = store.getItem(key);
                  out[`${prefix}:${key}`] = value ?? '';
                }
              };
              collect(window.localStorage, 'local');
              collect(window.sessionStorage, 'session');
              return out;
            }
            """
        )
        return data or {}
    except Exception:
        return {}


@dataclass
class BranchConfig:
    base_url: str
    postal_code: str
    branch_name: str
    selectors: Dict[str, Any]
    evidence_dir: Path
    html_dump_dir: Path
    log_path: Path
    headless: bool = True
    strict_verify: bool = True
    header_assert: Optional[str] = None
    user_data_dir: Path = Path(DEFAULT_USER_DATA_DIR)
    storage_state_path: Path = DEFAULT_STORAGE_STATE
    browser_channel: Optional[str] = DEFAULT_BROWSER_CHANNEL or None
    evidence_prefix: str = DEFAULT_EVIDENCE_PREFIX
    force_refresh: bool = False


class BranchEnsurer:
    def __init__(self, cfg: BranchConfig):
        self.cfg = cfg
        self.play = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._storage_before: Dict[str, str] = {}
        self._assert_tokens = self._build_assert_tokens()

        if self.cfg.force_refresh:
            self._clear_profile()

        _ensure_dir(self.cfg.evidence_dir)
        _ensure_dir(self.cfg.html_dump_dir)
        _ensure_dir(self.cfg.storage_state_path.parent)
        _ensure_dir(self.cfg.user_data_dir)

    def _locate_filtered(self, specs: Sequence[Dict[str, Any]], forbidden: Sequence[str] = None) -> Optional[Locator]:
        assert self.page is not None
        patterns = [p.lower() for p in (forbidden or [])] or ['iniciar', 'mi cuenta', 'registrarse']
        for spec in specs:
            loc = _locator_from_spec(self.page, spec)
            if not loc:
                continue
            try:
                count = loc.count()
            except Exception:
                count = 0
            for idx in range(count):
                candidate = loc.nth(idx)
                try:
                    candidate.wait_for(state="attached", timeout=2000)
                except Exception:
                    continue
                try:
                    text = (candidate.inner_text() or '').strip().lower()
                except Exception:
                    text = ''
                if any(p in text for p in patterns):
                    continue
                return candidate
        return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> Page:
        start = time.perf_counter()
        try:
            self._setup_browser()
            self._navigate_home()
            if self._already_targeted(stage="initial"):
                self._log("branch_cached", {"stage": "initial"})
                self._persist_state()
                self._log_branch_ok(route="cached", stage="initial")
                return self.page  # type: ignore[return-value]

            routes = [
                ("modal", self._route_modal),
                ("header", self._route_header),
                ("menu", self._route_menu),
            ]
            for route_name, route in routes:
                if not route:
                    continue
                self._log("route_attempt", {"route": route_name})
                postal_input = route()
                if not postal_input:
                    continue
                if not self._choose_store(postal_input, route_name):
                    continue
                if self._already_targeted(stage="post-selection"):
                    self._log("branch_selected", {"route": route_name})
                    self._persist_state()
                    self._log_branch_ok(route=route_name, stage="post-selection")
                    return self.page  # type: ignore[return-value]

            self._capture_failure("branch_selection_failed")
            raise RuntimeError("Branch selection did not complete; see evidence and logs.")
        finally:
            elapsed = time.perf_counter() - start
            self._log("branch_flow_done", {"seconds": round(elapsed, 3)})

    # ------------------------------------------------------------------
    # Browser setup
    # ------------------------------------------------------------------

    def _setup_browser(self) -> None:
        self.play = sync_playwright().start()
        chromium = self.play.chromium
        channel_label = self.cfg.browser_channel or 'chromium'
        self._log("browser_launch", {"mode": 'headless' if self.cfg.headless else 'headed', "channel": channel_label, "persistent": (not self.cfg.headless)})
        if self.cfg.headless:
            self.browser = chromium.launch(headless=True)
            context_kwargs: Dict[str, Any] = {"viewport": None}
            if self.cfg.storage_state_path.exists():
                context_kwargs["storage_state"] = str(self.cfg.storage_state_path)
            self.context = self.browser.new_context(**context_kwargs)
            self._log("browser_headless_ready", {"channel": 'chromium'})
        else:
            launch_kwargs: Dict[str, Any] = {
                "headless": False,
                "args": ["--start-maximized"],
            }
            if self.cfg.browser_channel:
                launch_kwargs["channel"] = self.cfg.browser_channel
            try:
                try:
                    self.context = chromium.launch_persistent_context(
                        user_data_dir=str(self.cfg.user_data_dir),
                        viewport=None,
                        **launch_kwargs,
                    )
                except Exception as exc:
                    if launch_kwargs.pop("channel", None) is not None:
                        self._log("browser_channel_fallback", {"channel": self.cfg.browser_channel, "error": str(exc)})
                        self.context = chromium.launch_persistent_context(
                            user_data_dir=str(self.cfg.user_data_dir),
                            viewport=None,
                            **launch_kwargs,
                        )
                        channel_label = 'chromium'
                    else:
                        raise
                self._log("browser_persistent_ready", {"channel": channel_label})
                self.browser = self.context.browser if hasattr(self.context, 'browser') else None
            except Exception as exc:
                self._log("persistent_launch_failed", {"error": str(exc), "channel": channel_label})
                self.browser = chromium.launch(headless=False)
                self._log("browser_context_fallback", {"mode": 'headed', "channel": 'chromium', "reason": 'persistent_launch_failed'})
                context_kwargs: Dict[str, Any] = {"viewport": None}
                if self.cfg.storage_state_path.exists():
                    context_kwargs["storage_state"] = str(self.cfg.storage_state_path)
                self.context = self.browser.new_context(**context_kwargs)
        self.context.set_default_timeout(45000)
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        self.page.set_default_timeout(45000)

    def _navigate_home(self) -> None:
        assert self.page is not None
        self.page.goto(self.cfg.base_url, wait_until="domcontentloaded")
        try:
            self.page.wait_for_load_state("networkidle", timeout=15000)
        except PWTimeoutError as exc:
            self._log("networkidle_timeout", {"error": str(exc)})
        self._log("nav", {"url": self.cfg.base_url})
        self._storage_before = _storage_snapshot(self.page)
        self._accept_cookies()

    def _wait_results(self) -> None:
        assert self.page is not None
        specs = self.cfg.selectors.get("branch_results_container") or []
        if not specs:
            return
        try:
            _locate_first(self.page, specs, timeout=8000)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Routes & actions
    # ------------------------------------------------------------------

    def _route_modal(self) -> Optional[Locator]:
        assert self.page is not None
        specs = self.cfg.selectors.get("branch_entry_modal") or []
        if specs:
            btn = _locate_first(self.page, specs)
            if btn:
                btn.click()
                self.page.wait_for_timeout(500)
        # Generic dialog fallback
        dialogs = self.page.locator("role=dialog")
        for idx in range(min(dialogs.count(), 3)):
            dialog = dialogs.nth(idx)
            try:
                dialog.wait_for(state="visible", timeout=1500)
            except Exception:
                continue
            cta = dialog.get_by_role("button")
            for pattern in ["continuar", "aceptar", "comprar", "empezar"]:
                target = cta.filter(has_text=_compile(pattern))
                if target.count():
                    try:
                        target.first.click()
                        self.page.wait_for_timeout(500)
                        return self._await_postal_input()
                    except Exception:
                        continue
        return self._await_postal_input()

    def _route_header(self) -> Optional[Locator]:
        assert self.page is not None
        specs = _merge_specs(
            self.cfg.selectors,
            "branch_entry_header",
            "location_button",
        )
        forbidden = ['iniciar', 'mi cuenta', 'registrarse']
        btn = self._locate_filtered(specs, forbidden)
        if not btn:
            return None
        try:
            btn.click()
        except PWTimeoutError:
            btn.click(force=True)
        self.page.wait_for_timeout(300)
        return self._await_postal_input()

    def _route_menu(self) -> Optional[Locator]:
        assert self.page is not None
        trigger_specs = self.cfg.selectors.get("branch_menu_trigger") or []
        forbidden = ['iniciar', 'mi cuenta', 'registrarse']
        if trigger_specs:
            trigger = self._locate_filtered(trigger_specs, forbidden)
            if trigger:
                trigger.click()
                self.page.wait_for_timeout(300)
        else:
            try:
                ham = self.page.get_by_role("button", name=_compile("menu"))
                if ham.count():
                    ham.first.click()
                    self.page.wait_for_timeout(300)
            except Exception:
                pass
        entry_specs = self.cfg.selectors.get("branch_entry_menu") or []
        entry = self._locate_filtered(entry_specs, forbidden) if entry_specs else None
        if entry:
            entry.click()
            self.page.wait_for_timeout(300)
        return self._await_postal_input()

    def _await_postal_input(self) -> Optional[Locator]:
        assert self.page is not None
        specs = self.cfg.selectors.get("postal_input") or []
        if not specs:
            return None
        return _locate_first(self.page, specs, timeout=6000)

    def _choose_store(self, postal_input: Locator, route_name: str) -> bool:
        assert self.page is not None
        t0 = time.perf_counter()
        target = self.cfg.postal_code
        try:
            postal_input.click()
            postal_input.fill(target)
            self.page.wait_for_timeout(50)
            postal_input.press("Enter")
        except Exception as exc:
            self._log("postal_input_error", {"route": route_name, "error": str(exc)})
            return False

        self._wait_results()
        self._capture_step(f"modal_after_cp_{route_name}")

        # Optional fulfillment selection
        fulfillment_specs = self.cfg.selectors.get("branch_fulfillment_option") or []
        for spec in fulfillment_specs:
            choice = _locate_first(self.page, [spec], timeout=2000)
            if choice:
                try:
                    choice.click()
                    self.page.wait_for_timeout(250)
                    self._wait_results()
                except Exception:
                    continue

        option_specs = self.cfg.selectors.get("branch_option") or []
        option_locator = _locate_first(self.page, option_specs, timeout=8000)
        if not option_locator:
            # fallback to textual search inside modal
            try:
                option_locator = self.page.get_by_text(_compile(self.cfg.branch_name))
                option_locator.first.wait_for(state="visible", timeout=8000)
            except Exception:
                option_locator = None
        if not option_locator:
            self._log(
                "branch_option_missing",
                {"route": route_name, "pattern": self.cfg.branch_name},
            )
            return False
        try:
            option_locator.click()
        except PWTimeoutError:
            option_locator.click(force=True)
        self.page.wait_for_timeout(400)

        confirm_specs = self.cfg.selectors.get("confirm_button") or []
        confirm = _locate_first(self.page, confirm_specs, timeout=2500)
        if confirm and confirm.is_enabled():
            try:
                confirm.click()
            except PWTimeoutError:
                confirm.click(force=True)
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)

        elapsed = time.perf_counter() - t0
        self._log("branch_option_selected", {"route": route_name, "seconds": round(elapsed, 3)})
        return True

    # ------------------------------------------------------------------
    # Validation & persistence
    # ------------------------------------------------------------------

    def _already_targeted(self, stage: str) -> bool:
        assert self.page is not None
        header_text = self._header_text()
        storage_after = _storage_snapshot(self.page)
        tokens = self._assert_tokens

        header_match = any(token.lower() in (header_text or "").lower() for token in tokens)
        storage_match = any(
            token.lower() in (value or "").lower()
            for token in tokens
            for value in storage_after.values()
        )
        if header_match:
            self._log(
                "branch_validation",
                {
                    "stage": stage,
                    "header_text": header_text,
                    "storage_match": storage_match,
                    "header_match": header_match,
                },
            )
            self._capture_step(f"header_{stage}")
            return True

        if storage_match:
            if stage == "initial":
                self._log(
                    "branch_validation_cache_only",
                    {
                        "stage": stage,
                        "header_text": header_text,
                    },
                )
            else:
                self._log(
                    "branch_validation",
                    {
                        "stage": stage,
                        "header_text": header_text,
                        "storage_match": storage_match,
                        "header_match": header_match,
                    },
                )
                self._capture_step(f"header_{stage}")
                return True

        if not self.cfg.strict_verify and stage != "initial":
            self._log(
                "branch_validation_soft",
                {
                    "stage": stage,
                    "header_text": header_text,
                },
            )
            self._capture_step(f"header_{stage}_soft")
            return True

        return False

    def _header_text(self) -> Optional[str]:
        assert self.page is not None
        specs = _merge_specs(
            self.cfg.selectors,
            "branch_header_label",
            "location_button",
        )
        locator = _locate_first(self.page, specs, timeout=2000)
        if locator:
            try:
                return locator.inner_text().strip()
            except Exception:
                return None
        try:
            header = self.page.locator("header")
            header.wait_for(state="visible", timeout=2000)
            text = header.inner_text()
            return text.strip()
        except Exception:
            return None

    def _persist_state(self) -> None:
        if not self.context:
            return
        try:
            self.context.storage_state(path=str(self.cfg.storage_state_path))
        except Exception:
            pass

    def _clear_profile(self) -> None:
        try:
            if self.cfg.storage_state_path.exists():
                self.cfg.storage_state_path.unlink()
        except Exception:
            pass
        try:
            if self.cfg.user_data_dir.exists():
                shutil.rmtree(self.cfg.user_data_dir)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _accept_cookies(self) -> None:
        assert self.page is not None
        specs = self.cfg.selectors.get("cookie_accept_button") or []
        btn = _locate_first(self.page, specs, timeout=2000)
        if not btn:
            return
        try:
            btn.click()
            self.page.wait_for_timeout(300)
        except Exception:
            pass

    def _capture_step(self, label: str) -> None:
        assert self.page is not None
        base = f"{self.cfg.evidence_prefix}_{label}" if self.cfg.evidence_prefix else label
        screenshot_path = self.cfg.evidence_dir / f"{base}.png"
        html_path = self.cfg.html_dump_dir / f"{base}.html"
        _capture(self.page, screenshot_path)
        _dump_html(self.page, html_path)

    def _capture_failure(self, label: str) -> None:
        try:
            self._capture_step(label)
        except Exception:
            pass

    def _log(self, event: str, payload: Dict[str, Any]) -> None:
        json_log(str(self.cfg.log_path), event, payload)

    def _log_branch_ok(self, *, route: str, stage: str) -> None:
        self._log("branch_ok", {"branch": self.cfg.branch_name, "postal_code": self.cfg.postal_code, "route": route, "stage": stage})

    def _build_assert_tokens(self) -> List[str]:
        tokens = _normalize_tokens(self.cfg.branch_name)
        header_assert = self.cfg.header_assert or DEFAULT_HEADER_ASSERT
        tokens.extend(_normalize_tokens(header_assert))
        return sorted({t for t in tokens if t})


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------


def ensure_branch(
    base_url: str,
    postal_code: str,
    branch_name: str,
    selectors: Dict[str, Any],
    evidence_dir: str,
    html_dump_dir: str,
    log_path: str,
    headless: bool = True,
    strict_verify: bool = True,
    *,
    header_assert: Optional[str] = None,
    user_data_dir: Optional[str] = None,
    storage_state_path: Optional[str] = None,
    browser_channel: Optional[str] = None,
    force_refresh: bool = False,
) -> Page:
    cfg = BranchConfig(
        base_url=base_url,
        postal_code=postal_code,
        branch_name=branch_name,
        selectors=selectors,
        evidence_dir=Path(evidence_dir),
        html_dump_dir=Path(html_dump_dir),
        log_path=Path(log_path),
        headless=headless,
        strict_verify=strict_verify,
        header_assert=header_assert,
        user_data_dir=Path(user_data_dir or DEFAULT_USER_DATA_DIR),
        storage_state_path=Path(storage_state_path or DEFAULT_STORAGE_STATE),
        browser_channel=browser_channel or DEFAULT_BROWSER_CHANNEL,
        force_refresh=force_refresh,
    )

    attempts = 2 if not cfg.force_refresh else 1
    page = None
    ensurer: Optional[BranchEnsurer] = None
    last_exc: Optional[Exception] = None
    for attempt in range(attempts):
        ensurer = BranchEnsurer(cfg)
        try:
            page = ensurer.run()
            break
        except Exception as exc:  # pylint: disable=broad-except
            last_exc = exc
            _context = getattr(ensurer, 'context', None)
            if _context:
                try:
                    _context.close()
                except Exception:
                    pass
            _browser = getattr(ensurer, 'browser', None)
            if _browser:
                try:
                    _browser.close()
                except Exception:
                    pass
            _play = getattr(ensurer, 'play', None)
            if _play:
                try:
                    _play.stop()
                except Exception:
                    pass
            if attempt == 0 and not cfg.force_refresh:
                cfg.force_refresh = True
                json_log(str(cfg.log_path), 'branch_refresh_retry', {'reason': str(exc)})
                continue
            raise
    if page is None:
        raise last_exc if last_exc else RuntimeError('Branch selection failed')

    # keep Playwright handles alive for the caller (so the browser stays open)
    setattr(page, "_branch_playwright", ensurer.play)
    setattr(page, "_branch_context", ensurer.context)
    setattr(page, "_branch_browser", ensurer.browser)
    return page


