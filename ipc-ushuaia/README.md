# IPC Ushuaia

Índice local de precios estilo CBA a partir de La Anónima Online – Ushuaia.

## Objetivo
Sistema periódico que releva precios, normaliza unidades, calcula CBA por AE y familia tipo (3,09 AE), deriva un índice base=100 y exporta serie histórica y reportes.

## Estructura
- `src/`: código fuente
- `data/`: datos crudos y procesados
- `exports/`: salidas (CSV, HTML, JSON)
- `reports/`: reportes generados
- `docs/`: documentación técnica/metodológica
- `tests/`: pruebas

## Uso
La aplicación expone una interfaz de línea de comandos situada en
`src/cli.py`.  Los subcomandos disponibles son:

```
python ipc-ushuaia/src/cli.py run --period 2024-01 --branch ushuaia --headless
python ipc-ushuaia/src/cli.py dry-run --period 2024-01 --html-path ejemplo.html
python ipc-ushuaia/src/cli.py export-series --period 2024-01 --input exports/series_cba.csv
```

Argumentos principales:

- `--period` en formato `YYYY-MM` (validado).
- `--branch` sucursal de La Anónima; actualmente solo `ushuaia`.
- `--headless` ejecuta el navegador sin interfaz gráfica.

`export-series` permite reexportar la serie histórica en CSV/HTML a partir de
datos ya persistidos.
