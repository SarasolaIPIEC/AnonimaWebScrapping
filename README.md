# ipc-ushuaia â€” Ãndice CBA local (Ushuaia)

CLI E2E para: fijar sucursal por CP 9410 (USHUAIA 5), buscar CBA por barra, extraer precios finales (promos), normalizar unidades, calcular CBA AE y familia (Ã—3,09), mantener serie Ã­ndice base=100 y generar reporte HTML con evidencia.

## Requisitos
- Python 3.10+

## Setup rÃ¡pido (1 sola vez)
1. Instalar dependencias:
   - `pip install -r requirements.txt`
2. Instalar navegador para Playwright:
   - `python -m playwright install chromium`

## Uso

### Selección y verificación de sucursal

Antes de cualquier scraping, la app fija y verifica la sucursal de Ushuaia (CP 9410). Podés ejecutar solo ese paso y ver la evidencia:

```
python -m src.cli check-branch [--period YYYY-MM] [--zip 9410] [--branch "USHUAIA"] [--debug]
```

Genera en `evidence/<period>_<YYYY-MM-DD>/` los archivos:
- branch_before.png, branch_after.png
- branch_dom_after.html
- branch_storage.json
- branch_steps.jsonl (log estructurado)
- branch_check.log (resumen humano)

Flags/env soportados:
- `--zip` o env `ZIPCODE_DEFAULT` (default: 9410)
- `--branch` o env `BRANCH_TEXT_HINT` (default: "USHUAIA")

La verificación combina señales en header, una PDP de control y storage/cookies; si falla, termina con código ≠ 0.

### Uso mÃ­nimo
Ejecutar E2E (headless por defecto):

```
python -m src.cli run
```

Opciones Ãºtiles:
- `--period YYYY-MM` para fijar el perÃ­odo (por defecto: mes actual).
- `--branch "USHUAIA 5"` para forzar sucursal (por defecto: Ushuaia 5).
- `--debug` para ver el navegador y no cerrar al final.

### Modo con enlaces (pins)
Si tenÃ©s los links de cada producto, podÃ©s fijarlos y extraer solo precios:

1) EditÃ¡ `data/sku_pins.csv` y completÃ¡ la columna `url` para los `item_id` que tengas (pÃ¡gina de producto con sucursal Ushuaia). Los Ã­tems sin URL serÃ¡n omitidos.
2) EjecutÃ¡:

```
python -m src.cli pins-run --period YYYY-MM
```

Genera exports y reporte usando Ãºnicamente los pins (sin buscar por barra).

### Dry-run (sin red)
Usa un HTML guardado para probar parsing/normalizaciÃ³n:

```
python -m src.cli dry-run --period YYYY-MM --html path/to/file.html
```

## Estructura
- `src/cli.py`: CLI run/dry-run y orquestaciÃ³n.
- `src/site/branch.py`: selecciÃ³n de sucursal por CP 9410 â†’ "USHUAIA 5" con locators semÃ¡nticos.
- `src/site/search.py`: entrada de query por barra, captura de cards, ranking.
- `src/site/extract.py`: parse de tÃ­tulo, precio "Ahora", stock, url, promo.
- `src/site/product.py`: extracciÃ³n desde pÃ¡gina de producto (pins).
- `src/normalize/units.py`: regex y normalizaciÃ³n a kg/L/unidad.
- `src/normalize/pricing.py`: precio unitario y costo por AE.
- `src/metrics/cba.py`: CBA AE y familia (Ã—3,09).
- `src/metrics/index.py`: serie, base=100, m/m, i.a.
- `src/reporting/render.py`: reporte HTML con SVG simple del Ã­ndice.
- `config/selectors.json`: alternativas de selectores; se prueban en orden.
- `config.toml`: base_url, umbrales, rutas, exclusiones.
- `data/cba_catalog.csv`: catÃ¡logo mÃ­nimo (10â€“15 Ã­tems) con cantidades por AE.
- `evidence/<period>_<YYYY-MM-DD>/`: capturas y HTML de pasos crÃ­ticos por corrida (y logs JSONL).
- `exports/`: `series_cba.csv`, `breakdown_<period>.csv` y `daily_prices_<YYYY-MM-DD>.csv` (precios con fecha del dÃ­a).
- `data/sku_pins.csv`: mapeo persistente de Ã­tems â†’ SKU/URL elegidos.
- `reports/`: reporte HTML mensual.

## Notas metodolÃ³gicas
- Precio final al consumidor (si hay Antes/Ahora, usar **Ahora**).
- Canasta fija con sustituciones documentadas (se loguean en evidence JSONL).
- Unidades normalizadas a kg/L/unidad, docena=12.
- Tolerancias: 900 ml â‰ˆ 1 L; packs xN 500 g; 1/2 kg, 1/4 kg.

## Validaciones
- Header contiene â€œUshuaiaâ€ tras fijar sucursal.
- â‰¥ 80% de Ã­tems con precio vÃ¡lido (configurable).
- En caso de falla, `exit code != 0`.

## DÃ³nde ver lo generado
- Reporte HTML: `reports/<period>.html` (abre en el navegador)
- Serie: `exports/series_cba.csv`
- Desglose del perÃ­odo: `exports/breakdown_<period>.csv`
- Precios diarios: `exports/daily_prices_<YYYY-MM-DD>.csv`
- Evidencia y logs: `evidence/<period>_<YYYY-MM-DD>/`

## Optimizaciones de robustez
- Pins de SKU: se intenta primero `data/sku_pins.csv`; si falla, se recurre a bÃºsqueda y se actualizan pins.
- Scroll infinito/paginaciÃ³n: se intenta cargar mÃ¡s resultados de bÃºsqueda si aplica.
- Stock: se considera el botÃ³n â€œAgregar/Comprarâ€ ademÃ¡s de textos â€œSin stockâ€.
- Fecha local: CSV diario usa zona `America/Argentina/Ushuaia`.

## Resultados
Al finalizar un run verÃ¡s en consola un resumen y en disco:
- `exports/series_cba.csv`: serie mensual con Ã­ndice base=100, m/m e i.a.
- `exports/breakdown_<period>.csv`: desglose por Ã­tem con costo AE.
- `exports/daily_prices_<YYYY-MM-DD>.csv`: precios con fecha del dÃ­a (zona Ushuaia).
- `reports/<period>.html`: reporte HTML con KPIs y grÃ¡fico.
- `evidence/<period>_<YYYY-MM-DD>/`: capturas, HTML y `run_<period>.jsonl`.

## Reporte v2
- Descripción: reporte HTML accesible con dos vistas (Por producto y Por kg/L/un), ordenamiento con  `aria-sort`, filtros y paginación, formato es-AR, panel de Metodología y descargas (CSV serie/breakdown, diccionario, log de sustituciones). 
- Personalización  Mi canasta: permite incluir/excluir ítems, ajustar cantidades por AE y trazar una serie personalizada (no sustituye al indicador oficial). Exporta CSV/PNG.
- Índice: Laspeyres base=100 con cantidades fijas (q0 = `monthly_qty_base`). Encadenamiento automático cuando cambia `basket_version`.
- Render independiente (sin scraping):
  - `python -m src.cli render-report --period YYYY-MM`

## Desarrollo (opcional)
- Tests bÃ¡sicos (parsers):
  - `pip install -r requirements-dev.txt`
  - `pytest -q`
