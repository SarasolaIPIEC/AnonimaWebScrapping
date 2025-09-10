
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

