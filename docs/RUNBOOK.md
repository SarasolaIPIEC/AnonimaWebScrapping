
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

## Ejecución manual
Desde la raíz del paquete `ipc-ushuaia`:

```bash
python -m src.cli run
```

El comando dispara el flujo completo con la configuración por defecto. Se pueden añadir banderas como `--export csv` para definir el formato de salida o `--ae 3.09` para escalar la canasta.

## Dónde se almacenan los datos por `run_id`
- Base PostgreSQL: tablas `runs`, `prices`, `index_values` y `logs` enlazan cada registro con su `run_id`.
- Archivos en disco:
  - `ipc-ushuaia/data/raw/<run_id>/` guarda HTML y capturas originales.
  - `ipc-ushuaia/data/processed/<run_id>/` contiene datos normalizados.
- Salidas derivadas: `ipc-ushuaia/exports/` y `ipc-ushuaia/reports/` generan archivos etiquetados por período.

## Recuperación ante fallos
- Reintentar extracción por lotes.
- Usar HTML capturado para depurar selectores.
- Documentar cualquier ajuste metodológico.

## Reintentos idempotentes
1. Identificar el `run_id` a relanzar.
2. Limpiar artefactos previos:
   - `rm -rf ipc-ushuaia/data/raw/<run_id> ipc-ushuaia/data/processed/<run_id>` y borrar exports/reports asociados.
   - `psql $PGDATABASE -c "DELETE FROM runs WHERE id=<run_id>;"` (las tablas dependientes se eliminan por `ON DELETE CASCADE`).
3. Relanzar la corrida con `python -m src.cli run`.

## Ejecución en Windows
Ejemplo con Task Scheduler utilizando `schtasks`:

```bat
cd C:\\ruta\\al\\proyecto
schtasks /Create /SC DAILY /TN "IPC-Ushuaia" /TR "cmd /c cd %CD% && python ipc-ushuaia\\src\\cli.py --run --export csv >> ipc-ushuaia\\logs\\scheduler.log 2>&1" /ST 02:00
```

## Ejecución en Linux
Ejemplo de cron (`crontab -e`) con redirección de logs:

```bash
0 2 * * * cd /ruta/al/proyecto && /usr/bin/python3 ipc-ushuaia/src/cli.py --run --export csv >> ipc-ushuaia/logs/cron.log 2>&1
```

