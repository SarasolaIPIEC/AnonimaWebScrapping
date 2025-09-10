from __future__ import annotations

"""Utility helpers for loading project configuration.

This module reads settings from a ``config.toml`` file and environment
variables defined in a ``.env`` file located at the project root.
"""

from dataclasses import dataclass
from pathlib import Path
import os
import tomllib
from typing import Iterable


def _str_to_bool(value: str) -> bool:
    """Return ``True`` if the string represents a truthy value."""

    return value.lower() in {"1", "true", "yes", "on"}


@dataclass
class Config:
    """Typed representation of the project configuration."""

    branch: str
    headless: bool
    delays: float
    max_retries: int
    user_agent: str
    output_dirs: list[Path]


def _load_env(path: Path) -> None:
    """Populate ``os.environ`` from a simple ``.env`` file if present."""

    if not path.exists():
        return

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def load_config(
    config_file: str = "config.toml", env_file: str = ".env"
) -> Config:
    """Load configuration and environment variables.

    Parameters
    ----------
    config_file: str
        Relative path to the TOML configuration file.
    env_file: str
        Relative path to the ``.env`` file.
    """

    root = Path(__file__).resolve().parent.parent
    config_path = root / config_file
    env_path = root / env_file

    _load_env(env_path)

    with config_path.open("rb") as f:
        data = tomllib.load(f)

    env = os.environ

    branch = env.get("BRANCH", data.get("branch", "main"))
    headless = _str_to_bool(env.get("HEADLESS", str(data.get("headless", True))))
    delays = float(env.get("DELAYS", data.get("delays", 0)))
    max_retries = int(env.get("MAX_RETRIES", data.get("max_retries", 0)))
    user_agent = env.get("USER_AGENT", data.get("user_agent", ""))

    if env.get("OUTPUT_DIRS"):
        output_dirs = [Path(p.strip()) for p in env["OUTPUT_DIRS"].split(",") if p.strip()]
    else:
        output_dirs = [Path(p) for p in data.get("output_dirs", [])]

    config = Config(
        branch=branch,
        headless=headless,
        delays=delays,
        max_retries=max_retries,
        user_agent=user_agent,
        output_dirs=output_dirs,
    )

    _ensure_playwright()
    _ensure_output_dirs(config.output_dirs)

    return config


def _ensure_playwright() -> None:
    """Verify that Playwright and the Chromium browser are installed."""

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
    except Exception as exc:  # pragma: no cover - best effort check
        raise RuntimeError(
            "Playwright Chromium browser is not installed. Run 'playwright install chromium'."
        ) from exc


def _ensure_output_dirs(dirs: Iterable[Path]) -> None:
    """Create output directories if they do not exist."""

    for path in dirs:
        path.mkdir(parents=True, exist_ok=True)


__all__ = ["Config", "load_config"]
