"""
Normalizador de precios por unidad base.
Calcula precio por unidad base a partir de precio, tamaño y unidad.
"""

def unit_price(price: float, pack_size: float, pack_unit: str, base_unit: str) -> float:
    """
    Calcula el precio por unidad base.
    Ej: price=300, pack_size=900, pack_unit='ml', base_unit='ml' -> 0.333...
    """
    from .units import to_base_units

    # Convertir pack_size a la unidad base deseada
    base_qty, base_unit_conv = to_base_units(pack_size, pack_unit)
    if base_unit_conv != base_unit:
        raise ValueError(f"No se puede convertir {pack_unit} a {base_unit}")
    if base_qty == 0:
        raise ValueError("El tamaño del pack no puede ser cero")
    return price / base_qty
