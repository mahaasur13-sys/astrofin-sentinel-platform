"""core.circuit_breaker — ADR-001 Sprint 3: Circuit Breaker с per-provider изоляцией."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────

@dataclass
class CBConfig:
    failure_threshold: int = 5
    window_seconds: float = 60.0
    recovery_cooldown: float = 30.0
    half_open_max: int = 3
    success_threshold: int = 2

DEFAULT_CB_CONFIG = CBConfig()

# ── State ──────────────────────────────────────────────────────────────

class CBState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

# ── Circuit Breaker ──────────────────────────────────────────────────

class CircuitBreaker:
    """3-phase Circuit Breaker per provider."""
    _config: CBConfig
    _name: str
    _state: CBState
    _failure_history: list[float]
    _opened_at: float
    _in_flight_count: int
    _success_count: int

    def __init__(self, config: CBConfig | None = None, name: str = "default"):
        self._config = config or DEFAULT_CB_CONFIG
        self._name = name
        self._state = CBState.CLOSED
        self._failure_history = []
        self._opened_at = 0.0
        self._in_flight_count = 0
        self._success_count = 0

    @property
    def state(self) -> CBState:
        return self._state

    @property
    def is_open(self) -> bool:
        return self._state == CBState.OPEN

    @property
    def is_closed(self) -> bool:
        return self._state == CBState.CLOSED

    @property
    def failure_count(self) -> int:
        return len(self._failure_history)

    def _prune_failures(self, now: float) -> None:
        cutoff = now - self._config.window_seconds
        self._failure_history = [t for t in self._failure_history if t >= cutoff]

    def failure(self) -> None:
        now = time.time()
        if self._state == CBState.OPEN:
            return
        if self._state == CBState.HALF_OPEN:
            self._state = CBState.OPEN
            self._opened_at = now
            return
        self._failure_history.append(now)
        self._prune_failures(now)
        if len(self._failure_history) > self._config.failure_threshold:
            self._state = CBState.OPEN
            self._opened_at = now

    def record_failure(self) -> None:
        self.failure()

    def success(self) -> None:
        self._in_flight_count = max(0, self._in_flight_count - 1)
        if self._state == CBState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self._config.success_threshold:
                self._state = CBState.CLOSED
                self._failure_history = []

    def record_success(self) -> None:
        self.success()

    async def acquire(self) -> None:
        now = time.time()
        if self._state == CBState.OPEN:
            if now - self._opened_at >= self._config.recovery_cooldown:
                self._state = CBState.HALF_OPEN
                self._in_flight_count = 0
                self._success_count = 0
            else:
                raise CircuitBreakerOpenError(self._name, self._opened_at)
        if self._state == CBState.HALF_OPEN:
            self._in_flight_count += 1
            if self._in_flight_count > self._config.half_open_max:
                raise CircuitBreakerHalfOpenLimitError(
                    self._name, self._in_flight_count, self._config.half_open_max
                )

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.record_failure()
            return False
        self.record_success()
        return None

    def stats(self) -> dict:
        return {
            "state": self._state.value,
            "failure_count": self.failure_count,
            "in_flight": self._in_flight_count,
            "success_count": self._success_count,
        }

# ── Registry ─────────────────────────────────────────────────────────

class CircuitBreakerRegistry:
    """Registry of circuit breakers indexed by provider."""
    _breakers: dict[str, CircuitBreaker]
    _default_config: CBConfig

    def __init__(self, default_config: CBConfig | None = None):
        self._breakers = {}
        self._default_config = default_config or DEFAULT_CB_CONFIG

    def get(self, provider: str, config: CBConfig | None = None) -> CircuitBreaker:
        if provider not in self._breakers:
            self._breakers[provider] = CircuitBreaker(config=config or self._default_config, name=provider)
        return self._breakers[provider]

    def all_metrics(self) -> dict[str, dict[str, Any]]:
        return {n: {"state": b.state.value, "failure_count": b.failure_count} for n, b in self._breakers.items()}

    def stats(self) -> dict[str, dict]:
        return {name: cb.stats() for name, cb in self._breakers.items()}

    def reset(self, provider: str | None = None) -> None:
        if provider:
            self._breakers.pop(provider, None)
        else:
            self._breakers.clear()

# ── Exceptions ────────────────────────────────────────────────────────

class CircuitBreakerOpenError(Exception):
    def __init__(self, provider: str, opened_at: float):
        self.provider = provider
        self.opened_at = opened_at
        super().__init__(f"Circuit breaker OPEN for '{provider}'")

class CircuitBreakerHalfOpenLimitError(Exception):
    def __init__(self, provider: str, in_flight: int, max_allowed: int):
        self.provider = provider
        super().__init__(f"HALF_OPEN limit exceeded for '{provider}' ({in_flight}/{max_allowed})")
