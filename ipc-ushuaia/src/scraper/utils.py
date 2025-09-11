"""Helpers for scraper: capture HTML and screenshots as evidence."""

from __future__ import annotations

import os
import random
import time
from functools import lru_cache
from pathlib import Path
from typing import Dict
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from uuid import uuid4

import requests

from src.infra.logging import get_logger


logger = get_logger(__name__)


@lru_cache(maxsize=32)
def _robots_parser(base_url: str, user_agent: str) -> RobotFileParser:
    """Return a parsed robots.txt for ``base_url``."""

    robots_url = urljoin(base_url, "/robots.txt")
    rp = RobotFileParser()
    try:
        resp = requests.get(robots_url, headers={"User-Agent": user_agent}, timeout=10)
        if resp.status_code == 200:
            rp.parse(resp.text.splitlines())
        else:
            rp.allow_all = True
    except Exception:
        rp.allow_all = True
    return rp


def is_allowed(url: str, user_agent: str) -> bool:
    """Return ``True`` if ``url`` is allowed for ``user_agent``."""

    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    rp = _robots_parser(base, user_agent)
    return rp.can_fetch(user_agent, parsed.path)


def random_delay(min_delay: float | None = None, max_delay: float | None = None) -> None:
    """Sleep for a random interval to reduce load on the server."""

    base = float(os.getenv("DELAYS", "0"))
    if min_delay is None or max_delay is None:
        if base <= 0:
            return
        min_delay = base
        max_delay = base * 2
    seconds = random.uniform(min_delay, max_delay)
    time.sleep(seconds)
    logger.info("Applied delay", extra={"seconds": round(seconds, 2)})


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


__all__ = [
    "save_html",
    "save_screenshot",
    "capture_evidence",
    "random_delay",
    "is_allowed",
]
