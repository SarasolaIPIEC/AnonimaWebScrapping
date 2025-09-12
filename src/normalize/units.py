import re
from typing import Tuple


_NUM = r"(?:\d+(?:[\.,]\d+)?)"


def _to_float(num: str) -> float:
    return float(num.replace(',', '.'))


def parse_title_size(title: str) -> Tuple[float, str]:
    """
    Parse presentation from title and return quantity in base unit and unit among kg/l/unit.
    Handles: g/kg, ml/L/cc, docena, xN 500 g, 1/2 kg, 1/4 kg, pack x2 500 g, etc.
    """
    t = title.lower()

    # docena / media docena
    if re.search(r"\bmedia\s+docena\b", t):
        return 6.0, 'unit'
    if re.search(r"docena", t):
        return 12.0, 'unit'

    # units count like 6 u / 6 unidades / x6 u
    m = re.search(r"(?:x\s*)?(\d+)\s*(?:u\b|unid(?:ades)?\b)", t)
    if m:
        return float(m.group(1)), 'unit'

    # patterns like 1 1/2 l or 2 1/2 kg
    m = re.search(r"(\d+)\s+1/2\s*(kg|kilo|kilogramo|l|lt|litro)", t)
    if m:
        whole = float(m.group(1))
        unit = m.group(2)
        qty, base = _normalize_unit(1.0, unit)
        return (whole + 0.5) * qty, base

    # xN packs like x2 500 g or 2 x 500 g
    m = re.search(rf"(?:x|\b)(\d+)\s*[×x]?\s*({_NUM})\s*(kg|g|gr|gramos|l|lt|ml|cc)", t)
    if m:
        n = int(m.group(1))
        num = _to_float(m.group(2))
        unit = m.group(3)
        qty, base = _normalize_unit(num, unit)
        return n * qty, base

    # 1/2 kg, 1/4 kg
    m = re.search(r"(1/2|1/4)\s*(kg|kilo|kilogramo|l|lt|litro)", t)
    if m:
        frac = m.group(1)
        unit = m.group(2)
        factor = 0.5 if frac == '1/2' else 0.25
        qty, base = _normalize_unit(1.0, unit)
        return factor * qty, base

    # explicit quantity like 1.5 l, 900 ml, 500 g, 1 kg
    m = re.search(rf"({_NUM})\s*(kg|kilo|kilogramo|g|gr|gramos|l|lt|litro|ml|cc)", t)
    if m:
        num = _to_float(m.group(1))
        unit = m.group(2)
        return _normalize_unit(num, unit)

    # fallback: unidad
    return 1.0, 'unit'


def _normalize_unit(num: float, unit: str) -> Tuple[float, str]:
    u = unit.lower()
    if u in ('kg', 'kilo', 'kilogramo'):
        return float(num), 'kg'
    if u in ('g', 'gr', 'gramos'):
        return float(num) / 1000.0, 'kg'
    if u in ('l', 'lt', 'litro'):
        return float(num), 'l'
    if u in ('ml', 'cc'):
        return float(num) / 1000.0, 'l'
    return float(num), 'unit'
