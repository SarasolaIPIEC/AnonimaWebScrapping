
# SCRAPING_GUIDE.md — Guía conceptual de recolección de precios

## Objetivo
Obtener el **precio final al consumidor** para cada ítem representativo de la CBA local desde **La Anónima Online (Ushuaia)**.

## Reglas clave
- **Sucursal correcta**: verificar que la vista active sea **Ushuaia** (persistir cookie/sesión).
- **Precio final**: usar el valor que paga el comprador; si hay promoción efectiva, usar ese precio.
- **OOS** (fuera de stock): registrar y aplicar **sustitución documentada**.
- **Presentaciones**: reconocer tamaños (p. ej. 900 ml vs 1,5 L) y luego **normalizar** a base (L/kg/unidad).

## Estrategias
- **Búsqueda** por palabra clave y/o **navegación por categoría**.
- **Selectores robustos**: preferir atributos estables (data-*) antes que clases volátiles.
- **Resiliencia**: timeouts, reintentos exponenciales, captura de HTML ante fallos.

## Evidencia y auditoría
- Guardar **capturas de pantalla o HTML** para muestras aleatorias de ítems críticos.
- Mantener un **log** de sustituciones, OOS y promociones aplicadas.
