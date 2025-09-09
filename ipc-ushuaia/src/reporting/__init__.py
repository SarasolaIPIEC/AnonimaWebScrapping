"""Utilidades para generar reportes HTML."""

from .render import render_monthly_report
from .plots import plot_index_series, plot_category_bars

__all__ = [
    "render_monthly_report",
    "plot_index_series",
    "plot_category_bars",
]
