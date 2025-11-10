"""HTML rendering helpers for IPC Ushuaia reports.

This module centralises data shaping for the monthly HTML report and keeps the
implementation ASCII-friendly.
"""
from __future__ import annotations

import csv
import html
import os
import re
import textwrap
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Set

from src.canasta_base import CANASTA_BASE, FAMILIA_AE, get_cantidad
from src.normalize.units import parse_title_size

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except Exception:  # pragma: no cover - optional dependency
    Environment = None
    FileSystemLoader = None
    select_autoescape = None


Row = Dict[str, Any]

__all__ = [
    "render_report",
    "load_data",
    "validate",
    "enrich",
    "build_context",
    "export_pdf",
]


@dataclass
class ValidationResult:
    rows: List[Row]
    warnings: List[str]


def _period_minus(period: str, months: int) -> str:
    year, month = period.split("-")
    total = int(year) * 12 + int(month) - 1 - months
    new_year, new_month = divmod(total, 12)
    return f"{new_year:04d}-{new_month + 1:02d}"


def _ensure_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("\xa0", "").replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y", "si", "s"}


def _normalize_brand(value: Any) -> str:
    if value is None:
        return "estandar"
    text = str(value).strip().lower()
    if text in {"premium", "estandar", "segunda"}:
        return text
    if "premium" in text:
        return "premium"
    if "segunda" in text or "econom" in text:
        return "segunda"
    return "estandar"


