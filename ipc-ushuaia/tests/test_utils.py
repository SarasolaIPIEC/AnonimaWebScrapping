import os
from pathlib import Path

import pytest

from scraper.utils import capture_evidence, save_html


class DummyPage:
    def content(self):
        return "<html></html>"

    def screenshot(self, path: str):
        Path(path).write_bytes(b"fake")


def test_capture_evidence(tmp_path):
    page = DummyPage()
    result = capture_evidence(page, "item", "run1", base_dir=tmp_path)
    assert result["html"].exists()
    assert result["screenshot"].exists()
    assert result["html"].parent == tmp_path / "run1"
    assert result["screenshot"].parent == tmp_path / "run1"


def test_save_html_run_id(tmp_path):
    path = save_html("<p>ok</p>", "test", base_dir=tmp_path, run_id="run2")
    assert path.exists()
    assert path.parent == tmp_path / "run2"
