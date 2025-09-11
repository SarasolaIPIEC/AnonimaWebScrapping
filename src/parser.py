"""Parser de productos y mapeo a la CBA."""
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

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


def match_sku_to_cba(
    product: Dict[str, Any], cba_row: Dict[str, Any], tolerance: float = 0.1
) -> Optional[Tuple[str, Optional[str]]]:
    """Heurística de matching por categoría, palabras clave y tamaño.

    Devuelve una tupla ``(source, reason)`` si matchea; en caso contrario, ``None``.
    ``source`` indica si se usó ``preferred`` o ``fallback``. ``reason`` documenta
    si se aceptó una diferencia de tamaño (``pack_size_diff``).
    """

    name = product.get("name", "").lower()
    prod_cat = product.get("category")
    cba_cat = cba_row.get("category")
    if cba_cat and prod_cat and cba_cat.lower() != prod_cat.lower():
        return None

    preferred = [k.strip() for k in cba_row.get("preferred_keywords", "").split(";")]
    fallback = [k.strip() for k in cba_row.get("fallback_keywords", "").split(";")]

    min_pack = cba_row.get("min_pack_size")
    pack_size = product.get("pack_size")
    reason: Optional[str] = None
    if min_pack is not None and pack_size is not None:
        try:
            min_pack_val = float(min_pack)
            pack_size_val = float(pack_size)
            if pack_size_val < min_pack_val * (1 - tolerance):
                return None
            if pack_size_val < min_pack_val:
                reason = "pack_size_diff"
        except (TypeError, ValueError):
            pass

    for kw in preferred:
        if kw and kw.lower() in name:
            return "preferred", reason
    for kw in fallback:
        if kw and kw.lower() in name:
            return "fallback", reason
    return None


def map_products_to_cba(
    products: List[Dict[str, Any]], cba_catalog: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """Mapea productos scrapeados a los ítems de la CBA."""

    mapping: Dict[str, Dict[str, Any]] = {}
    for cba_row in cba_catalog:
        matches: List[Dict[str, Any]] = []
        for prod in products:
            result = match_sku_to_cba(prod, cba_row)
            if result:
                source, reason = result
                prod_copy = prod.copy()
                prod_copy["unit_price"] = _final_unit_price(prod_copy)
                prod_copy["source"] = source
                if reason:
                    prod_copy["reason"] = reason
                matches.append(prod_copy)
        if matches:
            best = min(matches, key=lambda x: x.get("unit_price", float("inf")))
            item_data = {
                "sku": best.get("sku"),
                "price": best.get("unit_price"),
                "pack_size": best.get("pack_size"),
                "source": best.get("source"),
                "reason": best.get("reason"),
                "category": cba_row.get("category"),
            }
            if best.get("source") == "fallback" and not best.get("reason"):
                item_data["reason"] = "substitution"
            mapping[cba_row["item"]] = item_data
        else:
            mapping[cba_row["item"]] = {
                "sku": None,
                "price": None,
                "pack_size": None,
                "source": "missing",
                "reason": "OOS",
                "category": cba_row.get("category"),
            }
    return mapping


def save_evidence(
    mapping: Dict[str, Dict[str, Any]], output_dir: str = "data/evidence"
) -> None:
    """Guarda evidencia de hasta 3 ítems por categoría en archivos JSON."""

    os.makedirs(output_dir, exist_ok=True)
    per_cat: Dict[str, int] = {}
    for item, info in mapping.items():
        category = info.get("category", "sin_categoria")
        count = per_cat.get(category, 0)
        if count >= 3:
            continue
        filename = f"{category}_{item}.json"
        filename = re.sub(r"[^\w\-]+", "_", filename)
        path = os.path.join(output_dir, filename)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"item": item, **{k: v for k, v in info.items() if k != "category"}}, fh, ensure_ascii=False, indent=2)
        per_cat[category] = count + 1


# TODO: Documentar y testear reglas de sustitución y prorrateo
