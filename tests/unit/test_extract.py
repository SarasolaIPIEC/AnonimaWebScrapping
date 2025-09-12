import sys
from pathlib import Path

# Añade ruta al scraper dentro de ipc-ushuaia
sys.path.append(str(Path(__file__).resolve().parents[2] / "ipc-ushuaia" / "src"))

from scraper.extract import extract_product_cards


def test_extract_price_with_promo():
    html = """
    <div data-testid='product-card'>
      <div data-testid='product-name'>Promo Prod</div>
      <div class='precio-promo'>
        <div class='precio semibold'>$ 1.900</div>
        <div class='precio_complemento'><span class='decimales'>,00</span></div>
      </div>
      <div class='impuestos-nacionales'>IVA 21%</div>
    </div>
    """
    cards = extract_product_cards(html)
    assert cards[0]["price"] == 1900.00
    assert cards[0]["promo_flag"] is True
    assert cards[0]["impuestos_nacionales"] == "IVA 21%"
    assert cards[0]["in_stock"] is True


def test_extract_price_without_promo():
    html = """
    <div data-testid='product-card'>
      <div data-testid='product-name'>Regular Prod</div>
      <div class='precio'>$ 2.500</div>
      <div class='precio_complemento'><span class='decimales'>,50</span></div>
      <div class='impuestos-nacionales'>IVA 21%</div>
      <div data-testid='out-of-stock'></div>
    </div>
    """
    cards = extract_product_cards(html)
    assert cards[0]["price"] == 2500.50
    assert cards[0]["promo_flag"] is False
    assert cards[0]["impuestos_nacionales"] == "IVA 21%"
    assert cards[0]["in_stock"] is False
