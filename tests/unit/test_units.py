"""Pruebas para normalización de unidades (kg/L/unidad)."""
from src.normalize.units import parse_size, to_base_units


def test_parse_size():
    assert parse_size("1 kg") == (1, "kg")
    assert parse_size("1 L") == (1, "l")
    assert parse_size("docena") == (12, "unit")
    assert parse_size("x2 500 g") == (1, "kg")
    assert parse_size("1/2 kg") == (0.5, "kg")


def test_to_base_units():
    assert to_base_units(1, "kg") == (1, "kg")
    assert to_base_units(500, "g") == (0.5, "kg")
    assert to_base_units(2, "L") == (2, "l")
    assert to_base_units(750, "ml") == (0.75, "l")
    assert to_base_units(1, "docena") == (12, "unit")
