from src.site.branch import detect_ushuaia_in_text


def test_detect_ushuaia_in_text_variants():
    assert detect_ushuaia_in_text("Ushuaia (Tierra del Fuego)") is True
    assert detect_ushuaia_in_text("CP 9410 - Disponibilidad") is True
    assert detect_ushuaia_in_text("Retirar gratis en la sucursal de: USHUAIA") is True
    assert detect_ushuaia_in_text("Rio Grande") is False

