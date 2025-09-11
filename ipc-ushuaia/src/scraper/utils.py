"""Helpers for scraper: saving HTML evidence on failures."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4


def save_html(content: str, prefix: str, *, base_dir: str = "data/evidence") -> Path:
    """Persist raw HTML for later auditing.

    Parameters
    ----------
    content:
        HTML content to save.
    prefix:
        Prefix for the generated file name.
    base_dir:
        Directory where files will be stored.

    Returns
    -------
    pathlib.Path
        Path to the written file.
    """
    path = Path(base_dir)
    path.mkdir(parents=True, exist_ok=True)
    file = path / f"{prefix}_{uuid4().hex}.html"
    file.write_text(content, encoding="utf-8")
    return file
