"""
Selección y persistencia de sucursal en La Anónima Online.
"""

def select_branch(page, city: str = "Ushuaia") -> None:
    """
    Selecciona la sucursal deseada en la web y persiste la selección.
    Args:
        page: Instancia de página Playwright.
        city (str): Nombre de la ciudad/sucursal.
    """
    # TODO: Interactuar con el selector de sucursal
    pass

def get_current_branch(page) -> str:
    """
    Devuelve la sucursal actualmente seleccionada.
    Args:
        page: Instancia de página Playwright.
    Returns:
        str: Nombre de la sucursal seleccionada.
    """
    # TODO: Extraer sucursal actual
    pass