def _normalize_flag(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    if text in {"si", "s", "1", "true", "yes"}:
        return "si"
    if text in {"no", "n", "0", "false"}:
        return "no"
    return ""


def _read_csv(path: Path | str) -> List[Row]:
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_data(
    series_path: Path | str,
    breakdown_path: Path | str,
    period: str,
) -> Tuple[List[Row], List[Row], List[Row]]:
    """Return series, current breakdown and previous month breakdown rows."""
    series_rows = _read_csv(series_path)
    breakdown_rows = _read_csv(breakdown_path)
    prev_period = _period_minus(period, 1)
    breakdown_dir = Path(breakdown_path).resolve().parent
    prev_path = breakdown_dir / f"breakdown_{prev_period}.csv"
    prev_rows = _read_csv(prev_path)
    return series_rows, breakdown_rows, prev_rows


def _extract_quantity(row: Row, title: str) -> Tuple[Optional[float], str]:
    qty = _ensure_float(row.get("qty_base"))
    unit = str(row.get("unit") or "").strip().lower()
    if qty is None or not unit:
        parsed_qty, parsed_unit = parse_title_size(title)
        if qty is None:
            qty = parsed_qty
        if not unit:
            unit = parsed_unit
    return qty, unit


def _presentation(row: Row, qty: Optional[float], unit: str) -> str:
    for key in ("presentation_text", "presentation", "size_text"):
        val = row.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    if qty is None or not unit:
        return ""
    unit = unit.lower()
    if unit in {"unit", "un"}:
        return f"{qty:g} u"
    if unit == "kg":
        if qty < 1:
            return f"{qty * 1000:g} g"
        return f"{qty:g} kg"
    if unit == "l":
        if qty < 1:
            return f"{qty * 1000:g} ml"
        return f"{qty:g} l"
    return f"{qty:g} {unit}"


def _relative_link(origin: Path, target: Path) -> str:
    origin = origin.resolve()
    target = target.resolve()
    start = origin.parent if origin.is_file() else origin
    rel = os.path.relpath(target, start=start)
    return rel.replace(os.sep, "/")


def validate(rows: Sequence[Row]) -> ValidationResult:
    """Collect lightweight validation warnings without aborting the render."""
    warnings: List[str] = []
    clean_rows: List[Row] = []
    for row in rows:
        item_id = row.get("item_id") or "?"
        url = (row.get("url") or "").strip()
        price = _ensure_float(row.get("price_final"))
        if not url or "anonima" not in url.lower():
            warnings.append(f"item_id={item_id} no tiene URL valida de La Anonima")
        if price is None or price <= 0:
            warnings.append(f"item_id={item_id} tiene precio final no positivo")
        clean_rows.append(row)
    return ValidationResult(rows=list(clean_rows), warnings=warnings)


def enrich(rows: Sequence[Row], period: str, prev_rows: Sequence[Row]) -> List[Row]:
    """Normalise breakdown rows with unit prices, contributions and variations."""
    prev_map = {r.get("item_id"): r for r in prev_rows if r.get("item_id")}
    enriched: List[Row] = []
    for row in rows:
        item_id = row.get("item_id") or ""
        title = row.get("title") or row.get("name") or ""
        url = (row.get("url") or "").strip()
        category = (row.get("category") or "").strip().lower()
        brand = _normalize_brand(row.get("brand_tier"))
        flag = _normalize_flag(row.get("cba_flag"))
        in_stock = _boolish(row.get("in_stock", True))
        promo_flag = _boolish(row.get("promo_flag"))
        price_final = _ensure_float(row.get("price_final")) or 0.0
        price_original = _ensure_float(row.get("price_original"))
        if price_original is not None and price_original <= price_final:
            price_original = None
        qty_base, unit = _extract_quantity(row, title)
        qty_ae = _ensure_float(row.get("monthly_qty_base"))
        if qty_ae is None:
            qty_ae = get_cantidad(item_id, 1.0)
        unit_price = price_final / qty_base if qty_base else None
        cost_item_ae = _ensure_float(row.get("cost_item_ae"))
        if cost_item_ae is None and unit_price is not None and qty_ae:
            cost_item_ae = unit_price * qty_ae
        qty_family = get_cantidad(item_id, FAMILIA_AE)
        prev = prev_map.get(item_id)
        var_mom = None
        var_mom_unit = None
        if prev:
            prev_price = _ensure_float(prev.get("price_final"))
            prev_unit_price = _ensure_float(prev.get("unit_price_base"))
            if prev_price and price_final:
                var_mom = (price_final / prev_price - 1.0) * 100.0
            if prev_unit_price and unit_price:
                var_mom_unit = (unit_price / prev_unit_price - 1.0) * 100.0
        presentation = _presentation(row, qty_base, unit)
        base_unit = "un" if unit in {"unit", "un"} else unit
        enriched.append(
            {
                "period": period,
                "item_id": item_id,
                "title": title,
                "name": row.get("name") or title,
                "url": url,
                "category": category,
                "brand_tier": brand,
                "cba_flag": flag,
                "presentation_text": presentation,
                "base_equiv_value": qty_base or 0.0,
                "base_equiv_unit": base_unit or "",
                "price_final": price_final,
                "price_list": price_original,
                "promo_flag": promo_flag,
                "in_stock": in_stock,
                "unit_price": unit_price or 0.0,
                "unit_price_base": unit_price or 0.0,
                "qty_AE": qty_ae or 0.0,
                "qty_family": qty_family,
                "contrib_AE_money": cost_item_ae or 0.0,
                "contrib_AE_pct": 0.0,
                "variation_mom_pct": var_mom,
                "variation_yoy_pct": None,
                "variation_mom_unit_pct": var_mom_unit,
                "basket_version": row.get("basket_version") or "v1",
                "substitution": row.get("substitution", ""),
            }
        )
    total_cost = sum(r["contrib_AE_money"] for r in enriched)
    if total_cost > 0:
        for r in enriched:
            r["contrib_AE_pct"] = (r["contrib_AE_money"] / total_cost) * 100.0
    return enriched


def compute_kpis(period: str, series_rows: Sequence[Row], enriched_rows: Sequence[Row]) -> Dict[str, Any]:
    series_sorted = sorted(series_rows, key=lambda r: r.get("period", ""))
    latest = next((r for r in series_sorted if r.get("period") == period), series_sorted[-1] if series_sorted else {})
    cba_ae = _ensure_float(latest.get("cba_ae")) or sum(r.get("contrib_AE_money", 0.0) for r in enriched_rows)
    cba_family = _ensure_float(latest.get("cba_family")) or (cba_ae * FAMILIA_AE)
    idx = _ensure_float(latest.get("idx")) or 0.0
    mom = _ensure_float(latest.get("mom"))
    yoy = _ensure_float(latest.get("yoy"))
    total_items = len(enriched_rows)
    valid_items = sum(1 for r in enriched_rows if r.get("price_final", 0.0) > 0)
    promo_count = sum(1 for r in enriched_rows if r.get("price_list") and r.get("price_list") > r.get("price_final", 0.0))
    oos_count = sum(1 for r in enriched_rows if not r.get("in_stock"))
    total_cost = sum(r.get("contrib_AE_money", 0.0) for r in enriched_rows)
    summary = {
        "total_items": total_items,
        "valid_items": valid_items,
        "promo_count": promo_count,
        "oos_count": oos_count,
        "cba_ae_sum": total_cost,
        "valid_ratio": (valid_items / total_items) if total_items else 0.0,
    }
    return {
        "series_sorted": series_sorted,
        "kpis": {
            "cba_ae": cba_ae,
            "cba_family": cba_family,
            "idx": idx,
            "mom": mom,
            "yoy": yoy,
        },
        "summary": summary,
    }


def build_context(
    period: str,
    series_rows: Sequence[Row],
    enriched_rows: Sequence[Row],
    series_svg: str,
    warnings: Sequence[str],
) -> Dict[str, Any]:
    kpi_data = compute_kpis(period, series_rows, enriched_rows)
    categories = sorted({r["category"] for r in enriched_rows if r.get("category")})
    brand_tiers = ["premium", "estandar", "segunda"]
    view_a = sorted(enriched_rows, key=lambda r: r.get("contrib_AE_pct", 0.0), reverse=True)
    by_item: Dict[str, Row] = {}
    for row in enriched_rows:
        iid = row.get("item_id")
        if iid and iid not in by_item:
            by_item[iid] = row
    canasta_view: List[Dict[str, Any]] = []
    for entry in CANASTA_BASE:
        data = dict(entry)
        match = by_item.get(entry["item_id"])
        if match:
            data["url"] = match.get("url") or match.get("product_url")
            data["title"] = match.get("title") or match.get("name") or entry.get("nombre")
            data["category"] = match.get("category") or entry.get("categoria")
            data["price_final"] = match.get("price_final")
            data["in_stock"] = match.get("in_stock")
        else:
            data["title"] = entry.get("nombre")
            data["category"] = entry.get("categoria")
            data["url"] = ""
            data["price_final"] = None
            data["in_stock"] = None
        canasta_view.append(data)

    context = {
        "title": f"IPC Ushuaia - Reporte {period}",
        "header": "IPC Ushuaia - Canasta Basica Alimentaria",
        "period": period,
        "kpis": kpi_data["kpis"],
        "summary": {**kpi_data["summary"], "warnings": list(warnings)},
        "chart_index": series_svg,
        "viewA": view_a,
        "filters": {"categories": categories, "brand_tiers": brand_tiers},
        "links": {},
        "meta": {
            "source": "La Anonima Online",
            "branch": "Ushuaia 5",
            "tz": "America/Argentina/Ushuaia",
            "family_ae": FAMILIA_AE,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        },
        "canasta_base": CANASTA_BASE,
        "canasta_view": canasta_view,
        "series": kpi_data["series_sorted"],
    }
    if warnings:
        context["warnings"] = list(warnings)
    return context


def _fmt_currency(value: Any) -> str:
    val = _ensure_float(value)
    if val is None:
        val = 0.0
    formatted = f"{val:,.2f}"
    return "$" + formatted.replace(",", "_").replace(".", ",").replace("_", ".")


def _fmt_number(value: Any, digits: int = 2) -> str:
    val = _ensure_float(value)
    if val is None:
        val = 0.0
    formatted = f"{val:.{digits}f}".replace(".", ",")
    while formatted.endswith("0") and "," in formatted:
        formatted = formatted[:-1]
    if formatted.endswith(","):
        formatted = formatted[:-1]
    return formatted


def _fmt_pct(value: Any) -> str:
    val = _ensure_float(value)
    if val is None:
        return "N/D"
    return _fmt_number(val, digits=1) + "%"


def _build_jinja_env() -> Optional[Environment]:
    if Environment is None:
        return None
    template_dir = Path(__file__).resolve().parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.filters["currency"] = _fmt_currency
    env.filters["number"] = _fmt_number
    env.filters["pct"] = _fmt_pct
    return env


def _render_with_jinja(env: Environment, context: Dict[str, Any], out_path: Path) -> None:
    template = env.get_template("report.html")
    html_content = template.render(**context)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_content, encoding="utf-8")


