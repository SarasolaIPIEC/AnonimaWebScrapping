"""Pruebas para parser, incluyendo manejo de precios promocionales."""
from unittest.mock import patch

from src import parser, normalizer
from tests.fixtures import csv_fixture, seed_products


def test_match_sku_to_cba():
    cba_row = {"preferred_keywords": "pan;fresco", "fallback_keywords": "lactal"}
    product = {"name": "Pan fresco La Anónima"}
    assert parser.match_sku_to_cba(product, cba_row)


def test_map_products_to_cba_with_promo():
    catalog = normalizer.load_cba_catalog(str(csv_fixture()))
    mapping = parser.map_products_to_cba(seed_products(), catalog)
    assert mapping["Pan fresco"]["price"] == 100.0  # Usa precio promocional
    assert mapping["Leche entera"]["price"] == 200.0


def test_map_products_to_cba_mocked_search():
    catalog = normalizer.load_cba_catalog(str(csv_fixture()))
    products = seed_products()
    with patch("src.parser.match_sku_to_cba", side_effect=[True, False, False, True]) as mocked:
        mapping = parser.map_products_to_cba(products, catalog)
        assert mocked.call_count == 4
        assert mapping["Pan fresco"]["sku"] == "123"
        assert mapping["Leche entera"]["sku"] == "456"
