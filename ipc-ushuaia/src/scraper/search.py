"""Búsqueda y navegación con soporte de paginado y scroll."""

from __future__ import annotations

from typing import List

from playwright.sync_api import Page, TimeoutError

from src.infra.retry import exponential_backoff

from .utils import is_allowed, random_delay, save_html

__all__ = ["search", "list_category", "paginate"]


@exponential_backoff(max_attempts=3)
def search(page: Page, query: str, home_url: str = "https://supermercado.laanonimaonline.com/") -> str:
    """Realiza una búsqueda y retorna el HTML resultante.

    TODO: registrar cambios de DOM al expedir ``docs/evidence/search.md``.
    Evidencia: ``docs/evidence/search_{query}.html``
    Export: ``exports/search_{query}.html``

    El flujo navega a la *home* del sitio, completa el formulario
    ``#form_buscar`` y espera a que aparezcan elementos
    ``[data-testid='product-card']`` en la respuesta. Si los productos no se
    cargan, se captura el HTML igualmente para facilitar la depuración.
    """

    try:
        random_delay()
        page.goto(home_url)
        page.wait_for_selector("form#form_buscar")
        page.fill("#buscar", query)
        try:
            page.click("#btn_buscar_imetrics")
        except Exception:
            page.press("#buscar", "Enter")
        try:
            page.wait_for_selector("[data-testid='product-card']")
        except TimeoutError:
            save_html(page.content(), f"search_{query}")
            raise
        return page.content()
    except Exception:
        save_html(page.content(), "search_error")
        raise


@exponential_backoff(max_attempts=3)
def list_category(page: Page, category_path: str) -> str:
    """Navega a una categoría y devuelve el HTML de la página."""

    try:
        user_agent = page.context.user_agent
        if not is_allowed(category_path, user_agent):
            raise RuntimeError("URL blocked by robots.txt")
        random_delay()
        page.goto(category_path)
        page.wait_for_selector("[data-testid='product-card']")
        return page.content()
    except Exception:
        save_html(page.content(), "category_error")
        raise


def paginate(page: Page) -> List[str]:
    """Itera sobre páginas de resultados acumulando el HTML.

    Implementa *scroll* y paginado a través de un botón "siguiente" con
    reintentos y backoff exponencial en cada iteración.
    """

    html_pages: List[str] = []
    while True:
        random_delay()
        page.wait_for_selector("[data-testid='product-card']")
        html_pages.append(page.content())

        next_btn = page.get_by_role("button", name="Siguiente")
        if not next_btn or not next_btn.is_enabled():
            break

        @exponential_backoff(max_attempts=3)
        def _click_next():  # pragma: no cover - depende del DOM
            random_delay()
            next_btn.click()
            page.wait_for_load_state("networkidle")

        try:
            _click_next()
        except Exception:
            save_html(page.content(), "paginate_error")
            break

    return html_pages
