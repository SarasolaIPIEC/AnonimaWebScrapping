from __future__ import annotations

import functools
import json
import time
from pathlib import Path
from typing import Any, Callable, TypeVar, cast


F = TypeVar("F", bound=Callable[..., Any])


class CircuitBreakerOpen(RuntimeError):
    """Se lanza cuando el circuito está abierto y se bloquean las llamadas."""


def exponential_backoff(
    *,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    sleep: Callable[[float], None] = time.sleep,
) -> Callable[[F], F]:
    """Decorar una función para reintentos con backoff exponencial."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            delay = base_delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if attempt == max_attempts:
                        raise
                    sleep(delay)
                    delay *= factor
        return cast(F, wrapper)

    return decorator


def circuit_breaker(
    *,
    max_failures: int = 5,
    reset_timeout: float = 60.0,
    clock: Callable[[], float] = time.monotonic,
) -> Callable[[F], F]:
    """Decorar una función con lógica de *circuit breaker*."""

    def decorator(func: F) -> F:
        failures = 0
        opened_at: float | None = None

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            nonlocal failures, opened_at
            now = clock()
            if opened_at is not None and now - opened_at >= reset_timeout:
                failures = 0
                opened_at = None

            if failures >= max_failures:
                raise CircuitBreakerOpen(f"Circuito abierto tras {failures} fallas")

            try:
                result = func(*args, **kwargs)
                failures = 0
                opened_at = None
                return result
            except Exception:
                failures += 1
                if failures >= max_failures:
                    opened_at = now
                raise

        return cast(F, wrapper)

    return decorator


def save_checkpoint(
    run_id: str,
    step: str,
    data: dict[str, Any] | None = None,
    *,
    base_dir: str | Path = Path("data/raw"),
) -> None:
    """Persistir un checkpoint para un ``run_id``."""

    path = Path(base_dir) / run_id
    path.mkdir(parents=True, exist_ok=True)
    payload = {"step": step, **(data or {})}
    with (path / "checkpoint.json").open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False)


def load_checkpoint(
    run_id: str,
    *,
    base_dir: str | Path = Path("data/raw"),
) -> dict[str, Any] | None:
    """Cargar el checkpoint previo para un ``run_id``."""

    file = Path(base_dir) / run_id / "checkpoint.json"
    if not file.exists():
        return None
    with file.open("r", encoding="utf-8") as fh:
        return json.load(fh)


__all__ = [
    "exponential_backoff",
    "circuit_breaker",
    "CircuitBreakerOpen",
    "save_checkpoint",
    "load_checkpoint",
]
