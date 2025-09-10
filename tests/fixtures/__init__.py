"""Centraliza accesos a fixtures de pruebas.

Provee utilidades para obtener HTML, CSV y semillas de productos.
"""
from pathlib import Path
from typing import List, Dict, Any

FIXTURES_DIR = Path(__file__).resolve().parent


def html_fixture(name: str = "sample_products.html") -> str:
    """Devuelve el contenido de un fixture HTML."""
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def csv_fixture(name: str = "cba_catalog.csv") -> Path:
    """Devuelve la ruta a un fixture CSV."""
    return FIXTURES_DIR / name


def seed_products() -> List[Dict[str, Any]]:
    """Lista de productos de ejemplo para pruebas."""
    return [
        {
            "name": "Pan fresco La Anónima",
            "sku": "123",
            "price": 120.0,
            "promo_price": 100.0,
            "pack_size": 1,
        },
        {
            "name": "Leche entera",
            "sku": "456",
            "price": 200.0,
            "pack_size": 1,
        },
    ]

# Accesos directos útiles
CBA_CATALOG_CSV = csv_fixture()
