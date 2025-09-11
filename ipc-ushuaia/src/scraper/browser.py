"""Utilidades de navegador para scraping con Playwright."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright


def launch_browser(
    headless: bool = True,
    user_agent: str | None = None,
    storage_state: str = "storage_state.json",
) -> Tuple[Browser, BrowserContext, Page]:
    """Inicializa Playwright y reutiliza la sesión si está disponible.

    Parameters
    ----------
    headless:
        Ejecutar el navegador en modo *headless*.
    user_agent:
        Cadena de ``User-Agent`` personalizada.
    storage_state:
        Archivo donde se persisten cookies y ``localStorage`` para reusar
        sesiones entre ejecuciones.

    Returns
    -------
    tuple
        Instancias ``(browser, context, page)`` listas para usar.
    """

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=headless)

    state_file = Path(storage_state)
    context = browser.new_context(
        user_agent=user_agent,
        storage_state=state_file.read_text() if state_file.exists() else None,
    )

    page = context.new_page()
    return browser, context, page


def close_browser(
    browser: Browser,
    context: BrowserContext,
    storage_state: str = "storage_state.json",
) -> None:
    """Cierra Playwright y persiste la sesión en disco."""

    state_file = Path(storage_state)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(state_file))
    context.close()
    browser.close()
    # ``sync_playwright().start()`` devuelve un manejador global que se cierra
    # automáticamente al cerrar el navegador, por lo que no es necesario
    # conservar una referencia para detenerlo explícitamente aquí.

