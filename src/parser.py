"""Parser de productos y mapeo a la CBA."""
from typing import Any, Dict, List, Optional

# TODO: Implementar extracción real desde HTML/JSON de La Anónima


def _final_unit_price(product: Dict[str, Any]) -> Optional[float]:
    """Devuelve el precio por unidad considerando promociones."""
    if product.get("unit_price") is not None:
        return product.get("unit_price")

    price = product.get("promo_price")
    if price is None:
        price = product.get("price")

    pack_size = product.get("pack_size")
    try:
        return price / float(pack_size) if price is not None and pack_size else None
    except (TypeError, ValueError):
        return None


def match_sku_to_cba(product: Dict[str, Any], cba_row: Dict[str, Any]) -> bool:
    """Heurística de matching por nombre, marca, tamaño y palabras clave."""
    name = product.get("name", "").lower()
    preferred = [k.strip() for k in cba_row.get("preferred_keywords", "").split(";")]
    fallback = [k.strip() for k in cba_row.get("fallback_keywords", "").split(";")]
    for kw in preferred:
        if kw and kw in name:
            return True
    for kw in fallback:
        if kw and kw in name:
            return True
    return False


def map_products_to_cba(products: List[Dict[str, Any]], cba_catalog: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Mapea productos scrapeados a los ítems de la CBA."""
    mapping: Dict[str, Dict[str, Any]] = {}
    for cba_row in cba_catalog:
        matches: List[Dict[str, Any]] = []
        for prod in products:
            if match_sku_to_cba(prod, cba_row):
                prod_copy = prod.copy()
                prod_copy["unit_price"] = _final_unit_price(prod_copy)
                matches.append(prod_copy)
        if matches:
            best = min(matches, key=lambda x: x.get("unit_price", float("inf")))
            mapping[cba_row["item"]] = {
                "sku": best.get("sku"),
                "price": best.get("unit_price"),
                "pack_size": best.get("pack_size"),
                "source": (
                    "preferred"
                    if any(
                        kw in best.get("name", "").lower()
                        for kw in cba_row.get("preferred_keywords", "").split(";")
                    )
                    else "fallback"
                ),
            }
        else:
            mapping[cba_row["item"]] = {
                "sku": None,
                "price": None,
                "pack_size": None,
                "source": "missing",
            }
    return mapping

# TODO: Documentar y testear reglas de sustitución y prorrateo
