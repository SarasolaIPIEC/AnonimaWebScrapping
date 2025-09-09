
# NORMALIZATION_GUIDE.md — Normalización de presentaciones y precios

## Unidades base
- **Masa**: kg (1 kg = 1000 g).
- **Volumen**: L (1 L = 1000 ml = 1000 cc).
- **Cuenta**: unidad (incluye docena = 12 unidades).

## Casos frecuentes
- **Multipack**: "x2 500 g" ⇒ total 1000 g = 1 kg.
- **Fracciones**: "1/2 kg" = 0,5 kg; "1/4 kg" = 0,25 kg.
- **Docenas**: huevos: 1 docena = 12 unidades.

## Precio por unidad base
- `precio_unitario_base = precio_final / cantidad_en_unidad_base`.
- Costo en canasta: `precio_unitario_base * cantidad_mensual_base` (por AE).

## Validaciones recomendadas
- No permitir valores negativos/cero en cantidades o precios.
- Redondeos coherentes para mostrar (no para calcular).
