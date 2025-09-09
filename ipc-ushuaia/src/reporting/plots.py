"""Generación de gráficos para reportes HTML."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parents[2]
IMG_DIR = BASE_DIR / "reports" / "img"

# Estilo global para los gráficos
plt.style.use("seaborn-v0_8")


def plot_index_series(df_series: pd.DataFrame) -> Path:
    """Genera un gráfico de línea para la serie de índices.

    Parameters
    ----------
    df_series: pd.DataFrame
        Serie histórica con las columnas ``period`` e ``idx``.

    Returns
    -------
    Path
        Ruta al archivo PNG generado.
    """

    if "period" not in df_series or "idx" not in df_series:
        raise KeyError("df_series debe contener las columnas 'period' e 'idx'")

    period = df_series["period"].iloc[-1]
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    output_path = IMG_DIR / f"index_{period}.png"

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(df_series["period"], df_series["idx"], marker="o")
    ax.set_title("Índice CBA", fontsize=12)
    ax.set_xlabel("Período", fontsize=10)
    ax.set_ylabel("Índice (base=100)", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.5)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)

    return output_path


def plot_category_bars(df_breakdown: pd.DataFrame) -> Path:
    """Genera un gráfico de barras de variaciones por categoría.

    Parameters
    ----------
    df_breakdown: pd.DataFrame
        Desglose por categoría con las columnas ``period``, ``item`` (o ``category``)
        y ``delta``.

    Returns
    -------
    Path
        Ruta al archivo PNG generado.
    """

    if "period" not in df_breakdown:
        raise KeyError("df_breakdown debe contener la columna 'period'")

    label_col = "category" if "category" in df_breakdown.columns else "item"
    if label_col not in df_breakdown or "delta" not in df_breakdown:
        raise KeyError(
            "df_breakdown debe contener columnas 'item'/'category' y 'delta'"
        )

    period = df_breakdown["period"].iloc[0]
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    output_path = IMG_DIR / f"bars_{period}.png"

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(df_breakdown[label_col], df_breakdown["delta"], color="#1f77b4")
    ax.set_title("Variación por categoría", fontsize=12)
    ax.set_xlabel("Categoría", fontsize=10)
    ax.set_ylabel("Variación", fontsize=10)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)

    return output_path
