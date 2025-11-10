import csv
from pathlib import Path

import pytest

from src.reporting.render import build_context, enrich, render_report, validate


def test_validate_collects_warnings():
    rows = [{"item_id": "demo", "url": "", "price_final": "0"}]
    result = validate(rows)
    assert len(result.warnings) == 2
    assert result.rows == rows


def test_enrich_computes_contributions():
    rows = [{
        "item_id": "arroz_1kg",
        "title": "Arroz 1 kg",
        "url": "https://www.laanonima.com.ar/p/arroz",
        "category": "almacen",
        "brand_tier": "premium",
        "cba_flag": "si",
        "price_final": "1000",
        "qty_base": "1",
        "unit": "kg",
        "monthly_qty_base": "2",
    }]
    enriched = enrich(rows, "2025-09", [])
    assert pytest.approx(enriched[0]["unit_price"]) == 1000.0
    assert pytest.approx(enriched[0]["contrib_AE_money"]) == 2000.0
    assert pytest.approx(enriched[0]["contrib_AE_pct"]) == 100.0


def test_build_context_includes_canasta_base():
    rows = [{
        "item_id": "arroz_1kg",
        "title": "Arroz 1 kg",
        "url": "https://www.laanonima.com.ar/p/arroz",
        "category": "almacen",
        "brand_tier": "estandar",
        "cba_flag": "si",
        "price_final": "1000",
        "qty_base": "1",
        "unit": "kg",
        "monthly_qty_base": "2",
    }]
    enriched = enrich(rows, "2025-09", [])
    series_rows = [{
        "period": "2025-09",
        "cba_ae": "2000",
        "cba_family": "6180",
        "idx": "110",
        "mom": "5",
        "yoy": "50",
    }]
    context = build_context("2025-09", series_rows, enriched, "<svg></svg>", ["warn"])
    assert context["canasta_base"]
    assert context["viewA"]
    assert context["summary"]["warnings"] == ["warn"]
    assert "<svg" in context["chart_index"]


def test_render_report_writes_html(tmp_path: Path):
    series_path = tmp_path / "series.csv"
    breakdown_path = tmp_path / "breakdown_2025-09.csv"
    html_path = tmp_path / "report.html"

    with series_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["period", "cba_ae", "cba_family", "idx", "mom", "yoy"])
        writer.writeheader()
        writer.writerow({
            "period": "2025-09",
            "cba_ae": "2000",
            "cba_family": "6180",
            "idx": "110",
            "mom": "5",
            "yoy": "50",
        })

    with breakdown_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "period",
            "item_id",
            "name",
            "query",
            "title",
            "url",
            "brand_tier",
            "cba_flag",
            "category",
            "in_stock",
            "promo_flag",
            "price_original",
            "price_promo",
            "price_final",
            "unit_price_base",
            "qty_base",
            "expected_qty",
            "cost_item_ae",
            "substitution",
            "unit",
            "monthly_qty_base",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({
            "period": "2025-09",
            "item_id": "arroz_1kg",
            "name": "Arroz 1 kg",
            "query": "arroz 1 kg",
            "title": "Arroz 1 kg",
            "url": "https://www.laanonima.com.ar/p/arroz",
            "brand_tier": "estandar",
            "cba_flag": "si",
            "category": "almacen",
            "in_stock": "1",
            "promo_flag": "0",
            "price_original": "0",
            "price_promo": "",
            "price_final": "1000",
            "unit_price_base": "1000",
            "qty_base": "1",
            "expected_qty": "1",
            "cost_item_ae": "",
            "substitution": "",
            "unit": "kg",
            "monthly_qty_base": "2",
        })

    render_report(html_path, "2025-09", series_path, breakdown_path)
    text = html_path.read_text(encoding="utf-8")
    assert "IPC Ushuaia" in text
    assert "Arroz 1 kg" in text
    assert "Aporte AE" in text
