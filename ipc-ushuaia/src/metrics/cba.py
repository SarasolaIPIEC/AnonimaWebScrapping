"""
Cálculo del costo de la Canasta Básica Alimentaria (CBA) para un Adulto Equivalente (AE).
"""
import pandas as pd
from typing import List, Dict, Any

def compute_cba_ae(prices: pd.DataFrame, basket: pd.DataFrame) -> float:
    """
    Calcula el costo total de la CBA para un Adulto Equivalente.
    prices: DataFrame con columnas ['sku', 'unit_price']
    basket: DataFrame con columnas ['sku', 'quantity']
    Retorna el costo total (float).
    """
    merged = pd.merge(basket, prices, on='sku', how='inner')
    merged['total'] = merged['quantity'] * merged['unit_price']
    return merged['total'].sum()
