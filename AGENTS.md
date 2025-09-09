
# AGENTS.md — Guía para Copilot/Codex (ipc-ushuaia)

**Propósito:** orientar a Copilot/Codex para que comprenda el proyecto y produzca entregables consistentes con autonomía, sin plazos y sin pedir confirmaciones triviales.

## Contexto persistente
- Proyecto: **ipc-ushuaia** — índice local de precios estilo CBA (Canasta Básica Alimentaria) para Ushuaia.
- Fuente de precios: **La Anónima Online**, sucursal **Ushuaia**. Considerar **precio final al consumidor** (si hay promoción vigente y es el precio efectivo, utilizarlo).
- Unidad de cálculo: **CBA por Adulto Equivalente (AE)**. Hogar **familia tipo = 3,09 AE**.
- Índice: **base = 100** en el primer período de la serie; publicar **variación m/m** e **i.a.**.
- Periodicidad: **mensual** (sin fechas fijas en estos documentos).
- Metodología: **canasta fija**, sustituciones **documentadas** cuando falte un producto.

## Principios de diseño para Copilot
- **Autonomía**: proponer alternativas técnicas justificadas cuando haya ambigüedad.
- **Robustez**: contemplar cambios de DOM, OOS, promociones, multi-presentaciones y redondeos de unidad.
- **Trazabilidad**: dejar rastro de decisiones (comentarios, docs) y versionado de insumos.
- **Reutilización**: separar scraping, normalización, cálculo, reporting.
- **No plazos**: evitar timestamps/fechas en los documentos guía; la periodicidad es configurable.

## Qué producir (cuando se solicite)
- Planes de subtareas extensos, seccionados, con criterios de “listo” y riesgos/mitigaciones.
- Archivos de configuración y documentación explicativa (README, metodología, runbook).
- Esqueletos de implementación solo cuando un prompt lo pida explícitamente.

## Qué evitar
- Decisiones irreversibles sin justificar alternativas.
- Supuestos no documentados sobre impuestos locales.
- Plazos o cronogramas rígidos.

## Criterios de aceptación (macro)
- La canasta y sus cantidades por AE están claras y trazables.
- El precio utilizado por ítem corresponde al **precio final** visible para Ushuaia.
- Las unidades se normalizan a **kg/L/unidad** y los cálculos por ítem son reproducibles.
- El índice y sus variaciones se derivan de la serie de costos mensual sin “hardcodeos”.
- La documentación permite a terceros replicar el proceso.
