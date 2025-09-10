"""Pruebas para parser, incluyendo manejo de precios promocionales."""
from src import parser, normalizer
from tests.fixtures import data


def test_match_sku_to_cba():
    cba_row = {"preferred_keywords": "pan;fresco", "fallback_keywords": "lactal"}
    product = {"name": "Pan fresco La Anónima"}
    assert parser.match_sku_to_cba(product, cba_row)


def test_map_products_to_cba_with_promo():
    catalog = normalizer.load_cba_catalog(str(data.CBA_CATALOG_CSV))
    mapping = parser.map_products_to_cba(data.PRODUCTS, catalog)
    assert mapping["Pan fresco"]["price"] == 100.0  # Usa precio promocional
    assert mapping["Leche entera"]["price"] == 200.0
