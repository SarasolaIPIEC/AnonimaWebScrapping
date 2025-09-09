"""Renderizado de reportes mensuales en HTML mediante Jinja2."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import pandas as pd
from jinja2 import Environment, FileSystemLoader

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = BASE_DIR / "templates"
REPORT_DIR = BASE_DIR / "reports"


def render_monthly_report(
    period: str,
    df_series: pd.DataFrame,
    df_breakdown: pd.DataFrame,
    img_paths: Dict[str, str],
    meta: Dict[str, Any],
) -> Path:
    """Genera un reporte mensual en HTML.

    Parameters
    ----------
    period:
        Período del reporte (``YYYY-MM``).
    df_series:
        Serie histórica con las columnas ``cba_ae``, ``cba_family``, ``idx``,
        ``mom`` e ``yoy``.
    df_breakdown:
        Desglose de variaciones por ítem.
    img_paths:
        Rutas a los gráficos a incrustar en el reporte.
    meta:
        Metadatos adicionales para el reporte.

    Returns
    -------
    Path
        Ruta al archivo HTML generado.
    """

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
    template = env.get_template("monthly_report.html")

    latest = df_series.iloc[-1]
    kpis = {
        "CBA AE": f"{latest['cba_ae']:.2f}",
        "CBA familia": f"{latest.get('cba_family', latest['cba_ae'] * 3.09):.2f}",
        "m/m": f"{latest.get('mom', 0.0):.2f}%",
        "i.a.": f"{latest.get('yoy', 0.0):.2f}%",
        "índice": f"{latest.get('idx', 0.0):.2f}",
    }

    breakdown = df_breakdown.to_dict(orient="records")

    html = template.render(
        period=period,
        kpis=kpis,
        img_paths=img_paths,
        breakdown=breakdown,
        meta=meta,
    )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORT_DIR / f"monthly_{period}.html"
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(html)

    # TODO: Integrar estilos y plantillas responsivas.
    # TODO: Revisar atributos de accesibilidad (ej. etiquetas ARIA).

    return output_path
