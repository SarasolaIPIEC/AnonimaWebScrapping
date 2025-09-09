"""
Tests para el motor de cálculo de CBA e índice.
"""
import pandas as pd
from src import index_engine

def test_calculate_cba():
    catalog = [
        {'item': 'Pan fresco', 'adjusted_qty': 6},
        {'item': 'Leche líquida', 'adjusted_qty': 9}
    ]
    prices = {'Pan fresco': 100, 'Leche líquida': 200}
    total, missing = index_engine.calculate_cba(catalog, prices)
    assert total == 6*100 + 9*200
    assert missing == []

def test_calculate_index_and_variations():
    series = pd.Series({'2024-01': 1000, '2024-02': 1100, '2024-03': 1200})
    idx = index_engine.calculate_index(series, base_period='2024-01')
    assert idx['2024-01'] == 100
    df = index_engine.calculate_variations(idx)
    assert 'var_mm' in df.columns
