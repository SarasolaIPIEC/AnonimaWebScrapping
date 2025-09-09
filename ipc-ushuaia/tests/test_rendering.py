import pandas as pd
from pathlib import Path

from src.reporting.render import render_monthly_report


def test_render_monthly_report(tmp_path):
    period = "2024-01"
    series = pd.DataFrame({
        "period": ["2023-12", "2024-01"],
        "cba_ae": [100.0, 110.0],
    })
    series["cba_family"] = series["cba_ae"] * 3.09
    series["idx"] = (series["cba_ae"] / series["cba_ae"].iloc[0]) * 100
    series["mom"] = series["idx"].pct_change() * 100
    series["yoy"] = series["idx"].pct_change(12) * 100

    breakdown = pd.DataFrame({"item": ["A", "B"], "delta": [1.5, -0.5]})
    img_paths = {"index": "index.png"}

    output = render_monthly_report(period, series, breakdown, img_paths, meta={})
    assert output.exists()
    html = output.read_text(encoding="utf-8")
    assert "Indicadores Clave" in html
    assert "Top subas y bajas" in html
