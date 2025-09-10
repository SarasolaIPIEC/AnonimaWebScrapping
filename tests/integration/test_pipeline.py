import csv
from pathlib import Path
from typing import List, Dict, Any

import requests
import responses
from bs4 import BeautifulSoup

from src import parser, normalizer
from tests.fixtures import html_fixture, csv_fixture

EXPECTED_DIR = Path(__file__).resolve().parents[1] / "expected"


def _parse_html_products(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    products = []
    for div in soup.select("div.product"):
        name = div.select_one(".product-name").get_text(strip=True)
        sku = div["data-sku"]
        price = float(div.select_one(".product-price").get_text(strip=True).replace("$", ""))
        promo_tag = div.select_one(".product-promo")
        promo_price = (
            float(promo_tag.get_text(strip=True).replace("$", ""))
            if promo_tag else None
        )
        pack_text = div.select_one(".product-pack").get_text(strip=True)
        pack_size = float(pack_text.split()[0].replace(",", "."))
        products.append({
            "name": name,
            "sku": sku,
            "price": price,
            "promo_price": promo_price,
            "pack_size": pack_size,
        })
    return products


def _write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@responses.activate
def test_full_pipeline(tmp_path: Path) -> None:
    url = "https://la-anonima.test/products"
    responses.get(url, body=html_fixture(), content_type="text/html; charset=utf-8")
    html = requests.get(url).text
    products = _parse_html_products(html)

    products_csv = tmp_path / "products.csv"
    _write_csv(products_csv, products, ["name", "sku", "price", "promo_price", "pack_size"])
    assert _read_csv(products_csv) == _read_csv(EXPECTED_DIR / "products.csv")

    cba_catalog = normalizer.load_cba_catalog(str(csv_fixture()))
    mapping = parser.map_products_to_cba(products, cba_catalog)
    adjusted = normalizer.adjust_quantities(cba_catalog, ae_multiplier=1.0)

    rows = []
    for row in adjusted:
        info = mapping[row["item"]]
        rows.append({
            "item": row["item"],
            "sku": info["sku"],
            "price": f"{info['price']:.1f}" if info["price"] is not None else "",
            "pack_size": str(int(info["pack_size"])) if info["pack_size"] is not None else "",
            "source": info["source"],
            "adjusted_qty": f"{row['adjusted_qty']:.1f}" if row["adjusted_qty"] is not None else "",
        })

    output_csv = tmp_path / "cba_prices.csv"
    _write_csv(output_csv, rows, ["item", "sku", "price", "pack_size", "source", "adjusted_qty"])
    assert _read_csv(output_csv) == _read_csv(EXPECTED_DIR / "cba_prices.csv")
