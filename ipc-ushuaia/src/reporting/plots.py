"""Generación de gráficos para reportes HTML sin archivos intermedios."""

from __future__ import annotations

from io import BytesIO
import base64

import matplotlib.pyplot as plt
import pandas as pd

# Estilo global para los gráficos
plt.style.use("seaborn-v0_8")


def _fig_to_data_uri(fig) -> str:
    """Convierte una figura de matplotlib en un data URI PNG."""

    buffer = BytesIO()
    fig.savefig(buffer, format="png")
    plt.close(fig)
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def plot_index_series(df_series: pd.DataFrame) -> str:
    """Genera un gráfico de línea para la serie de índices.

    Parameters
    ----------
    df_series: pd.DataFrame
        Serie histórica con las columnas ``period`` e ``idx``.

    Returns
    -------
    str
        Data URI listo para incrustar en HTML.
    """

    if "period" not in df_series or "idx" not in df_series:
        raise KeyError("df_series debe contener las columnas 'period' e 'idx'")

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(df_series["period"], df_series["idx"], marker="o")
    ax.set_title("Índice CBA", fontsize=12)
    ax.set_xlabel("Período", fontsize=10)
    ax.set_ylabel("Índice (base=100)", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.5)
    fig.tight_layout()

    return _fig_to_data_uri(fig)


def plot_category_bars(df_breakdown: pd.DataFrame) -> str:
    """Genera un gráfico de barras de variaciones por categoría.

    Parameters
    ----------
    df_breakdown: pd.DataFrame
        Desglose por categoría con las columnas ``period``, ``item`` (o ``category``)
        y ``delta``.

    Returns
    -------
    str
        Data URI listo para incrustar en HTML.
    """

    if "period" not in df_breakdown:
        raise KeyError("df_breakdown debe contener la columna 'period'")

    label_col = "category" if "category" in df_breakdown.columns else "item"
    if label_col not in df_breakdown or "delta" not in df_breakdown:
        raise KeyError(
            "df_breakdown debe contener columnas 'item'/'category' y 'delta'"
        )

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(df_breakdown[label_col], df_breakdown["delta"], color="#1f77b4")
    ax.set_title("Variación por categoría", fontsize=12)
    ax.set_xlabel("Categoría", fontsize=10)
    ax.set_ylabel("Variación", fontsize=10)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()

    return _fig_to_data_uri(fig)
