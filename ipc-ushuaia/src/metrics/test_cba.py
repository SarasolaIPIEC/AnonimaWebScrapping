import pandas as pd
from metrics.cba import compute_cba_ae

def test_compute_cba_ae():
    prices = pd.DataFrame([
        {'sku': 'sku1', 'unit_price': 100},
        {'sku': 'sku2', 'unit_price': 200},
    ])
    basket = pd.DataFrame([
        {'sku': 'sku1', 'quantity': 2},
        {'sku': 'sku2', 'quantity': 1},
    ])
    assert compute_cba_ae(prices, basket) == 400
