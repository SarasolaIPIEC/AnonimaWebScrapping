"""Demo para generar exportaciones y reporte mensual.

Las rutas de salida quedan documentadas y los archivos se materializan al
ejecutar este script para servir como referencia.

Archivos de referencia generados:
- ipc-ushuaia/exports/*.csv
- ipc-ushuaia/reports/*.html (con gráficos embebidos)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# Añade el paquete 'src' al path para las importaciones
ROOT_DIR = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT_DIR / "ipc-ushuaia"
sys.path.insert(0, str(PACKAGE_DIR))

from src.exporter import export_breakdown, export_series
from src.reporting.meta import build_meta
from src.reporting.plots import plot_category_bars, plot_index_series
from src.reporting.render import render_monthly_report

# Directorios documentados para las exportaciones
EXPORT_DIR = PACKAGE_DIR / "exports"
REPORT_DIR = PACKAGE_DIR / "reports"


def main() -> None:
    """Genera un reporte de demostración para un período ficticio."""

    period = "2024-12"

    series = pd.DataFrame(
        {
            "period": ["2024-11", period],
            "cba_ae": [100.0, 110.0],
        }
    )
    series["idx"] = (series["cba_ae"] / series["cba_ae"].iloc[0]) * 100
    breakdown = pd.DataFrame(
        {
            "period": [period, period],
            "category": ["demo1", "demo2"],
            "item": ["demo1", "demo2"],
            "cost": [50.0, 60.0],
            "delta": [1.5, -0.3],
        }
    )

    series_path = export_series(series)
    breakdown_path = export_breakdown(breakdown, period)
    idx_img = plot_index_series(series)
    bars_img = plot_category_bars(breakdown)

    render_monthly_report(
        period,
        series,
        breakdown,
        {"index": idx_img, "bars": bars_img},
        build_meta("demo"),
    )

    print(f"Serie histórica exportada a {series_path}")
    print(f"Desglose exportado a {breakdown_path}")
    print(f"Gráficos embebidos en el reporte")
    print(f"Reporte HTML generado en {REPORT_DIR}")


if __name__ == "__main__":  # pragma: no cover - ejemplo interactivo
    main()
