from src.normalize.units import parse_title_size
from src.site.extract import parse_price_ar


def test_parse_price_ar():
    assert parse_price_ar("$ 1.234,56") == 1234.56
    assert parse_price_ar("$12,34") == 12.34
    assert parse_price_ar("sin precio") is None


def test_parse_title_size_basic():
    assert parse_title_size("Arroz 1 kg") == (1.0, 'kg')
    assert parse_title_size("Leche 900 ml") == (0.9, 'l')
    assert parse_title_size("Aceite 1.5 l") == (1.5, 'l')


def test_parse_title_size_packs_and_fracs():
    assert parse_title_size("Fideos x2 500 g") == (1.0, 'kg')
    assert parse_title_size("Carne 1/2 kg") == (0.5, 'kg')
    assert parse_title_size("Huevos docena") == (12.0, 'unit')

