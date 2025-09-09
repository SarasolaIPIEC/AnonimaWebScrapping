import pandas as pd
from metrics.cba import compute_cba_ae
from metrics.index import compute_index

def test_integration_cba_index():
    prices = pd.DataFrame([
        {'sku': 'sku1', 'unit_price': 100},
        {'sku': 'sku2', 'unit_price': 200},
    ])
    basket = pd.DataFrame([
        {'sku': 'sku1', 'quantity': 2},
        {'sku': 'sku2', 'quantity': 1},
    ])
    cba = compute_cba_ae(prices, basket)
    assert cba == 400
    prev = 350
    idx = compute_index(cba, prev)
    assert round(idx, 2) == round((400-350)/350*100, 2)
