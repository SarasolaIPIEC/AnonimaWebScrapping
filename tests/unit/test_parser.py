"""Pruebas para parser, incluyendo manejo de precios promocionales."""
from unittest.mock import patch

from src import parser, normalizer
from tests.fixtures import csv_fixture, seed_products


def test_match_sku_to_cba():
    cba_row = {
        "preferred_keywords": "pan;fresco",
        "fallback_keywords": "lactal",
        "category": "Panaderia",
        "min_pack_size": 1,
    }
    product = {
        "name": "Pan fresco La Anónima",
        "category": "Panaderia",
        "pack_size": 1,
    }
    assert parser.match_sku_to_cba(product, cba_row) == ("preferred", None)


def test_match_sku_to_cba_pack_tolerance():
    cba_row = {
        "preferred_keywords": "leche",
        "fallback_keywords": "",
        "category": "Lacteos",
        "min_pack_size": 1,
    }
    product = {"name": "Leche entera 900ml", "category": "Lacteos", "pack_size": 0.9}
    assert parser.match_sku_to_cba(product, cba_row) == ("preferred", "pack_size_diff")


def test_match_sku_to_cba_parse_size_from_name():
    cba_row = {
        "preferred_keywords": "leche",
        "fallback_keywords": "",
        "category": "Lacteos",
        "min_pack_size": 1,
        "monthly_qty_unit": "L",
    }
    product = {"name": "Leche entera 900 ml", "category": "Lacteos"}
    assert parser.match_sku_to_cba(product, cba_row) == ("preferred", "pack_size_diff")


def test_match_sku_to_cba_category_filter():
    cba_row = {
        "preferred_keywords": "pan;fresco",
        "fallback_keywords": "",
        "category": "Panaderia",
    }
    product = {"name": "Pan fresco", "category": "Lacteos"}
    assert parser.match_sku_to_cba(product, cba_row) is None


def test_map_products_to_cba_with_promo():
    catalog = normalizer.load_cba_catalog(str(csv_fixture()))
    mapping = parser.map_products_to_cba(seed_products(), catalog)
    assert mapping["Pan fresco"]["price"] == 100.0  # Usa precio promocional
    assert mapping["Leche entera"]["price"] == 200.0
    assert mapping["Pan fresco"]["source"] == "preferred"
    assert mapping["Pan fresco"]["reason"] is None


def test_map_products_to_cba_mocked_search():
    catalog = normalizer.load_cba_catalog(str(csv_fixture()))
    products = seed_products()
    with patch(
        "src.parser.match_sku_to_cba",
        side_effect=[("preferred", None), ("preferred", None)],
    ) as mocked:
        mapping = parser.map_products_to_cba(products, catalog)
        assert mocked.call_count == 2
        assert mapping["Pan fresco"]["sku"] == "123"
        assert mapping["Leche entera"]["sku"] == "456"


def test_map_products_to_cba_substitution_reason():
    catalog = [
        {
            "item": "Pan lactal",
            "category": "Panaderia",
            "preferred_keywords": "pan lactal",
            "fallback_keywords": "pan fresco",
            "min_pack_size": 1,
        }
    ]
    products = [
        {
            "name": "Pan fresco", "sku": "789", "price": 100.0, "pack_size": 1, "category": "Panaderia"
        }
    ]
    mapping = parser.map_products_to_cba(products, catalog)
    assert mapping["Pan lactal"]["source"] == "fallback"
    assert mapping["Pan lactal"]["reason"] == "substitution"


def test_map_products_to_cba_prefers_preferred_over_price():
    catalog = [
        {
            "item": "Leche entera",
            "category": "Lacteos",
            "preferred_keywords": "leche entera",
            "fallback_keywords": "bebida lactea",
            "min_pack_size": 1,
        }
    ]
    products = [
        {
            "name": "Bebida lactea",
            "sku": "1",
            "price": 50.0,
            "pack_size": 1,
            "category": "Lacteos",
        },
        {
            "name": "Leche entera",
            "sku": "2",
            "price": 100.0,
            "pack_size": 1,
            "category": "Lacteos",
        },
    ]
    mapping = parser.map_products_to_cba(products, catalog)
    assert mapping["Leche entera"]["sku"] == "2"
    assert mapping["Leche entera"]["source"] == "preferred"


def test_save_evidence_skips_missing(tmp_path):
    mapping = {
        "a": {"sku": "1", "price": 1, "category": "cat"},
        "b": {"sku": None, "price": None, "category": "cat"},
        "c": {"sku": "3", "price": 3, "category": "cat"},
        "d": {"sku": "4", "price": 4, "category": "cat"},
    }
    parser.save_evidence(mapping, output_dir=str(tmp_path))
    assert len(list(tmp_path.iterdir())) == 3
