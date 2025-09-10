"""Pruebas para el módulo normalizer."""
from src import normalizer
from tests.fixtures import data


def test_load_cba_catalog():
    catalog = normalizer.load_cba_catalog(str(data.CBA_CATALOG_CSV))
    assert len(catalog) == 2
    assert catalog[0]["item"] == "Pan fresco"


def test_adjust_quantities_family_type():
    catalog = normalizer.load_cba_catalog(str(data.CBA_CATALOG_CSV))
    adjusted = normalizer.adjust_quantities(catalog, ae_multiplier=3.09)
    pan = next(row for row in adjusted if row["item"] == "Pan fresco")
    assert pan["adjusted_qty"] == 3.09


def test_validate_cba():
    catalog = normalizer.load_cba_catalog(str(data.CBA_CATALOG_CSV))
    summary = normalizer.validate_cba(catalog)
    assert set(summary["units"]) == {"kg", "L"}
    assert summary["missing_qty"] == []
