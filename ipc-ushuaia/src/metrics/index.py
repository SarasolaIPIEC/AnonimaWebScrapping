"""
Cálculo del IPC-Ushuaia e índices de variación mensual/anual.
"""
import pandas as pd
from typing import List, Dict, Any

def compute_index(current: float, previous: float) -> float:
    """
    Calcula la variación porcentual entre dos valores.
    """
    if previous == 0:
        return float('nan')
    return (current - previous) / previous * 100
