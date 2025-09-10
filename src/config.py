from __future__ import annotations

"""Utility helpers for loading project configuration.

This module reads settings from a ``config.toml`` file and environment
variables defined in a ``.env`` file located at the project root.
"""

from dataclasses import dataclass
from pathlib import Path
import os
import tomllib


@dataclass
class Config:
    """Typed representation of the ``config.toml`` contents."""

    branch: str
    headless: bool
    delays: float
    retries: int
    base_period: str


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

    return Config(**data)


__all__ = ["Config", "load_config"]