def _write_by_category(base_dir: Path, period: str, rows: Sequence[Row]) -> None:
    if not rows:
        return
    base_dir.mkdir(parents=True, exist_ok=True)
    safe_pattern = re.compile(r"[^a-z0-9]+")
    fields = [
        "period",
        "item_id",
        "title",
        "url",
        "brand_tier",
        "cba_flag",
        "category",
        "price_final",
        "unit_price",
        "contrib_AE_money",
    ]
    buckets: Dict[str, List[Row]] = {}
    for row in rows:
        category = row.get("category") or "sin_categoria"
        slug = safe_pattern.sub("_", category.lower()).strip("_") or "sin_categoria"
        buckets.setdefault(slug, []).append(row)
    for slug, items in buckets.items():
        path = base_dir / f"{slug}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for item in items:
                writer.writerow(
                    {
                        "period": period,
                        "item_id": item.get("item_id"),
                        "title": item.get("title"),
                        "url": item.get("url"),
                        "brand_tier": item.get("brand_tier"),
                        "cba_flag": item.get("cba_flag"),
                        "category": item.get("category"),
                        "price_final": item.get("price_final"),
                        "unit_price": item.get("unit_price"),
                        "contrib_AE_money": item.get("contrib_AE_money"),
                    }
                )


def _svg_line(series: Sequence[Row], width: int = 960, height: int = 240, margin: int = 40) -> str:
    points = [
        (_ensure_float(row.get("idx")), row.get("period"))
        for row in series
        if _ensure_float(row.get("idx")) is not None
    ]
    if not points:
        return ""
    values = [value for value, _ in points if value is not None]
    min_y = min(values)
    max_y = max(values)
    if max_y == min_y:
        max_y += 1.0
    step = (width - 2 * margin) / max(1, len(points) - 1)
    coordinates: List[str] = []
    dots: List[str] = []
    labels: List[str] = []
    for index, (value, period_label) in enumerate(points):
        x = margin + index * step
        y = height - margin - (value - min_y) * (height - 2 * margin) / (max_y - min_y)
        coordinates.append(f"{x:.1f},{y:.1f}")
        dots.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='3' fill='#1976d2' />")
        labels.append(
            f"<text x='{x:.1f}' y='{y - 8:.1f}' font-size='10' text-anchor='middle' fill='#333'>{html.escape(period_label or '')}</text>"
        )
    return textwrap.dedent(
        f"""
        <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
          <rect x="0" y="0" width="{width}" height="{height}" fill="#fff" />
          <polyline fill="none" stroke="#1976d2" stroke-width="2" points="{' '.join(coordinates)}" />
          {' '.join(dots)}
          <line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{height - margin}" stroke="#bbb" stroke-width="1" />
          <line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" stroke="#bbb" stroke-width="1" />
          {' '.join(labels)}
        </svg>
        """
    ).strip()


