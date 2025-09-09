"""
Tests para parser y normalizador de unidades y tamaños.
"""
from src.normalize.units import parse_size, to_base_units

def test_parse_size_cases():
    assert parse_size('1 kg') == (1000, 'g')
    assert parse_size('900 ml') == (900, 'ml')
    assert parse_size('x2 500g') == (1000, 'g')
    assert parse_size('docena') == (12, 'unidad')
    assert parse_size('2 docenas') == (24, 'unidad')
    assert parse_size('1/2 kg') == (500, 'g')
    assert parse_size('x3 900ml') == (2700, 'ml')
    assert parse_size('750 cc') == (750, 'ml')
    assert parse_size('1.5 L') == (1500, 'ml')
    assert parse_size('x4 250g') == (1000, 'g')
    assert parse_size('3 unidades') == (3, 'unidad')
    assert parse_size('x2 1/2 kg') == (1000, 'g')

def test_to_base_units_cases():
    assert to_base_units(1.5, 'L') == (1500, 'ml')
    assert to_base_units(2, 'kg') == (2000, 'g')
    assert to_base_units(500, 'g') == (500, 'g')
    assert to_base_units(1, 'docena') == (12, 'unidad')
    assert to_base_units(2, 'docena') == (24, 'unidad')
