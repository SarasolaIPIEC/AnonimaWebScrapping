"""Metadatos comunes para los reportes.

Centraliza valores reutilizables como la metodolog\u00eda, la fuente de precios y la versi\u00f3n del scraper.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

SCRAPER_VERSION = "0.1.0"

SUMMARY_METHODOLOGY = (
    "Canasta b\u00e1sica alimentaria fija; precios finales al consumidor; índice base 100 en el primer per\u00edodo."
)
SOURCE = "La An\u00f3nima Ushuaia"

def build_meta(run_id: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Construye un diccionario de metadatos comunes para los reportes.

    Parameters
    ----------
    run_id:
        Identificador de ejecuci\u00f3n del scraper.
    extra:
        Metadatos adicionales que pueden sobreescribir los predeterminados.

    Returns
    -------
    dict
        Diccionario con metadatos enriquecidos.
    """
    meta = {
        "methodology": SUMMARY_METHODOLOGY,
        "source": SOURCE,
        "scraper_version": SCRAPER_VERSION,
        "run_id": run_id,
    }
    if extra:
        meta.update(extra)
    return meta
