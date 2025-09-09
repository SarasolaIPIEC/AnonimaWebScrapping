"""
Tests para heurísticas de matching y mapeo de productos a la CBA.
"""
from src import parser

def test_match_sku_to_cba():
    cba_row = {
        'preferred_keywords': 'pan;fresco',
        'fallback_keywords': 'lactal;salvado'
    }
    product = {'name': 'Pan fresco La Anónima'}
    assert parser.match_sku_to_cba(product, cba_row)
    product2 = {'name': 'Pan lactal'}
    assert parser.match_sku_to_cba(product2, cba_row)
    product3 = {'name': 'Galletitas'}
    assert not parser.match_sku_to_cba(product3, cba_row)

def test_map_products_to_cba():
    cba_catalog = [
        {'item': 'Pan fresco', 'preferred_keywords': 'pan;fresco', 'fallback_keywords': 'lactal;salvado'},
        {'item': 'Leche líquida', 'preferred_keywords': 'leche', 'fallback_keywords': 'descremada'}
    ]
    products = [
        {'name': 'Pan fresco La Anónima', 'sku': '123', 'unit_price': 100, 'pack_size': 1},
        {'name': 'Leche entera', 'sku': '456', 'unit_price': 200, 'pack_size': 1}
    ]
    mapping = parser.map_products_to_cba(products, cba_catalog)
    assert mapping['Pan fresco']['sku'] == '123'
    assert mapping['Leche líquida']['sku'] == '456'
