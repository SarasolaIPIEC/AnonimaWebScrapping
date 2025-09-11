from pathlib import Path

import pytest

import scraper.utils as utils
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


def test_random_delay(monkeypatch):
    called = {}

    def fake_uniform(a, b):
        return (a + b) / 2

    def fake_sleep(seconds):
        called["s"] = seconds

    monkeypatch.setattr(utils.random, "uniform", fake_uniform)
    monkeypatch.setattr(utils.time, "sleep", fake_sleep)
    utils.random_delay(0.1, 0.2)
    assert called["s"] == pytest.approx(0.15)


def test_is_allowed(monkeypatch):
    robots_txt = "User-agent: *\nDisallow: /nope"

    class Resp:
        status_code = 200
        text = robots_txt

    monkeypatch.setattr(utils.requests, "get", lambda *a, **k: Resp())
    utils._robots_parser.cache_clear()

    assert utils.is_allowed("https://example.com/ok", "bot")
    assert not utils.is_allowed("https://example.com/nope", "bot")
