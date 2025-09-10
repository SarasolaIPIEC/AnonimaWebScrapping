"""Pruebas para decoradores de retry y checkpoints."""

import pytest

from src.infra.retry import (
    CircuitBreakerOpen,
    circuit_breaker,
    exponential_backoff,
    load_checkpoint,
    save_checkpoint,
)


def test_exponential_backoff_success():
    calls = {"n": 0}

    @exponential_backoff(max_attempts=3, base_delay=0, sleep=lambda _: None)
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ValueError("fail")
        return "ok"

    assert flaky() == "ok"
    assert calls["n"] == 3


def test_circuit_breaker_opens_and_resets():
    current = {"t": 0.0}

    def clock() -> float:
        return current["t"]

    @circuit_breaker(max_failures=2, reset_timeout=10, clock=clock)
    def always_fail():
        raise ValueError("boom")

    with pytest.raises(ValueError):
        always_fail()
    with pytest.raises(ValueError):
        always_fail()
    with pytest.raises(CircuitBreakerOpen):
        always_fail()

    current["t"] += 10
    with pytest.raises(ValueError):
        always_fail()


def test_checkpoint_roundtrip(tmp_path):
    base = tmp_path / "data" / "raw"
    save_checkpoint("run123", "step1", {"extra": 42}, base_dir=base)
    data = load_checkpoint("run123", base_dir=base)
    assert data == {"step": "step1", "extra": 42}
