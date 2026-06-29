"""
data_room/circuit_breaker.py
============================
Per-resolver circuit breaker (half-open state machine).

    CLOSED    ──(failure_threshold exceeded)──► OPEN
    OPEN      ──(cooldown elapsed)────────────► HALF_OPEN
    HALF_OPEN ──(test call succeeds)───────────► CLOSED
    HALF_OPEN ──(test call fails)──────────────► OPEN

The breaker is intentionally **per resolver**, not global. Aladdin
treats a Bloomberg outage differently from a Reuters outage.

Usage:
    breaker = CircuitBreaker(failure_threshold=5, cooldown_seconds=60)
    if breaker.allow():
        try:
            result = await call_resolver(...)
            breaker.record_success()
        except Exception:
            breaker.record_failure()
            raise
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, TypeVar

T = TypeVar("T")


class BreakerState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class CircuitBreaker:
    name: str = "default"
    failure_threshold: int = 5
    cooldown_seconds: float = 60.0

    _state: BreakerState = field(default=BreakerState.CLOSED, init=False)
    _failures: int = field(default=0, init=False)
    _opened_at: float = field(default=0.0, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    @property
    def state(self) -> BreakerState:
        return self._state

    def allow(self) -> bool:
        """Return True if the caller may attempt the protected call."""
        with self._lock:
            now = time.monotonic()
            if self._state is BreakerState.OPEN:
                if now - self._opened_at >= self.cooldown_seconds:
                    self._state = BreakerState.HALF_OPEN
                    return True
                return False
            return True

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._state = BreakerState.CLOSED

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self.failure_threshold:
                self._state = BreakerState.OPEN
                self._opened_at = time.monotonic()


def call_with_breaker(
    breaker: CircuitBreaker,
    fn: Callable[[], T],
) -> T:
    """
    Run fn() through the breaker. Returns its result. If the breaker is
    OPEN, raises CircuitBreakerOpen. If fn() raises, the failure is recorded
    on the breaker and the exception is re-raised.
    """
    if not breaker.allow():
        raise CircuitBreakerOpen("CircuitBreakerOpen: circuit is OPEN, refusing call")
    try:
        result = fn()
    except Exception:
        breaker.record_failure()
        raise
    else:
        breaker.record_success()
        return result


class CircuitBreakerOpen(Exception):
    """Raised when the breaker is OPEN and the call is rejected."""


__all__ = ["CircuitBreaker", "BreakerState", "T"]
