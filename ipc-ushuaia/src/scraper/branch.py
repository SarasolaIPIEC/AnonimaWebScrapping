"""Selección y persistencia de sucursal en La Anónima Online."""

from __future__ import annotations

import re

from playwright.sync_api import Page

from .utils import capture_evidence

__all__ = ["select_branch", "get_current_branch"]


def select_branch(page: Page, city: str = "Ushuaia") -> None:
    """Selecciona la sucursal deseada en la web y persiste la selección.

    Evidencia: ``docs/evidence/select_branch.md``
    Export: ``exports/branch_selection.html``

    Parameters
    ----------
    page:
        Instancia de página Playwright.
    city:
        Nombre de la ciudad/sucursal.
    """

    selector = "[data-testid='current-branch']"
    try:
        current = page.inner_text(selector).strip()
    except Exception:
        capture_evidence(page, "branch_detect_error", run_id="branch")
        raise

    if city.lower() in current.lower():
        return

    try:
        page.click(selector)
        page.wait_for_selector("text=Tierra del Fuego")
        page.get_by_text("Tierra del Fuego").click()
        page.wait_for_selector(f"text={city}")
        page.get_by_text(city).click()

        # Intentar distintos textos de botón de confirmación
        try:
            page.get_by_role("button", name=re.compile("Ingresar|Aceptar|Confirmar", re.I)).click()
        except Exception:
            pass

        page.wait_for_function(
            """
            (city) => {
                const el = document.querySelector("[data-testid='current-branch']");
                if (!el) return false;
                const text = (el.textContent || '').toLowerCase();
                const title = (el.getAttribute('title') || '').toLowerCase();
                return text.includes(city.toLowerCase()) || title.includes(city.toLowerCase());
            }
            """,
            arg=city,
            timeout=5000,
        )

        updated = page.inner_text(selector).strip()
        title_attr = page.get_attribute(selector, "title") or ""
        if city.lower() not in updated.lower() and city.lower() not in title_attr.lower():
            raise RuntimeError("Branch selection validation failed")

    except Exception:
        capture_evidence(page, "branch_selection_error", run_id="branch")
        raise


def get_current_branch(page: Page) -> str:
    """Devuelve la sucursal actualmente seleccionada."""

    selector = "[data-testid='current-branch']"
    try:
        return page.inner_text(selector).strip()
    except Exception:
        capture_evidence(page, "get_current_branch_error", run_id="branch")
        raise
