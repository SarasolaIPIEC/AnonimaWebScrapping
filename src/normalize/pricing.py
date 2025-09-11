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


def precio_unitario_base(price: float, presentation: str) -> tuple[float, str]:
    """Calcula el precio por unidad base a partir de una presentación textual."""
    from .units import parse_size

    qty, unit = parse_size(presentation)
    if qty <= 0:
        raise ValueError("La cantidad debe ser positiva")
    return price / qty, unit


def costo_item_ae(
    price: float,
    presentation: str,
    monthly_qty_value: float,
    monthly_qty_unit: str,
) -> float:
    """Calcula el costo mensual del ítem por Adulto Equivalente."""
    from .units import to_base_units

    unit_price_val, base_unit = precio_unitario_base(price, presentation)
    qty_base, qty_unit = to_base_units(monthly_qty_value, monthly_qty_unit)
    if qty_unit != base_unit:
        raise ValueError("Unidades incompatibles entre precio y cantidad mensual")
    return unit_price_val * qty_base
