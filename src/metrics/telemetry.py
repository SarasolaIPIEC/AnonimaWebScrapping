from __future__ import annotations

"""Utilities for recording run metrics.

This module tracks stage durations, out-of-stock (OOS) percentage and
error counts by type. Metrics can be persisted as CSV (default) or JSON
and are also logged using the project's JSON logger.
"""

from dataclasses import dataclass, field
import csv
import json
import time
from pathlib import Path
from typing import Dict, Optional

from infra.logging import get_logger


@dataclass
class Telemetry:
    """Collect and persist metrics for a single run.

    Parameters
    ----------
    run_id:
        Identifier of the current run. Used in output file names.
    output_dir:
        Directory where the telemetry files will be stored.
    output_format:
        Either ``"csv"`` or ``"json"``.
    """

    run_id: str
    output_dir: Path = Path("data/processed")
    output_format: str = "csv"
    logger_name: str = "telemetry"

    stages: Dict[str, float] = field(default_factory=dict)
    errors: Dict[str, int] = field(default_factory=dict)
    _stage_start: Optional[float] = field(default=None, init=False)
    _current_stage: Optional[str] = field(default=None, init=False)
    _total_items: int = field(default=0, init=False)
    _oos_items: int = field(default=0, init=False)

    def __post_init__(self) -> None:  # pragma: no cover - trivial
        self.logger = get_logger(self.logger_name)

    # Stage timing -----------------------------------------------------
    def start_stage(self, name: str) -> None:
        """Mark the beginning of a stage."""

        self._current_stage = name
        self._stage_start = time.perf_counter()
        self.logger.info(f"stage_start {name}")

    def end_stage(self, name: str) -> None:
        """Mark the end of a stage and record its duration."""

        if self._current_stage != name or self._stage_start is None:
            self.logger.error(f"stage_mismatch {name}")
            return
        elapsed = time.perf_counter() - self._stage_start
        self.stages[name] = elapsed
        self.logger.info(f"stage_end {name} {elapsed:.3f}s")
        self._current_stage = None
        self._stage_start = None

    # OOS percentage ---------------------------------------------------
    def record_oos(self, total_items: int, oos_items: int) -> None:
        """Record the number of total and out-of-stock items."""

        self._total_items += total_items
        self._oos_items += oos_items
        self.logger.info(
            "oos %s/%s => %.2f%%",
            oos_items,
            total_items,
            self.oos_percentage,
        )

    @property
    def oos_percentage(self) -> float:
        """Return the accumulated OOS percentage."""

        if self._total_items == 0:
            return 0.0
        return (self._oos_items / self._total_items) * 100

    # Error handling ---------------------------------------------------
    def increment_error(self, err_type: str) -> None:
        """Increment the count for ``err_type``."""

        self.errors[err_type] = self.errors.get(err_type, 0) + 1
        self.logger.info("error %s count=%d", err_type, self.errors[err_type])

    # Persistence ------------------------------------------------------
    def _as_dict(self) -> Dict[str, object]:
        return {
            "run_id": self.run_id,
            "stages": self.stages,
            "oos_pct": self.oos_percentage,
            "errors": self.errors,
        }

    def write(self) -> Path:
        """Persist metrics to disk and return the output path."""

        self.output_dir.mkdir(parents=True, exist_ok=True)
        data = self._as_dict()
        if self.output_format == "json":
            path = self.output_dir / f"telemetry_{self.run_id}.json"
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        else:
            path = self.output_dir / f"telemetry_{self.run_id}.csv"
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["metric", "key", "value"])
                for stage, duration in self.stages.items():
                    writer.writerow(["stage", stage, f"{duration:.3f}"])
                writer.writerow(["oos_pct", "", f"{self.oos_percentage:.2f}"])
                for err, count in self.errors.items():
                    writer.writerow(["error", err, count])
        self.logger.info("telemetry_written %s", path)
        return path


__all__ = ["Telemetry"]
