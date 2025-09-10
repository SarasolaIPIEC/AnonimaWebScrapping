from __future__ import annotations

import json
import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path


def _default_log_dir() -> Path:
    """Return a writable directory for log files.

    Uses the user's cache directory when available to avoid writing inside the
    package installation path.
    """

    if os.name == "nt":
        base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:  # POSIX
        base = Path(os.getenv("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / "anonima" / "logs"


# Default directory to store log files without creating it on import
LOG_DIR = _default_log_dir()


class JsonFormatter(logging.Formatter):
    """Formatter that outputs logs as JSON."""

    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover - trivial
        log_record = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        return json.dumps(log_record, ensure_ascii=False)


def _build_handler(
    log_path: Path,
    rotation: str,
    *,
    max_bytes: int,
    backup_count: int,
    when: str,
    interval: int,
) -> logging.Handler:
    """Create the appropriate rotating handler."""

    if rotation == "size":
        handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
    elif rotation == "time":
        handler = TimedRotatingFileHandler(
            log_path,
            when=when,
            interval=interval,
            backupCount=backup_count,
            encoding="utf-8",
        )
    else:  # pragma: no cover - defensive
        raise ValueError("rotation must be 'size' or 'time'")

    handler.setFormatter(JsonFormatter())
    return handler


def get_logger(
    name: str,
    *,
    log_file: str | Path | None = None,
    rotation: str = "size",
    max_bytes: int = 1_000_000,
    backup_count: int = 5,
    when: str = "midnight",
    interval: int = 1,
) -> logging.Logger:
    """Return a logger configured to emit JSON records.

    Parameters
    ----------
    name:
        Name of the logger to retrieve.
    log_file:
        Path to the log file. Defaults to ``<user-cache>/anonima/logs/<name>.log``.
    rotation:
        Either ``"size"`` or ``"time"`` to select the rotation strategy.
    max_bytes, backup_count, when, interval:
        Rotation parameters forwarded to the underlying handler.
    """

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    log_path = Path(log_file) if log_file else LOG_DIR / f"{name}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = _build_handler(
        log_path,
        rotation,
        max_bytes=max_bytes,
        backup_count=backup_count,
        when=when,
        interval=interval,
    )

    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


__all__ = ["get_logger"]
