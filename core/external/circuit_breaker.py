"""Circuit breaker pattern with tenacity + Prometheus metrics.

Usage:
    from core.external.circuit_breaker import CircuitBreaker

    cb = CircuitBreaker("coingecko", fail_max=5, timeout_seconds=60)
    with cb:
        result = call_external_service()

Or as a decorator:
    @circuit_breaker("coingecko")
    def fetch_price(symbol: str) -> float: ...
"""

from __future__ import annotations

import time
from collections.abc import Callable
from functools import wraps

from tenacity import (
    RetryError,
    retry,
    stop_after_attempt,
    wait_exponential,
)

try:
    from prometheus_client import Counter, Gauge
    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False

CIRCUIT_STATE = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half_open)",
    ["service"],
) if _PROMETHEUS_AVAILABLE else None

CIRCUIT_FAILURES = Counter(
    "circuit_breaker_failures_total",
    "Total circuit breaker trip events",
    ["service"],
) if _PROMETHEUS_AVAILABLE else None

CIRCUIT_FALLBACKS = Counter(
    "circuit_breaker_fallbacks_total",
    "Total fallback activations",
    ["service"],
) if _PROMETHEUS_AVAILABLE else None

import logging

log = logging.getLogger(__name__)


class CircuitBreakerError(Exception):
    """Raised when a circuit breaker is open."""


class CircuitBreaker:
    """Stateful circuit breaker with half-open probing."""

    def __init__(
        self,
        service: str,
        fail_max: int = 5,
        timeout_seconds: float = 60.0,
        fallback: Callable | None = None,
    ) -> None:
        self.service = service
        self.fail_max = fail_max
        self.timeout_seconds = timeout_seconds
        self.fallback = fallback
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._state: str = "closed"

    @property
    def is_open(self) -> bool:
        if self._state == "open":
            if time.monotonic() - self._last_failure_time >= self.timeout_seconds:
                self._state = "half_open"
                self._emit_metric()
                log.info("circuit_breaker: %s → half_open (probing)", self.service)
                return False
            return True
        return False

    def success(self) -> None:
        self._failure_count = 0
        if self._state == "half_open":
            log.info("circuit_breaker: %s → closed (recovered)", self.service)
        self._state = "closed"
        self._emit_metric()

    def failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self.fail_max:
            self._state = "open"
            log.warning("circuit_breaker: %s → open (failures=%d)", self.service, self._failure_count)
            if CIRCUIT_FAILURES:
                CIRCUIT_FAILURES.labels(service=self.service).inc()
        self._emit_metric()

    def _emit_metric(self) -> None:
        if CIRCUIT_STATE:
            state_map = {"closed": 0, "open": 1, "half_open": 2}
            CIRCUIT_STATE.labels(service=self.service).set(state_map.get(self._state, -1))

    def __enter__(self) -> CircuitBreaker:
        if self.is_open:
            if self.fallback:
                if CIRCUIT_FALLBACKS:
                    CIRCUIT_FALLBACKS.labels(service=self.service).inc()
                return self
            raise CircuitBreakerError(f"Circuit breaker open for {self.service}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is None:
            self.success()
        elif exc_type is not None:
            self.failure()
            if self.fallback:
                if CIRCUIT_FALLBACKS:
                    CIRCUIT_FALLBACKS.labels(service=self.service).inc()
                return True
        return False

    def wrap(self, func: Callable) -> Callable:
        """Decorator wrapping with retry + circuit breaker."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.is_open:
                if self.fallback:
                    return self.fallback(*args, **kwargs)
                raise CircuitBreakerError(f"Circuit breaker open for {self.service}")
            try:
                @retry(
                    stop=stop_after_attempt(2),
                    wait=wait_exponential(multiplier=1, min=0.5, max=4),
                    reraise=True,
                )
                def _inner():
                    return func(*args, **kwargs)
                result = _inner()
                self.success()
                return result
            except (RetryError, Exception) as e:
                self.failure()
                if self.fallback:
                    return self.fallback(*args, **kwargs)
                raise
        return wrapper


def circuit_breaker(service: str, fail_max: int = 5, timeout_seconds: float = 60.0):
    """Decorator factory for circuit breaker patterns."""
    cb = CircuitBreaker(service, fail_max=fail_max, timeout_seconds=timeout_seconds)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return cb.wrap(func)(*args, **kwargs)
        return wrapper
    return decorator
