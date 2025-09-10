"""Fixtures de productos y rutas de catálogos.

Supuestos:
- ``promo_price`` representa el precio final con descuento.
- ``pack_size`` ya está expresado en la unidad base (kg/L/unidad).
"""
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent
CBA_CATALOG_CSV = FIXTURES_DIR / "cba_catalog.csv"

PRODUCTS = [
    {
        "name": "Pan fresco La Anónima",
        "sku": "123",
        "price": 120.0,
        "promo_price": 100.0,
        "pack_size": 1,  # 1 kg
    },
    {
        "name": "Leche entera",
        "sku": "456",
        "price": 200.0,
        "pack_size": 1,  # 1 L
    },
]
