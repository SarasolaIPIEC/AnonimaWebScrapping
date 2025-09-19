

import re
from src.normalize.units import parse_title_size

def precio_unitario_base(price, qty_base):
    """
    Calcula el precio unitario base (precio / cantidad base).
    Permite presentaciones tipo string ("x2 500 g", "1/2 kg", "1 kg", etc) y retorna (precio_unitario, unidad_base).
    """
    if isinstance(qty_base, str):
        qty, unit = parse_title_size(qty_base)
    else:
        qty, unit = qty_base, 'unit'
    if price and qty:
        return price / qty, unit.lower()
    return 0.0, unit.lower()

def costo_item_ae(price: float, qty_base: str, monthly_qty: float, unit: str) -> float:
    """Calcula el costo mensual por AE para un ítem dado el precio, presentación y cantidad mensual."""
    # Para simplificar, asume qty_base ya normalizado a unidad base (kg/l/unit)
    # En casos reales, se debe parsear qty_base y unit
    try:
        base_qty = float(qty_base.split()[0]) if isinstance(qty_base, str) else float(qty_base)
        unit_price = price / base_qty if base_qty else 0.0
        return unit_price * monthly_qty
    except Exception:
        return 0.0

__all__ = [
    "compute_item_costs", "precio_unitario_base"
]
from typing import List, Dict, Any


def compute_item_costs(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for r in rows:
        price = r.get('price_final') or 0
        qty_base = r.get('qty_base') or 0
        monthly_qty = r.get('monthly_qty_base') or 0
        unit_price_base = (price / qty_base) if price and qty_base else None
        cost_item_ae = (unit_price_base * monthly_qty) if unit_price_base and monthly_qty else None
        r2 = dict(r)
        r2['unit_price_base'] = unit_price_base
        r2['cost_item_ae'] = cost_item_ae
        out.append(r2)
    return out

