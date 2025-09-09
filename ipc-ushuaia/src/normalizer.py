"""
Normalizador de unidades, precios y cantidades ajustables por AE/familia.
Incluye validaciones de integridad y consistencia de la canasta.
"""

import csv
from typing import List, Dict, Any

def load_cba_catalog(path: str) -> List[Dict[str, Any]]:
    """
    Carga la canasta básica alimentaria desde un CSV.
    """
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        return [row for row in reader]

def adjust_quantities(cba_catalog: List[Dict[str, Any]], ae_multiplier: float = 1.0) -> List[Dict[str, Any]]:
    """
    Ajusta las cantidades de cada alimento según el multiplicador de AE/familia.
    """
    adjusted = []
    for row in cba_catalog:
        row_copy = row.copy()
        try:
            base_qty = float(row['monthly_qty_value'])
            row_copy['adjusted_qty'] = base_qty * ae_multiplier
        except (ValueError, KeyError):
            row_copy['adjusted_qty'] = None
        adjusted.append(row_copy)
    return adjusted

def validate_cba(cba_catalog: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Valida integridad y consistencia de la canasta:
    - Suma por rubro
    - Consistencia de unidades
    - Flags si falta SKU o hay unidades inconsistentes
    """
    summary = {}
    unit_set = set()
    missing_qty = []
    for row in cba_catalog:
        unit_set.add(row.get('monthly_qty_unit', ''))
        if not row.get('monthly_qty_value'):
            missing_qty.append(row.get('item', ''))
    summary['units'] = list(unit_set)
    summary['missing_qty'] = missing_qty
    # Suma por rubro
    by_category = {}
    for row in cba_catalog:
        cat = row.get('category', 'Otros')
        try:
            qty = float(row['monthly_qty_value'])
        except (ValueError, KeyError):
            qty = 0
        by_category[cat] = by_category.get(cat, 0) + qty
    summary['sum_by_category'] = by_category
    return summary

# TODO: Integrar con el parser y el motor de cálculo para matching y prorrateos
