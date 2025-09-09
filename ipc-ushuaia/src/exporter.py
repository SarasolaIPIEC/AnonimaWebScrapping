"""Exportador de datos a CSV, HTML y JSON.

Incluye utilidades para exportar la serie histórica y el desglose de la
canasta.  Todos los archivos se generan en ``exports/`` con codificación
UTF-8 y el separador estándar ``,``, lo que facilita el consumo desde
herramientas como Power BI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd


# Directorio base para las exportaciones
BASE_DIR = Path(__file__).resolve().parents[1]
EXPORT_DIR = BASE_DIR / "exports"


def _ensure_exports_dir() -> None:
    """Crea el directorio de exportaciones si no existe."""

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def export_to_csv(df: pd.DataFrame, path: str) -> None:
    """Exporta un :class:`~pandas.DataFrame` a CSV.

    Los archivos se guardan utilizando codificación UTF-8 y el separador
    `","` para asegurar compatibilidad con herramientas externas.
    """

    df.to_csv(path, index=False, encoding="utf-8", sep=",")


def export_to_json(df: pd.DataFrame, path: str) -> None:
    """Exporta un :class:`~pandas.DataFrame` a JSON UTF-8."""

    with open(path, "w", encoding="utf-8") as fh:
        df.to_json(fh, orient="records", force_ascii=False)


def export_to_html(df: pd.DataFrame, path: str) -> None:
    """Exporta un :class:`~pandas.DataFrame` a HTML UTF-8."""

    with open(path, "w", encoding="utf-8") as fh:
        df.to_html(fh, index=False)


def export_series(df: pd.DataFrame, output: Optional[str] = None) -> Path:
    """Exporta la serie histórica de la CBA.

    Parameters
    ----------
    df:
        DataFrame con al menos las columnas ``period`` y ``cba_ae``.
    output:
        Ruta opcional de salida.  Por defecto se utiliza
        ``exports/series_cba.csv``.

    Returns
    -------
    Path
        Ruta al archivo generado.
    """

    _ensure_exports_dir()
    output_path = Path(output) if output else EXPORT_DIR / "series_cba.csv"

    series = df.copy()
    # Costo de la canasta para una familia tipo (3,09 AE)
    if "cba_family" not in series.columns:
        series["cba_family"] = series["cba_ae"] * 3.09

    # Índice base 100 en el primer período
    base_value = series["cba_ae"].iloc[0]
    series["idx"] = (series["cba_ae"] / base_value) * 100
    series["mom"] = series["idx"].pct_change() * 100
    series["yoy"] = series["idx"].pct_change(12) * 100

    export_df = series[["period", "cba_ae", "cba_family", "idx", "mom", "yoy"]]
    export_to_csv(export_df, str(output_path))
    return output_path


def export_breakdown(df: pd.DataFrame, period: str, output: Optional[str] = None) -> Path:
    """Exporta el desglose de costos por rubro/ítem para un período dado.

    Parameters
    ----------
    df:
        DataFrame con las columnas ``period``, ``category``, ``item`` y
        ``cost`` (costo del ítem en el período).
    period:
        Período a exportar (formato libre, p.ej. ``"2024-01"``).
    output:
        Ruta opcional de salida.  Por defecto se genera un archivo llamado
        ``exports/breakdown_<period>.csv``.

    Returns
    -------
    Path
        Ruta al archivo generado.
    """

    _ensure_exports_dir()
    output_path = (
        Path(output)
        if output
        else EXPORT_DIR / f"breakdown_{period}.csv"
    )

    filtered = df[df["period"] == period]
    breakdown = (
        filtered.groupby(["category", "item"])["cost"].sum().reset_index()
    )

    export_to_csv(breakdown, str(output_path))
    return output_path


# TODO: Integrar con index_engine.py y report.py para automatizar salidas
