from typing import List, Dict, Any, Tuple


def compute_cba_values(items: List[Dict[str, Any]], family_ae: float) -> Tuple[float, float]:
    cba_ae = 0.0
    for r in items:
        val = r.get('cost_item_ae')
        if isinstance(val, (int, float)):
            cba_ae += float(val)
    cba_family = cba_ae * float(family_ae)
    return cba_ae, cba_family

