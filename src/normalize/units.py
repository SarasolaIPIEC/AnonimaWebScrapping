"""
Parser y normalizador de tamaños y unidades.
Detecta patrones como '1 kg', '900 ml', 'x2 500g', 'docena', fracciones y multi-pack.
"""

import re
from typing import Tuple

# Alias y conversiones
_unit_aliases = {
    'g': 'g', 'gr': 'g', 'grs': 'g',
    'kg': 'kg', 'kilo': 'kg',
    'ml': 'ml', 'cc': 'ml',
    'l': 'l', 'lt': 'l', 'litro': 'l',
    'unidad': 'unidad', 'un': 'unidad', 'u': 'unidad',
    'unidades': 'unidad',  # Soporte plural
    'docena': 'docena', 'docenas': 'docena',
}

# Conversión a unidades base kg/L/unidad
_unit_multipliers = {
    'g': 0.001,     # gramos -> kg
    'kg': 1,
    'ml': 0.001,    # mililitros -> L
    'l': 1,
    'unidad': 1,
    'docena': 12,   # docena -> unidades
}

def _parse_fraction(s):
    s = s.replace('½', '1/2').replace('¼', '1/4')
    if '/' in s:
        num, den = s.split('/')
        return float(num) / float(den)
    return float(s)

def parse_size(text: str) -> Tuple[float, str]:
    """
    Extrae cantidad y unidad base (kg/L/unidad) de una descripción textual.
    Ej: 'x2 500g' -> (1.0, 'kg')
    """
    text = text.lower().strip()
    # Multi-pack: xN ...
    m = re.match(r"x\s*(\d+)\s*(.*)", text)
    if m:
        mult = int(m.group(1))
        rest = m.group(2).strip()
        qty, unit = parse_size(rest)
        return mult * qty, unit
    # Multi-pack con fracción: xN fracción unidad
    m = re.match(r"x\s*(\d+)\s*([\d/.,]+)\s*([a-zA-Z]+)", text)
    if m:
        mult = int(m.group(1))
        qty = _parse_fraction(m.group(2).replace(',', '.'))
        unit = m.group(3)
        base_qty, base_unit = to_base_units(qty, unit)
        return mult * base_qty, base_unit
    # Fracción: 1/2 kg, 0.5 kg, ½ kg
    m = re.match(r"([\d/.,]+)\s*([a-zA-Z]+)", text)
    if m:
        qty = _parse_fraction(m.group(1).replace(',', '.'))
        unit = m.group(2)
        return to_base_units(qty, unit)
    # Docena
    if 'docena' in text:
        m = re.match(r"(\d+)\s*docena", text)
        if m:
            return int(m.group(1)) * 12, 'unidad'
        return 12, 'unidad'
    # Unidades
    m = re.match(r"(\d+)\s*unidades?", text)
    if m:
        return int(m.group(1)), 'unidad'
    # Solo número (asumir unidad)
    m = re.match(r"(\d+)$", text)
    if m:
        return float(m.group(1)), 'unidad'
    # Si solo dice 'docena'
    if text.strip() == 'docena':
        return 12, 'unidad'
    raise ValueError(f"No se pudo parsear tamaño: {text}")

def to_base_units(value: float, unit: str) -> Tuple[float, str]:
    """
    Convierte a unidad base kg/L/unidad.
    Ej: (500, 'g') -> (0.5, 'kg')
    """
    unit = unit.lower()
    if unit not in _unit_aliases:
        raise ValueError(f"Unidad desconocida: {unit}")
    canonical = _unit_aliases[unit]
    if canonical not in _unit_multipliers:
        raise ValueError(f"Unidad no convertible: {unit}")
    mult = _unit_multipliers[canonical]
    if canonical == 'docena':
        return value * mult, 'unidad'
    if canonical in ('g', 'kg'):
        return value * mult, 'kg'
    if canonical in ('ml', 'l'):
        return value * mult, 'L'
    return value * mult, canonical
