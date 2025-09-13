# Reporte v2 — Runbook de reporting (ipc-ushuaia)

Propósito: documentar el flujo end‑to‑end y las decisiones de diseño del reporte HTML para facilitar mantenimiento y evolución sin romper la CLI.

## Flujo de datos (alto nivel)
- Inputs: `data/cba_catalog.csv` (canasta fija y cantidades por AE) + scraping/pins → `src/site/*` extrae `title/url/price_final/...` y stock/promo.
- Enrichment: `src/normalize/pricing.py` calcula `unit_price_base` y `cost_item_ae` por ítem (base kg/L/unidad).
- KPIs/serie: `src/metrics/cba.py` agrega CBA AE y familia (= AE × 3,09); `src/metrics/index.py` mantiene `exports/series_cba.csv` con índice base=100, m/m, i.a.
- Reporting: `src/reporting/render.py` lee `exports/breakdown_<period>.csv` + `exports/series_cba.csv` y genera `reports/<period>.html` con:
  - KPIs: CBA (AE), CBA Hogar (×3,09), Índice, m/m, i.a.
  - Serie histórica (SVG). Si hay un solo punto, se oculta el gráfico y se muestra estado.
  - Dos vistas con toggle: Aporte% y Unitario (con órdenes por defecto y sort accesible en headers).
  - Tabla semántica (caption, th scope, aria-sort), filtros, paginación, “Mostrando X de Y”.
  - Panel “Metodología” y descargas (CSV breakdown, serie, diccionario, log de sustituciones si existe).

## Compatibilidad y salidas
- No se modifican rutas ni firmas públicas: la CLI (`src/cli.py`) sigue llamando `render_report(report_path, period, series_path, breakdown_path)` y genera:
  - `exports/series_cba.csv`
  - `exports/breakdown_<period>.csv`
  - `reports/<period>.html`
  - `evidence/<period>_<YYYY-MM-DD>/...`
- `src/reporting/render.py` también puede correrse de forma independiente para regenerar el HTML (ver `python -m src.reporting.render --period YYYY-MM`).

## Deudas técnicas detectadas y mejoras aplicadas
- Formato numérico: había formato estilo en-US (coma de miles) en varios lugares. Se unifica a es-AR (punto de miles, coma decimal) en servidor y en cliente (Intl.NumberFormat).
- KPIs m/m e i.a.: antes se mostraba “-” al faltar base; ahora se muestra “N/D” explícito y no se infiere 0,00%.
- Gráfico de serie: siempre renderizaba SVG; ahora se oculta con mensaje si hay < 2 puntos.
- Promociones: el render no debe inferir descuentos si la fuente no marca promo. Se muestra precio “Antes” sólo si `promo_flag == True` (evita casos 100% por faltantes/ruido).
- Accesibilidad: se agregan `<caption>`, `th scope="col"`, `aria-sort` con toggle de teclado; foco visible y header sticky.
- Ordenamiento y filtros: se reemplaza el ordenamiento ad‑hoc por headers clicables (con `aria-sort`) y búsqueda insensible a acentos; se añade paginación con estado “Mostrando X de Y”.
- Vistas: se incorporan dos vistas operativas con toggle y órdenes por defecto: Aporte% (desc) y Unitario (asc).
- Extras: detección de cambios de presentación (shrinkflation), resumen por categoría y top subas/bajas por unitario (con umbral anti‑ruido configurable).

## Supuestos matemáticos y ajustes (Laspeyres)
- Índice Laspeyres oficial: el archivo `exports/series_cba.csv` implementa de facto `I_t = 100 × CBA_AE_t / CBA_AE_base`, donde CBA_AE se computa como Σ(p_t × q0) con `q0 = monthly_qty_base` por ítem (AE) y `p_t` el precio por unidad normalizado. Es equivalente a Laspeyres con base fija.
- m/m: `(I_t / I_{t-1}) - 1`; i.a.: `(I_t / I_{t-12}) - 1`. Si falta base → `N/D`.
- Ajuste por tamaño (“shrinkflation”): los cálculos usan precio unitario (p/ kg/L/un), por lo que cambios en presentación no distorsionan el índice. Se marca `shrink_flag` cuando cambia significativamente `qty_base` vs. el mes previo (≥5%).
- Personalización de canasta: en el reporte se permite recalcular series personalizadas en el cliente usando `q0` (cantidades por AE) de la selección del usuario y `p_t` por unidad a lo largo de breakdowns históricos. La serie personalizada se grafica en paralelo a la oficial y no reemplaza el indicador.

## Oportunidades futuras
- Plantillas: existe `src/reporting/templates/monthly_report.html` como referencia, pero no hay motor de templates. Posibles opciones:
  - Adoptar Jinja2 y separar HTML, CSS y JS en archivos estáticos versionados.
  - Exportar un bundle `reports/assets/` para CSS/JS y minimizar.
- Tests de render: snapshot HTML + validaciones de a11y (axe-core vía Playwright) en CI.
- Internacionalización: permitir `locale` configurable para formatos.
- Theming: modo alto contraste e impresión (CSS print).
