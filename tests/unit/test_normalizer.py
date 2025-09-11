"""Pruebas para el módulo normalizer."""
from src import normalizer
from tests.fixtures import csv_fixture


def test_load_cba_catalog():
    catalog = normalizer.load_cba_catalog(str(csv_fixture()))
    assert len(catalog) == 2
    assert catalog[0]["item"] == "Pan fresco"


def test_adjust_quantities_family_type():
    catalog = normalizer.load_cba_catalog(str(csv_fixture()))
    adjusted = normalizer.adjust_quantities(catalog, ae_multiplier=3.09)
    pan = next(row for row in adjusted if row["item"] == "Pan fresco")
    assert pan["adjusted_qty"] == 3.09


def test_validate_cba():
    catalog = normalizer.load_cba_catalog(str(csv_fixture()))
    summary = normalizer.validate_cba(catalog)
    assert set(summary["units"]) == {"kg", "L"}
    assert summary["missing_qty"] == []


def test_load_cba_catalog_creates_file(tmp_path):
    tmp_file = tmp_path / "cba.csv"
    catalog = normalizer.load_cba_catalog(str(tmp_file))
    assert catalog == []
    assert tmp_file.exists()
    with open(tmp_file, encoding="utf-8") as fh:
        header = fh.readline().strip().split(",")
    assert header == normalizer.CBA_COLUMNS
