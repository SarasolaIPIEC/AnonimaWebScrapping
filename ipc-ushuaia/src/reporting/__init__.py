"""Utilidades para generar reportes HTML."""

from .render import render_monthly_report
from .meta import build_meta

__all__ = [
    "render_monthly_report",
    "plot_index_series",
    "plot_category_bars",
    "build_meta",
]

try:
    from .plots import plot_index_series, plot_category_bars
except ModuleNotFoundError:  # pragma: no cover - dependencias opcionales
    def plot_index_series(*args, **kwargs):  # type: ignore[override]
        raise RuntimeError("matplotlib es requerido para generar gr\u00e1ficos")

    def plot_category_bars(*args, **kwargs):  # type: ignore[override]
        raise RuntimeError("matplotlib es requerido para generar gr\u00e1ficos")
