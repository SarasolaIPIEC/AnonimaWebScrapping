"""Cálculo del costo de la Canasta Básica Alimentaria (CBA)."""

import pandas as pd

__all__ = ["compute_cba_ae", "compute_cba"]


def compute_cba_ae(prices: pd.DataFrame, basket: pd.DataFrame) -> float:
    """Calcula el costo total de la CBA para un Adulto Equivalente.

    TODO: validar redondeos y actualizar ``docs/evidence/compute_cba_ae.md``.
    Evidencia: ``docs/evidence/compute_cba_ae.md``
    Export: ``exports/cba_ae.csv``
    """
    merged = pd.merge(basket, prices, on="sku", how="inner")
    merged["total"] = merged["quantity"] * merged["unit_price"]
    return merged["total"].sum()


def compute_cba(prices: pd.DataFrame, basket: pd.DataFrame) -> float:
    """Conveniencia que delega en :func:`compute_cba_ae`.

    TODO: consolidar metodología y dejar evidencia en ``docs/evidence/compute_cba.md``.
    Evidencia: ``docs/evidence/compute_cba.md``
    Export: ``exports/cba_series.csv``
    """
    return compute_cba_ae(prices, basket)
