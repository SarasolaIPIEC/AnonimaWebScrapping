# reports_dev.md — Flujo de reporting (ipc-ushuaia)

- Inputs: `exports/series_cba.csv` (serie mensual) y `exports/breakdown_<period>.csv` (desglose por ítem).
- Enrich: se derivan campos faltantes sin tocar el scraper (presentación base, precio de lista para tachado, flags normalizados, variaciones m/m y i.a. cuando hay período previo, metadatos de fuente y canasta).
- KPIs/serie: se leen y ordenan los puntos de la serie (base=100 en el primer período) y se obtienen KPIs del último: CBA AE, CBA familia (x3,09), índice, m/m, i.a.
- Render HTML: `src/reporting/render.py` construye el contexto (dos vistas conmutables: por producto y por kg/L/un) y renderiza Jinja2 usando plantillas en `src/reporting/templates/`.

Pipeline lógico en `src/reporting/render.py` (funciones puras):
- `load_data(series_path, breakdown_path, period)`
- `validate(rows)` valida precios/URL/unidades (no rompe: acumula advertencias)
- `enrich(rows, period, prev_rows)` deriva: `presentation_text`, `base_equiv_value|unit`, `price_list`, `unit_price`, `qty_AE`, `contrib_AE_$`, `contrib_AE_%`, `variation_mom_%`, `variation_yoy_%`, metadatos
- `compute_kpis(series_rows, enriched_rows)`
- `build_context(...)` agrupa datos para las vistas y filtros
- `render_report()` aplica `templates/base.html`, `templates/report.html` y `templates/macros.html`

Decisiones clave y trazabilidad:
- Canasta fija; sustituciones se registran en `exports/breakdown_*.csv` y `evidence/run_*.jsonl`.
- Precio usado: `price_final` (si hay promoción y es efectivo). `price_list` solo para tachado si `price_original > price_final`.
- Normalización a kg/L/unidad vía `src/normalize/units.py`. Si falta `unit`, se infiere del título (`parse_title_size`).
- Variaciones m/m y unitarias: se compara contra `exports/breakdown_<period-1>.csv` por `item_id`; si no hay base: N/D.
- Fuente: “La Anónima – Suc. 166 Ushuaia 5”. Zona local `America/Argentina/Ushuaia`.

Compatibilidad y CLI:
- Compatibilidad: se mantiene la firma `render_report(out_path, period, series_path, breakdown_path)` usada por `src/cli.py`.
- CLI adicional: `python -m src.reporting.render --period YYYY-MM --in exports/breakdown_<period>.csv --series exports/series_cba.csv --out reports/ [--write-by-category]`.

Riesgos y mitigaciones:
- Cambios de DOM/promos: el render usa datos normalizados (no depende del DOM). Si falta `unit`, se infiere de `title` con tolerancias.
- Codificación: salida en UTF-8; plantillas no embeben mojibake. Helpers de formateo AR.
- Datos faltantes: se muestran como “N/D” sin romper ordenamiento/JS.
- Jinja2 no instalado: fallback a renderizador actual para no bloquear el pipeline.

Criterio de “listo”:
- Reporte HTML compila sin errores con dos vistas conmutables, filtros básicos y KPI correctos.
- Se puede ejecutar vía CLI principal y vía módulo `-m`.
- Tests de humo para formateo, unitario, orden por aporte y N/D pasan.
