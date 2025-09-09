"""
Tests para cálculo de precio por unidad base.
"""
from src.normalize.pricing import unit_price

def test_unit_price_cases():
    assert abs(unit_price(300, 900, 'ml', 'ml') - 0.333333) < 1e-5
    assert abs(unit_price(120, 1000, 'g', 'g') - 0.12) < 1e-5
    assert abs(unit_price(240, 2, 'kg', 'g') - 0.12) < 1e-5  # 2 kg = 2000 g
    assert abs(unit_price(100, 1, 'docena', 'unidad') - 8.333333) < 1e-5  # 1 docena = 12 unidades
