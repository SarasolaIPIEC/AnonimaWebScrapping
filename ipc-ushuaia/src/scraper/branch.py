"""Selección y persistencia de sucursal en La Anónima Online."""

from playwright.sync_api import Page

__all__ = ["select_branch", "get_current_branch"]


def select_branch(page: Page, city: str = "Ushuaia") -> None:
    """Selecciona la sucursal deseada en la web y persiste la selección.

    TODO: Implementar interacción con el modal de sucursales.
    Evidencia: ``docs/evidence/select_branch.md``
    Export: ``exports/branch_selection.html``

    Parameters
    ----------
    page:
        Instancia de página Playwright.
    city:
        Nombre de la ciudad/sucursal.
    """
    # TODO: Interactuar con el selector de sucursal
    pass


def get_current_branch(page: Page) -> str:
    """Devuelve la sucursal actualmente seleccionada."""

    # TODO: Extraer sucursal actual
    # Evidencia: ``docs/evidence/get_current_branch.md``
    return ""  # TODO: Retornar la sucursal real
