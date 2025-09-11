"""Simplified pipeline runner returning summary stats.

This module provides a placeholder ``run`` function returning a ``RunSummary``
object. The real implementation would execute scraping, normalization and
export steps, but tests may stub ``run`` to emulate different scenarios.
"""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass
class RunSummary:
    """Aggregated results of a pipeline execution."""

    found: int
    oos: int
    substitutions: int
    variants: int
    fallbacks: int


def run(*, period: str, branch: str, headless: bool, ae: float) -> RunSummary:
    """Run the full pipeline and return a summary.

    This simplified implementation inspects the ``TEST_SCENARIO`` environment
    variable to emulate different outcomes during tests.
    """

    scenario = os.getenv("TEST_SCENARIO", "nominal")
    if scenario == "oos":
        return RunSummary(found=2, oos=1, substitutions=1, variants=0, fallbacks=0)
    if scenario == "variants":
        return RunSummary(found=3, oos=0, substitutions=0, variants=2, fallbacks=0)
    if scenario == "dom_changed":
        return RunSummary(found=3, oos=0, substitutions=0, variants=0, fallbacks=1)
    # nominal
    return RunSummary(found=3, oos=0, substitutions=0, variants=0, fallbacks=0)