def _legacy_report(context: Dict[str, Any], out_path: Path) -> None:
    rows_html = "".join(
        "<tr>"
        + f"<td><a href=\"{html.escape(row.get('url') or '')}\" target=\"_blank\">{html.escape(row.get('title') or '')}</a></td>"
        + f"<td>{html.escape(row.get('presentation_text') or '')}</td>"
        + f"<td>{_fmt_currency(row.get('price_final'))}</td>"
        + f"<td>{_fmt_currency(row.get('contrib_AE_money'))}</td>"
        + f"<td>{_fmt_pct(row.get('variation_mom_pct'))}</td>"
        + "</tr>"
        for row in context.get("viewA", [])
    )
    warnings_html = ""
    warnings = context.get("warnings") or []
    if warnings:
        items = "".join(f"<li>{html.escape(w)}</li>" for w in warnings)
        warnings_html = f"<section><h2>Advertencias</h2><ul>{items}</ul></section>"
    template = textwrap.dedent(
        f"""
        <!doctype html>
        <html lang="es">
        <head>
          <meta charset="utf-8"/>
          <title>{html.escape(context.get('title', 'IPC Ushuaia'))}</title>
          <style>
            body {{ font-family: Arial, sans-serif; margin: 24px; color: #0f172a; }}
            h1 {{ margin-bottom: 4px; }}
            .muted {{ color: #667085; font-size: 14px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
            th, td {{ border: 1px solid #e5e7eb; padding: 8px; text-align: left; }}
            th {{ background: #f3f4f6; }}
          </style>
        </head>
        <body>
          <h1>{html.escape(context.get('header', 'IPC Ushuaia - Canasta Basica Alimentaria'))}</h1>
          <div class="muted">Periodo {html.escape(context.get('period', ''))}</div>
          <section style="margin-top:16px;">
            <h2>Resumen</h2>
            <ul>
              <li>CBA AE: {_fmt_currency(context.get('kpis', {}).get('cba_ae'))}</li>
              <li>CBA Familia: {_fmt_currency(context.get('kpis', {}).get('cba_family'))}</li>
              <li>Indice: {_fmt_number(context.get('kpis', {}).get('idx'), digits=2)}</li>
              <li>m/m: {_fmt_pct(context.get('kpis', {}).get('mom'))}</li>
              <li>i.a.: {_fmt_pct(context.get('kpis', {}).get('yoy'))}</li>
            </ul>
          </section>
          {warnings_html}
          <section>
            <h2>Detalle por item</h2>
            <table>
              <thead>
                <tr><th>Item</th><th>Presentacion</th><th>Precio final</th><th>Contribucion AE</th><th>m/m</th></tr>
              </thead>
              <tbody>
                {rows_html}
              </tbody>
            </table>
          </section>
        </body>
        </html>
        """
    ).strip()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(template, encoding="utf-8")


