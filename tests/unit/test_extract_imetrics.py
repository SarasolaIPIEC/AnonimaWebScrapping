import sys
from pathlib import Path

# Añade ruta al scraper dentro de ipc-ushuaia
sys.path.append(str(Path(__file__).resolve().parents[2] / "ipc-ushuaia" / "src"))

from scraper.extract import extract_product_cards_imetrics


def test_extract_imetrics_with_offer_and_stock():
    html = """
    <div class="producto item">
      <a id="btn_nombre_imetrics_1" href="http://example.com/a">Producto A</a>
      <input type="hidden" id="precio_item_imetrics_1" value="1200,00" />
      <input type="hidden" id="precio_oferta_item_imetrics_1" value="1000,00" />
      <input type="hidden" id="brand_item_imetrics_1" value="MarcaA" />
      <input type="hidden" id="sku_item_imetrics_1" value="SKU1" />
      <div class="btnagregarcarritosinstock_1" style="display:none;"></div>
    </div>
    """
    cards = extract_product_cards_imetrics(html)
    assert cards[0] == {
        "sku": "SKU1",
        "nombre": "Producto A",
        "marca": "MarcaA",
        "url": "http://example.com/a",
        "precio_final": 1000.0,
        "promo_flag": True,
        "in_stock": True,
    }


def test_extract_imetrics_without_offer_oos():
    html = """
    <div class="producto item">
      <a id="btn_nombre_imetrics_2" href="http://example.com/b">Producto B</a>
      <input type="hidden" id="precio_item_imetrics_2" value="1500,50" />
      <input type="hidden" id="brand_item_imetrics_2" value="MarcaB" />
      <input type="hidden" id="sku_item_imetrics_2" value="SKU2" />
      <div class="btnagregarcarritosinstock_2"></div>
    </div>
    """
    cards = extract_product_cards_imetrics(html)
    assert cards[0] == {
        "sku": "SKU2",
        "nombre": "Producto B",
        "marca": "MarcaB",
        "url": "http://example.com/b",
        "precio_final": 1500.50,
        "promo_flag": False,
        "in_stock": False,
    }

