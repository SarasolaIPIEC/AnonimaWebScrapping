"""Extracción y normalización de productos desde HTML."""

from __future__ import annotations

from typing import Dict, List

from bs4 import BeautifulSoup

from .utils import save_html

__all__ = ["extract_product_cards", "normalize_product"]


def extract_product_cards(html: str) -> List[Dict]:
    """Parsea tarjetas de productos desde el HTML de resultados.

    TODO: documentar cambios de selectores en ``docs/evidence/extract_cards.md``.
    Evidencia: ``docs/evidence/extract_cards.md``
    Export: ``exports/raw_cards.json``

    Se busca un precio promocional (``ahora``) cuando esté disponible y se
    marca el producto como *out of stock* si corresponde.
    """

    try:
        soup = BeautifulSoup(html, "html.parser")
        cards = []
        for node in soup.select("[data-testid='product-card']"):
            name = node.select_one("[data-testid='product-name']").get_text(strip=True)

            impuestos_node = node.select_one("div.impuestos-nacionales")
            impuestos_txt = impuestos_node.get_text(strip=True) if impuestos_node else ""

            promo_container = node.select_one("div.precio-promo")
            if promo_container:
                price_node = promo_container.select_one("div.precio.semibold")
                dec_node = promo_container.select_one("span.decimales")
                promo_flag = True
            else:
                price_node = node.select_one("div.precio")
                dec_node = node.select_one("div.precio_complemento span.decimales") or node.select_one(
                    "span.decimales"
                )
                promo_flag = False

            price_int = price_node.get_text(strip=True) if price_node else ""
            decimals = dec_node.get_text(strip=True) if dec_node else ""
            price_text = f"{price_int}{decimals}"

            stock_flag = node.select_one("[data-testid='out-of-stock']") is not None

            raw = {
                "name": name,
                "price": price_text,
                "oos": stock_flag,
                "promo_flag": promo_flag,
                "impuestos_nacionales": impuestos_txt,
            }
            cards.append(normalize_product(raw))
        return cards
    except Exception:
        save_html(html, "extract_error")
        raise


def normalize_product(raw: dict) -> dict:
    """Normaliza un producto crudo a un contrato estándar.

    TODO: estandarizar unidades y registrar notas en
    ``docs/evidence/normalize_product.md``.
    Export: ``exports/normalized_products.json``
    """

    price_raw = (raw.get("price") or "").replace("$", "").replace(" ", "")
    try:
        price = float(price_raw.replace(".", "").replace(",", ".")) if price_raw else None
    except ValueError:
        price = None

    return {
        "name": raw["name"],
        "price": price,
        "in_stock": not raw["oos"],
        "promo_flag": raw.get("promo_flag", False),
        "impuestos_nacionales": raw.get("impuestos_nacionales", ""),
    }
