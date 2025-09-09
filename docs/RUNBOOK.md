
# RUNBOOK.md — Guía operativa (alto nivel)

## Flujo general
1. Preparar contexto (sucursal Ushuaia).
2. Relevar precios (preferentemente en un único “run”).
3. Normalizar unidades y calcular precio por unidad base.
4. Calcular CBA AE y CBA familia (3,09 AE).
5. Actualizar índice (base=100 en el primer período) y variaciones.
6. Generar exports y reporte.

## Validaciones mínimas por corrida
- % de ítems con precio válido ≥ umbral definido.
- Diferencias contra mes previo dentro de rangos esperados por rubro.
- Registro de OOS y sustituciones.

## Recuperación ante fallos
- Reintentar extracción por lotes.
- Usar HTML capturado para depurar selectores.
- Documentar cualquier ajuste metodológico.