def render_report(
    out_path: str | Path,
    period: str,
    series_path: str | Path,
    breakdown_path: str | Path,
    write_by_category: bool = False,
) -> None:
    out_path = Path(out_path)
    series_path = Path(series_path)
    breakdown_path = Path(breakdown_path)
    series_rows, breakdown_rows, prev_rows = load_data(series_path, breakdown_path, period)
    validation = validate(breakdown_rows)
    enriched = enrich(validation.rows, period, prev_rows)
    series_svg = _svg_line(sorted(series_rows, key=lambda r: r.get("period", "")))
    context = build_context(period, series_rows, enriched, series_svg, validation.warnings)
    context["links"]["breakdown"] = _relative_link(out_path, breakdown_path)
    context["links"]["series"] = _relative_link(out_path, series_path)
    env = _build_jinja_env()
    if env is not None:
        _render_with_jinja(env, context, out_path)
    else:
        _legacy_report(context, out_path)
    if write_by_category:
        _write_by_category(out_path.parent / "by_category", period, enriched)


def export_pdf(html_path: str | Path, pdf_path: str | Path) -> None:
    """Render a local HTML file to PDF using Playwright/Chromium."""
    from playwright.sync_api import sync_playwright  # type: ignore import-not-found

    html_path = Path(html_path).resolve()
    pdf_path = Path(pdf_path).resolve()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    file_url = "file://" + html_path.as_posix()
    playwright = sync_playwright().start()
    try:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(file_url, wait_until="load")
        page.pdf(path=str(pdf_path), format="A4", print_background=True)
        context.close()
        browser.close()
    finally:
        playwright.stop()
