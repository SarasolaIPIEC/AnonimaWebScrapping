"""
Tests para funciones de normalización y validación de la canasta.
"""
import os
from src import normalizer

def test_load_and_adjust():
    path = os.path.join(os.path.dirname(__file__), '../data/cba_catalog.csv')
    cba = normalizer.load_cba_catalog(path)
    adjusted = normalizer.adjust_quantities(cba, ae_multiplier=3.09)
    assert all('adjusted_qty' in row for row in adjusted)
    assert adjusted[0]['adjusted_qty'] == float(adjusted[0]['monthly_qty_value']) * 3.09

def test_validate_cba():
    path = os.path.join(os.path.dirname(__file__), '../data/cba_catalog.csv')
    cba = normalizer.load_cba_catalog(path)
    summary = normalizer.validate_cba(cba)
    assert 'units' in summary
    assert 'sum_by_category' in summary
