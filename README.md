# ipc-ushuaia — Índice CBA local (Ushuaia)

CLI E2E para: fijar sucursal por CP 9410 (USHUAIA 5), buscar CBA por barra, extraer precios finales (promos), normalizar unidades, calcular CBA AE y familia (×3,09), mantener serie índice base=100 y generar reporte HTML con evidencia.

## Requisitos
- Python 3.10+

## Setup rápido (1 sola vez)
1. Instalar dependencias:
   - `pip install -r requirements.txt`
2. Instalar navegador para Playwright:
   - `python -m playwright install chromium`

## Uso

### Uso mínimo
Ejecutar E2E (headless por defecto):

```
python -m src.cli run
```

Opciones útiles:
- `--period YYYY-MM` para fijar el período (por defecto: mes actual).
- `--branch "USHUAIA 5"` para forzar sucursal (por defecto: Ushuaia 5).
- `--debug` para ver el navegador y no cerrar al final.

### Modo con enlaces (pins)
Si tenés los links de cada producto, podés fijarlos y extraer solo precios:

1) Editá `data/sku_pins.csv` y completá la columna `url` para cada `item_id` (página de producto con sucursal Ushuaia).
2) Ejecutá:

```
python -m src.cli pins-run --period YYYY-MM
```

Genera exports y reporte usando únicamente los pins (sin buscar por barra).

### Dry-run (sin red)
Usa un HTML guardado para probar parsing/normalización:

```
python -m src.cli dry-run --period YYYY-MM --html path/to/file.html
```

## Estructura
- `src/cli.py`: CLI run/dry-run y orquestación.
- `src/site/branch.py`: selección de sucursal por CP 9410 → "USHUAIA 5" con locators semánticos.
- `src/site/search.py`: entrada de query por barra, captura de cards, ranking.
- `src/site/extract.py`: parse de título, precio "Ahora", stock, url, promo.
- `src/site/product.py`: extracción desde página de producto (pins).
- `src/normalize/units.py`: regex y normalización a kg/L/unidad.
- `src/normalize/pricing.py`: precio unitario y costo por AE.
- `src/metrics/cba.py`: CBA AE y familia (×3,09).
- `src/metrics/index.py`: serie, base=100, m/m, i.a.
- `src/reporting/render.py`: reporte HTML con SVG simple del índice.
- `config/selectors.json`: alternativas de selectores; se prueban en orden.
- `config.toml`: base_url, umbrales, rutas, exclusiones.
- `data/cba_catalog.csv`: catálogo mínimo (10–15 ítems) con cantidades por AE.
- `evidence/<period>_<YYYY-MM-DD>/`: capturas y HTML de pasos críticos por corrida (y logs JSONL).
- `exports/`: `series_cba.csv`, `breakdown_<period>.csv` y `daily_prices_<YYYY-MM-DD>.csv` (precios con fecha del día).
- `data/sku_pins.csv`: mapeo persistente de ítems → SKU/URL elegidos.
- `reports/`: reporte HTML mensual.

## Notas metodológicas
- Precio final al consumidor (si hay Antes/Ahora, usar **Ahora**).
- Canasta fija con sustituciones documentadas (se loguean en evidence JSONL).
- Unidades normalizadas a kg/L/unidad, docena=12.
- Tolerancias: 900 ml ≈ 1 L; packs xN 500 g; 1/2 kg, 1/4 kg.

## Validaciones
- Header contiene “Ushuaia” tras fijar sucursal.
- ≥ 80% de ítems con precio válido (configurable).
- En caso de falla, `exit code != 0`.

## Dónde ver lo generado
- Reporte HTML: `reports/<period>.html` (abre en el navegador)
- Serie: `exports/series_cba.csv`
- Desglose del período: `exports/breakdown_<period>.csv`
- Precios diarios: `exports/daily_prices_<YYYY-MM-DD>.csv`
- Evidencia y logs: `evidence/<period>_<YYYY-MM-DD>/`

## Optimizaciones de robustez
- Pins de SKU: se intenta primero `data/sku_pins.csv`; si falla, se recurre a búsqueda y se actualizan pins.
- Scroll infinito/paginación: se intenta cargar más resultados de búsqueda si aplica.
- Stock: se considera el botón “Agregar/Comprar” además de textos “Sin stock”.
- Fecha local: CSV diario usa zona `America/Argentina/Ushuaia`.

## Resultados
Al finalizar un run verás en consola un resumen y en disco:
- `exports/series_cba.csv`: serie mensual con índice base=100, m/m e i.a.
- `exports/breakdown_<period>.csv`: desglose por ítem con costo AE.
- `exports/daily_prices_<YYYY-MM-DD>.csv`: precios con fecha del día (zona Ushuaia).
- `reports/<period>.html`: reporte HTML con KPIs y gráfico.
- `evidence/<period>_<YYYY-MM-DD>/`: capturas, HTML y `run_<period>.jsonl`.

## Desarrollo (opcional)
- Tests básicos (parsers):
  - `pip install -r requirements-dev.txt`
  - `pytest -q`
