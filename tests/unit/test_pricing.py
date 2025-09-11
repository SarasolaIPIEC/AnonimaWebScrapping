"""Pruebas para cálculo de precios y costos por ítem."""
from src.normalize.pricing import precio_unitario_base, costo_item_ae


def test_precio_unitario_base():
    price, unit = precio_unitario_base(200, "x2 500 g")
    assert unit == "kg"
    assert price == 200 / 1  # 200 por kg
    price2, unit2 = precio_unitario_base(150, "1/2 kg")
    assert unit2 == "kg"
    assert price2 == 300  # 150 / 0.5


def test_costo_item_ae():
    cost = costo_item_ae(100, "1 kg", 2, "kg")
    assert cost == 200
