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

