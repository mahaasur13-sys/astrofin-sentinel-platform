"""
observability/metrics.py
========================
Prometheus metrics for AstroFin Sentinel V5.

This module is the single source of truth for *what we measure*. It
exposes a thin facade that can be backed by:

  - prometheus_client (production)
  - in-memory dict (tests, CI)

Use these helpers from anywhere; do not import prometheus_client directly
elsewhere. That way swapping the backend is a one-file change.

Naming convention follows Prometheus best practices:
  - counters end in `_total`
  - histograms end in `_seconds`
  - gauges are nouns (e.g. `agent_confidence`)
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

try:
    from prometheus_client import Counter, Gauge, Histogram  # type: ignore

    _HAS_PROM = True
except ImportError:  # pragma: no cover
    _HAS_PROM = False

logger = logging.getLogger("observability")


# ─── Metric definitions ────────────────────────────────────────────────

AGENT_RUNS_TOTAL = (
    Counter(
        "astrofin_agent_runs_total",
        "Total number of agent invocations",
        labelnames=("agent", "signal", "ttc"),
    )
    if _HAS_PROM
    else None
)

AGENT_LATENCY_SECONDS = (
    Histogram(
        "astrofin_agent_latency_seconds",
        "Latency of a single agent invocation",
        labelnames=("agent", "ttc"),
        buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    )
    if _HAS_PROM
    else None
)

AGENT_CONFIDENCE = (
    Gauge(
        "astrofin_agent_confidence",
        "Last confidence score emitted by the agent",
        labelnames=("agent", "signal"),
    )
    if _HAS_PROM
    else None
)

DATA_ROOM_RESOLVE_TOTAL = (
    Counter(
        "astrofin_data_room_resolve_total",
        "Data Room resolver calls",
        labelnames=("resolver", "status"),
    )
    if _HAS_PROM
    else None
)

DATA_ROOM_LATENCY = (
    Histogram(
        "astrofin_data_room_latency_seconds",
        "Data Room resolver latency",
        labelnames=("resolver",),
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    )
    if _HAS_PROM
    else None
)

# Per-agent quality gauge
SIGNAL_CONSENSUS_QUALITY = (
    Gauge(
        "astrofin_signal_consensus_quality",
        "Quality of the weighted consensus (0..1)",
        labelnames=("symbol", "timeframe"),
    )
    if _HAS_PROM
    else None
)


# ─── Helpers ───────────────────────────────────────────────────────────


def record_agent_run(
    agent: str, signal: str, latency_s: float, confidence: int
) -> None:
    """Idempotent: records a single agent run, including latency and confidence."""
    if not _HAS_PROM:
        logger.debug(
            "metrics stub: agent=%s signal=%s conf=%d lat=%.3fs",
            agent,
            signal,
            confidence,
            latency_s,
        )
        return
    AGENT_RUNS_TOTAL.labels(agent=agent, signal=signal, ttc="false").inc()
    AGENT_LATENCY_SECONDS.labels(agent=agent, ttc="false").observe(latency_s)
    AGENT_CONFIDENCE.labels(agent=agent, signal=signal).set(confidence)


def record_data_room_resolve(resolver: str, status: str, latency_s: float) -> None:
    if not _HAS_PROM:
        logger.debug(
            "metrics stub: resolver=%s status=%s lat=%.3fs", resolver, status, latency_s
        )
        return
    DATA_ROOM_RESOLVE_TOTAL.labels(resolver=resolver, status=status).inc()
    DATA_ROOM_LATENCY.labels(resolver=resolver).observe(latency_s)


@contextmanager
def time_block(metric_name: str = "default") -> Any:
    """Convenience timing context for ad-hoc measurements.

    Yields the elapsed time (seconds) as a float. If prom is available,
    also records to the global latency histogram.
    """
    start = time.perf_counter()
    yield_holder: dict[str, float] = {"elapsed": 0.0}
    try:
        yield yield_holder
    finally:
        elapsed = time.perf_counter() - start
        yield_holder["elapsed"] = elapsed
        if _HAS_PROM and AGENT_LATENCY_SECONDS is not None:
            AGENT_LATENCY_SECONDS.labels(agent=metric_name, ttc="false").observe(
                elapsed
            )


def with_agent_timing(
    agent: str,
    signal_getter: Callable[[Any], str],
    confidence_getter: Callable[[Any], int],
) -> Callable:
    """Decorator: record latency + confidence of an agent's run() method.

    Usage:
        @with_agent_timing("FundamentalAgent",
                           signal_getter=lambda r: r.signal.value,
                           confidence_getter=lambda r: r.confidence)
        async def run(self, state): ...
    """

    def deco(fn: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = await fn(*args, **kwargs)
            latency = time.perf_counter() - start
            try:
                sig = signal_getter(result)
                conf = confidence_getter(result)
                record_agent_run(agent, sig, latency, conf)
            except Exception as exc:  # noqa: BLE001
                logger.warning("with_agent_timing: %s", exc)
            return result

        return wrapper

    return deco


__all__ = [
    "record_agent_run",
    "record_data_room_resolve",
    "time_block",
    "with_agent_timing",
    "AGENT_RUNS_TOTAL",
    "AGENT_LATENCY_SECONDS",
    "AGENT_CONFIDENCE",
    "DATA_ROOM_RESOLVE_TOTAL",
    "DATA_ROOM_LATENCY",
    "SIGNAL_CONSENSUS_QUALITY",
]
