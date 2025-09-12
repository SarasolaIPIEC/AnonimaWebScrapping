import sys
from pathlib import Path

import pandas as pd

# Añadir ruta al exporter dentro de ipc-ushuaia
sys.path.append(str(Path(__file__).resolve().parents[2] / "ipc-ushuaia" / "src"))

from exporter import export_products


def test_export_products(tmp_path):
    products = [
        {"name": "Pan", "price": 100.0, "promo_flag": True, "impuestos_nacionales": "IVA 21%"},
        {"name": "Leche", "price": 200.0, "promo_flag": False, "impuestos_nacionales": "IVA 21%"},
    ]
    out = tmp_path / "products.csv"
    export_products(products, str(out))
    assert out.exists()
    df = pd.read_csv(out)
    assert "promo_flag" in df.columns
    assert "impuestos_nacionales" in df.columns
