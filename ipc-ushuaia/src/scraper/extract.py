"""Extracción y normalización de productos desde HTML."""

from __future__ import annotations

import re
from typing import Dict, List

from bs4 import BeautifulSoup

from .utils import save_html


def extract_product_cards(html: str) -> List[Dict]:
    """Parsea tarjetas de productos desde el HTML de resultados.

    Se busca un precio promocional (``ahora``) cuando esté disponible y se
    marca el producto como *out of stock* si corresponde.
    """

    try:
        soup = BeautifulSoup(html, "html.parser")
        cards = []
        for node in soup.select("[data-testid='product-card']"):
            name = node.select_one("[data-testid='product-name']").get_text(strip=True)

            price_now = node.select_one("[data-testid='price-now']")
            price_regular = node.select_one("[data-testid='price']")
            price_text = price_now.get_text(strip=True) if price_now else price_regular.get_text(strip=True)

            stock_flag = node.select_one("[data-testid='out-of-stock']") is not None

            raw = {"name": name, "price": price_text, "oos": stock_flag}
            cards.append(normalize_product(raw))
        return cards
    except Exception:
        save_html(html, "extract_error")
        raise


_PRICE_RE = re.compile(r"[0-9]+(?:[.,][0-9]+)?")


def normalize_product(raw: dict) -> dict:
    """Normaliza un producto crudo a un contrato estándar."""

    price_match = _PRICE_RE.search(raw["price"])
    price = float(price_match.group(0).replace(".", "").replace(",", ".")) if price_match else None

    return {
        "name": raw["name"],
        "price": price,
        "in_stock": not raw["oos"],
    }
