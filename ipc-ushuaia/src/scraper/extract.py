"""
Extracción y parseo de productos desde HTML de La Anónima Online.
Incluye normalización y contrato de salida.
"""

from typing import List, Dict

# TODO: Instalar y usar BeautifulSoup o lxml para parseo

def extract_product_cards(html: str) -> List[Dict]:
    """
    Extrae los datos de productos de un HTML de resultados.
    Args:
        html (str): HTML de la página de resultados.
    Returns:
        List[Dict]: Lista de productos extraídos (dicts normalizados).
    """
    # TODO: Parsear HTML y extraer productos
    pass

def normalize_product(raw: dict) -> dict:
    """
    Normaliza los campos extraídos a un contrato estándar.
    Args:
        raw (dict): Producto crudo extraído.
    Returns:
        dict: Producto normalizado.
    """
    # TODO: Normalizar campos (precio final, unidad, stock, promo, etc.)
    pass
