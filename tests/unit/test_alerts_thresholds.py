from pathlib import Path

import pytest

import src.alerts as alerts


def test_enforce_thresholds_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(alerts, "evidence_dir", tmp_path)
    items = {
        "a": {"price": 10},
        "b": {"price": None},
    }
    flag = tmp_path / "flag.txt"
    with pytest.raises(SystemExit):
        alerts.enforce_thresholds(items, {}, min_valid_items=2, variation_tolerance=5, flag_file=flag)
    assert flag.exists()


def test_enforce_thresholds_insufficient(tmp_path, monkeypatch):
    monkeypatch.setattr(alerts, "evidence_dir", tmp_path)
    items = {
        "a": {"price": 10},
        "b": {"price": 20},
    }
    flag = tmp_path / "flag.txt"
    with pytest.raises(SystemExit):
        alerts.enforce_thresholds(items, {}, min_valid_items=3, variation_tolerance=5, flag_file=flag)
    assert flag.exists()


def test_enforce_thresholds_variation(tmp_path, monkeypatch):
    monkeypatch.setattr(alerts, "evidence_dir", tmp_path)
    items = {
        "a": {"price": 10},
        "b": {"price": 20},
    }
    flag = tmp_path / "flag.txt"
    with pytest.raises(SystemExit):
        alerts.enforce_thresholds(items, {"foo": 12}, min_valid_items=2, variation_tolerance=10, flag_file=flag)
    assert flag.exists()


def test_enforce_thresholds_ok(tmp_path, monkeypatch):
    monkeypatch.setattr(alerts, "evidence_dir", tmp_path)
    items = {
        "a": {"price": 10},
        "b": {"price": 20},
    }
    variations = {"foo": 1.0}
    flag = tmp_path / "flag.txt"
    alerts.enforce_thresholds(items, variations, min_valid_items=2, variation_tolerance=5, flag_file=flag)
    assert not flag.exists()
