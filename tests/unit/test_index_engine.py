"""Pruebas para el motor de índice y cálculo de CBA."""
import pandas as pd
import pytest
from src import index_engine, normalizer
from tests.fixtures import data


def _prices_from_mapping(mapping):
    return {item: info["price"] for item, info in mapping.items()}


def test_calculate_cba_ae_and_family():
    catalog = normalizer.load_cba_catalog(str(data.CBA_CATALOG_CSV))
    mapping = {
        "Pan fresco": {"price": 100.0},
        "Leche entera": {"price": 200.0},
    }
    adjusted_ae = normalizer.adjust_quantities(catalog, ae_multiplier=1.0)
    total_ae, missing = index_engine.calculate_cba(adjusted_ae, _prices_from_mapping(mapping))
    assert missing == []
    assert total_ae == 100.0 * 1 + 200.0 * 2

    adjusted_family = normalizer.adjust_quantities(catalog, ae_multiplier=3.09)
    total_family, _ = index_engine.calculate_cba(adjusted_family, _prices_from_mapping(mapping))
    assert total_family == pytest.approx(total_ae * 3.09)


def test_calculate_index_and_variations():
    series = pd.Series({"2023-01": 500, "2023-02": 550})
    index = index_engine.calculate_index(series, "2023-01")
    assert index.loc["2023-01"] == 100
    assert index.loc["2023-02"] == pytest.approx(110)

    df = index_engine.calculate_variations(index)
    assert pytest.approx(df.loc["2023-02", "var_mm"], rel=1e-4) == 10.0


def test_validate_series():
    dates = pd.to_datetime(["2023-01", "2023-02", "2023-03"])
    index = pd.DataFrame({"index": pd.Series([100, None, 300000], index=dates)})
    summary = index_engine.validate_series(index)
    assert summary["missing"]["index"] == 1
    assert isinstance(summary["outliers"], list)
