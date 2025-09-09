
# DATA_MODEL_GUIDE.md — Modelo de datos (conceptual)

## Entidades y relaciones (alto nivel)
- **Producto**: categoría + item canasta (ej. Aceite Girasol).
- **SKU**: variante específica (marca, presentación).
- **Precio observado**: monto final, fecha de observación, stock, promoción, URL origen.
- **Ítem de canasta**: cantidad mensual base y unidad (por AE).
- **Ejecución (run)**: metadatos de una corrida de extracción/cálculo.
- **Índice**: costos agregados por período (CBA AE/familia) e indicador base=100 con variaciones.

## Claves y consistencia
- Identificar SKU por combinación de nombre + tamaño + marca + URL.
- Evitar duplicados por período (mismo SKU y fecha/hora de observación).
- Documentar sustituciones y su impacto.

## Exportables
- **Series** de CBA e índice por período.
- **Desagregados** por rubro/ítem para análisis.
