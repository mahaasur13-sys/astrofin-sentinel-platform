"""
tests/data_room/test_data_room.py
=================================
Tests for the Data Room: circuit breaker, graceful degradation,
observability counter.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from data_room.circuit_breaker import (  # noqa: E402
    BreakerState as CircuitState,
    CircuitBreaker,
    call_with_breaker,
)
from data_room.observability import MetricsStore  # noqa: E402

reset_metrics = MetricsStore.instance().reset


def test_circuit_breaker_starts_closed():
    cb = CircuitBreaker("test", failure_threshold=3, cooldown_seconds=0.1)
    assert cb.state == CircuitState.CLOSED


def test_circuit_breaker_opens_after_threshold():
    cb = CircuitBreaker("test", failure_threshold=2, cooldown_seconds=0.1)

    def boom():
        raise RuntimeError("nope")

    for _ in range(2):
        with pytest.raises(RuntimeError):
            call_with_breaker(cb, boom)
    assert cb.state == CircuitState.OPEN


def test_circuit_breaker_short_circuits_when_open():
    cb = CircuitBreaker("test", failure_threshold=1, cooldown_seconds=10)

    def boom():
        raise RuntimeError("nope")

    with pytest.raises(RuntimeError):
        call_with_breaker(cb, boom)
    # Now open. Next call should NOT invoke the function.
    called = False

    def ok():
        nonlocal called
        called = True
        return "ok"

    with pytest.raises(Exception) as exc_info:
        call_with_breaker(cb, ok)
    assert "CircuitBreakerOpen" in str(exc_info.value)
    assert not called


def test_circuit_breaker_half_open_recovery():
    cb = CircuitBreaker("test", failure_threshold=1, cooldown_seconds=0.05)

    def boom():
        raise RuntimeError("nope")

    with pytest.raises(RuntimeError):
        call_with_breaker(cb, boom)
    time.sleep(0.06)

    def ok():
        return "ok"

    # First call after cooldown → HALF_OPEN → success → CLOSED
    assert call_with_breaker(cb, ok) == "ok"
    assert cb.state == CircuitState.CLOSED


def test_metrics_store_records_calls():
    reset_metrics()
    m = MetricsStore.instance()
    m.record("resolver_a", latency=0.1, success=True, quality=0.95)
    m.record("resolver_a", latency=0.2, success=False, quality=0.0)
    m.record("resolver_b", latency=0.3, success=True, quality=0.8)

    snapshot = m.snapshot()
    assert snapshot["access_count"]["resolver_a"] == 2
    assert snapshot["error_count"]["resolver_a"] == 1
    assert snapshot["access_count"]["resolver_b"] == 1
    assert abs(snapshot["latency_sum_ms"]["resolver_a"] - 300.0) < 1.0
    assert snapshot["last_quality"]["resolver_a"] == 0.0  # last call failed


def test_metrics_store_health_check():
    reset_metrics()
    m = MetricsStore.instance()
    for _ in range(10):
        m.record("good", latency=0.01, success=True, quality=0.9)
    for _ in range(7):
        m.record("bad", latency=0.01, success=False, quality=0.0)
    # `bad` is >50% failure → degraded
    health = m.health_check()
    assert health["good"]["status"] == "healthy"
    assert health["bad"]["status"] == "degraded"


def test_blueprint_falls_back_to_secondary_on_error():
    """If primary resolver raises, blueprint tries the secondary."""
    from data_room.blueprint import Blueprint, PriceTick

    class AlwaysFails:
        id = "always_fails"
        freshness_sla_seconds = 30

        async def resolve(self, symbol, asof):
            raise RuntimeError("down")

    class AlwaysSucceeds:
        id = "always_succeeds"
        freshness_sla_seconds = 30

        async def resolve(self, symbol, asof):
            return PriceTick(symbol=symbol, price=100.0, asof=asof or "now", source_id=self.id, quality_score=0.9)

    bp = Blueprint()
    bp.register("price", AlwaysFails(), chain=["always_succeeds"])
    bp.register("price", AlwaysSucceeds())

    import asyncio

    tick = asyncio.run(bp.get_price("BTCUSDT"))
    assert tick.source_id == "always_succeeds"
    assert tick.price == 100.0


def test_blueprint_returns_none_when_all_fail():
    """If all resolvers in the chain fail, get_price() returns None."""
    from data_room.blueprint import Blueprint

    class Fail1:
        id = "fail1"
        freshness_sla_seconds = 30

        async def resolve(self, symbol, asof):
            raise RuntimeError("down1")

    class Fail2:
        id = "fail2"
        freshness_sla_seconds = 30

        async def resolve(self, symbol, asof):
            raise RuntimeError("down2")

    bp = Blueprint()
    bp.register("price", Fail1(), chain=["fail2"])
    bp.register("price", Fail2())

    import asyncio

    result = asyncio.run(bp.get_price("BTCUSDT"))
    assert result is None
