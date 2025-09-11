"""Helpers for scraper: capture HTML and screenshots as evidence."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4
from typing import Dict

from src.infra.logging import get_logger


logger = get_logger(__name__)


def _run_dir(base_dir: str | Path, run_id: str | None) -> Path:
    """Return the directory where evidence for ``run_id`` will be stored."""

    path = Path(base_dir)
    if run_id:
        path = path / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_html(
    content: str,
    prefix: str,
    *,
    base_dir: str = "data/evidence",
    run_id: str | None = None,
) -> Path:
    """Persist raw HTML for later auditing.

    Parameters
    ----------
    content:
        HTML content to save.
    prefix:
        Prefix for the generated file name.
    base_dir:
        Directory where files will be stored.
    run_id:
        Identifier for the current run. When provided, evidence is saved under
        ``<base_dir>/<run_id>/``.

    Returns
    -------
    pathlib.Path
        Path to the written file.
    """

    path = _run_dir(base_dir, run_id)
    file = path / f"{prefix}_{uuid4().hex}.html"
    file.write_text(content, encoding="utf-8")
    logger.info("Saved HTML evidence", extra={"path": str(file)})
    return file


def save_screenshot(
    page,
    prefix: str,
    *,
    base_dir: str = "data/evidence",
    run_id: str | None = None,
) -> Path:
    """Capture a screenshot from ``page`` and persist it.

    ``page`` is expected to provide a ``screenshot`` method compatible with
    ``playwright.sync_api.Page``.
    """

    path = _run_dir(base_dir, run_id)
    file = path / f"{prefix}_{uuid4().hex}.png"
    page.screenshot(path=str(file))
    logger.info("Saved screenshot evidence", extra={"path": str(file)})
    return file


def capture_evidence(
    page,
    prefix: str,
    run_id: str,
    *,
    base_dir: str = "data/evidence",
) -> Dict[str, Path]:
    """Save both HTML and a screenshot for the current ``page``.

    Returns a mapping with paths to the written files under keys ``html`` and
    ``screenshot``.
    """

    html_path = save_html(page.content(), prefix, base_dir=base_dir, run_id=run_id)
    shot_path = save_screenshot(page, prefix, base_dir=base_dir, run_id=run_id)
    return {"html": html_path, "screenshot": shot_path}


__all__ = ["save_html", "save_screenshot", "capture_evidence"]
