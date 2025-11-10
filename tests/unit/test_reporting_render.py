import os

from src.reporting import render as R


def test_currency_es_ar_basic():
    assert R._fmt_currency(1234.5) == "$1.234,50"
    assert R._fmt_currency(0) == "$0,00"


def test_number_and_pct_es_ar():
    assert R._fmt_number(0.473, digits=3) == "0,473"
    assert R._fmt_pct(12.34) == "12,3%"
    assert R._fmt_pct(None) == "N/D"


def test_enrich_unit_price_and_contrib_ordering(tmp_path):
    period = "2025-09"
    rows = [
        {"item_id": "a", "title": "Producto A 1 kg", "price_final": 1000, "qty_base": 1.0, "unit": "kg", "monthly_qty_base": 2.0, "cost_item_ae": 2000},
        {"item_id": "b", "title": "Producto B 500 g", "price_final": 400, "qty_base": 0.5, "unit": "kg", "monthly_qty_base": 1.0, "cost_item_ae": 800},
    ]
    enriched = R.enrich(rows, period, prev_rows=[])
    up = {r['item_id']: r['unit_price'] for r in enriched}
    assert up["a"] == 1000 / 1.0
    assert up["b"] == 400 / 0.5
    k = R.compute_kpis(period, [], enriched)
    assert k["summary"]["cba_ae_sum"] > 0
    ctx = R.build_context(period, [], enriched, series_svg="", warnings=[])
    contribs = [r['contrib_AE_pct'] for r in ctx['viewA']]
    assert contribs == sorted(contribs, reverse=True)


def test_pct_nd():
    assert R._fmt_pct('N/D') == 'N/D'
    assert R._fmt_pct('') == 'N/D'
