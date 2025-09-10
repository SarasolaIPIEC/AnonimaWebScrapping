"""Pruebas para normalización de unidades (kg/L/unidad)."""
from src.normalize.units import parse_size, to_base_units


def test_parse_size():
    assert parse_size("1 kg") == (1000, "g")
    assert parse_size("1 L") == (1000, "ml")
    assert parse_size("docena") == (12, "unidad")


def test_to_base_units():
    assert to_base_units(1, "kg") == (1000, "g")
    assert to_base_units(2, "L") == (2000, "ml")
    assert to_base_units(1, "docena") == (12, "unidad")
