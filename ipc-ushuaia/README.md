# IPC Ushuaia

Ãndice local de precios estilo CBA a partir de La AnÃ³nima Online â€“ Ushuaia.

## Objetivo
Sistema periÃ³dico que releva precios, normaliza unidades, calcula CBA por AE y familia tipo (3,09 AE), deriva un Ã­ndice base=100 y exporta serie histÃ³rica y reportes.

## Estructura
- `src/`: cÃ³digo fuente
- `data/`: datos crudos y procesados
- `exports/`: salidas (CSV, HTML, JSON)
- `reports/`: reportes generados
- `docs/`: documentaciÃ³n tÃ©cnica/metodolÃ³gica
- `tests/`: pruebas

## Uso (simplificado)

Ejecutar con valores por defecto (mes actual y sucursal Ushuaia):

```
python -m src.cli run
```

Opciones útiles:

- `--period YYYY-MM` para setear el período (por defecto: mes actual)
- `--branch ushuaia` para forzar sucursal (por defecto: ushuaia)
- `--headless` para correr sin UI

Otros subcomandos:

```
python -m src.cli dry-run --html-path ejemplo.html
python -m src.cli export-series --input exports/series_cba.csv
```

`export-series` reexporta la serie en CSV/HTML a partir de datos ya persistidos.
