"""
Governance Layer — Layer C.

Provides:
- SystemMetrics dataclass
- DegradationLevel enum
- GlobalDegradationController (GREEN/YELLOW/RED system state)
- LoadShedder (queue/memory/CPU pressure → reject/cancel/throttle LOW priority)
- AdmissionController (priority-gated task acceptance)
- AdaptiveRetryController (dynamic backoff tuning based on health signals)
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from enum import Enum

import redis.asyncio as aioredis

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

_async_r: aioredis.Redis | None = None


async def _get_redis() -> aioredis.Redis:
    global _async_r
    if _async_r is None:
        _async_r = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _async_r


# ── system model ────────────────────────────────────────────────────────────────

@dataclass
class SystemMetrics:
    queue_depth: int = 0
    cpu_usage: float = 0.0       # 0.0–1.0
    memory_usage: float = 0.0   # 0.0–1.0
    p95_latency: float = 0.0    # seconds
    error_rate_15m: float = 0.0  # 0.0–1.0 fraction
    active_workers: int = 0
    ollama_healthy: bool = True
    redis_healthy: bool = True
    qdrant_healthy: bool = True
    timestamp: float = field(default_factory=time.time)


class DegradationLevel(str, Enum):
    GREEN = "green"   # nominal
    YELLOW = "yellow"  # degraded — some action needed
    RED = "red"       # critical — immediate load shedding


# ── load shedding decision ─────────────────────────────────────────────────────

@dataclass
class LoadShedDecision:
    reject: list[str] = field(default_factory=list)   # ["LOW_PRIORITY", ...]
    cancel: list[str] = field(default_factory=list)   # ["LOW_PRIORITY", ...]
    throttle_factor: float = 1.0                       # multiply concurrency by this
    degradation: DegradationLevel = DegradationLevel.GREEN
    reason: str = ""

    def no_action(self) -> bool:
        return not self.reject and not self.cancel and self.throttle_factor == 1.0


@dataclass
class AdmissionDecision:
    allowed: bool
    reason: str
    queue_if_rejected: bool = False  # suggest enqueueing for later


# ── Global Degradation Controller ──────────────────────────────────────────────

class GlobalDegradationController:
    """
    Centralised system-health evaluator.
    Reads metrics → emits a global DegradationLevel.
    Downstream components (LoadShedder, AdaptiveRetryController) react to it.
    """

    QUEUE_DEPTH_YELLOW = 500
    QUEUE_DEPTH_RED = 1000
    CPU_YELLOW = 0.75
    CPU_RED = 0.90
    MEM_YELLOW = 0.70
    MEM_RED = 0.85
    P95_LAT_YELLOW = 5.0   # seconds
    P95_LAT_RED = 10.0
    ERROR_RATE_YELLOW = 0.10
    ERROR_RATE_RED = 0.30

    async def evaluate(self, m: SystemMetrics) -> DegradationLevel:
        # RED conditions — any one triggers RED
        if (m.queue_depth >= self.QUEUE_DEPTH_RED
                or m.cpu_usage >= self.CPU_RED
                or m.memory_usage >= self.MEM_RED
                or m.p95_latency >= self.P95_LAT_RED
                or m.error_rate_15m >= self.ERROR_RATE_RED
                or not m.ollama_healthy
                or not m.redis_healthy):
            return DegradationLevel.RED

        # YELLOW conditions — any one triggers YELLOW
        if (m.queue_depth >= self.QUEUE_DEPTH_YELLOW
                or m.cpu_usage >= self.CPU_YELLOW
                or m.memory_usage >= self.MEM_YELLOW
                or m.p95_latency >= self.P95_LAT_YELLOW
                or m.error_rate_15m >= self.ERROR_RATE_YELLOW
                or not m.qdrant_healthy):
            return DegradationLevel.YELLOW

        return DegradationLevel.GREEN

    async def get_concurrency_multiplier(self, level: DegradationLevel) -> float:
        if level == DegradationLevel.RED:
            return 0.25
        if level == DegradationLevel.YELLOW:
            return 0.60
        return 1.0


# ── Load Shedder ───────────────────────────────────────────────────────────────

class LoadShedder:
    """
    Evaluates SystemMetrics → LoadShedDecision.
    Acts on LOW priority tasks when system is under pressure.
    """

    QUEUE_REJECT_THRESHOLD = 1000
    MEMORY_CANCEL_THRESHOLD = 0.80
    CPU_THROTTLE_THRESHOLD = 0.90
    THROTTLE_FACTOR_REDUCED = 0.5

    def evaluate(self, m: SystemMetrics) -> LoadShedDecision:
        decision = LoadShedDecision()
        reasons = []

        # queue overload
        if m.queue_depth > self.QUEUE_REJECT_THRESHOLD:
            decision.reject.append("LOW_PRIORITY")
            reasons.append(f"queue_depth={m.queue_depth}")

        # memory pressure
        if m.memory_usage > self.MEMORY_CANCEL_THRESHOLD:
            decision.cancel.append("LOW_PRIORITY")
            reasons.append(f"memory_usage={m.memory_usage:.0%}")

        # CPU pressure
        if m.cpu_usage > self.CPU_THROTTLE_THRESHOLD:
            decision.throttle_factor = self.THROTTLE_FACTOR_REDUCED
            reasons.append(f"cpu_usage={m.cpu_usage:.0%}")

        if reasons:
            decision.reason = "; ".join(reasons)

        return decision

    def from_degradation(self, level: DegradationLevel) -> LoadShedDecision:
        """Translate degradation level to a conservative shed decision."""
        if level == DegradationLevel.RED:
            return LoadShedDecision(
                reject=["LOW_PRIORITY"],
                cancel=["LOW_PRIORITY"],
                throttle_factor=0.25,
                degradation=level,
                reason=f"degradation={level.value}",
            )
        if level == DegradationLevel.YELLOW:
            return LoadShedDecision(
                reject=[],
                cancel=["LOW_PRIORITY"],
                throttle_factor=0.6,
                degradation=level,
                reason=f"degradation={level.value}",
            )
        return LoadShedDecision(degradation=level)


# ── Admission Controller ───────────────────────────────────────────────────────

class AdmissionController:
    """
    Priority-gated task admission.
    Consults LoadShedDecision before accepting a task.
    """

    def __init__(self, shedder: LoadShedder | None = None):
        self.shedder = shedder or LoadShedder()

    def allow(self, task_priority: str, shed: LoadShedDecision) -> AdmissionDecision:
        # LOW priority tasks are first-class shedding candidates
        if task_priority == "LOW" and "LOW_PRIORITY" in shed.reject:
            return AdmissionDecision(
                allowed=False,
                reason=f"LoadShed rejected LOW priority: {shed.reason}",
                queue_if_rejected=True,
            )
        if task_priority == "LOW" and "LOW_PRIORITY" in shed.cancel:
            return AdmissionDecision(
                allowed=False,
                reason=f"LoadShed cancelled LOW priority: {shed.reason}",
                queue_if_rejected=False,
            )
        return AdmissionDecision(allowed=True, reason="admitted")

    def allow_from_metrics(self, task_priority: str, m: SystemMetrics) -> AdmissionDecision:
        shed = self.shedder.evaluate(m)
        return self.allow(task_priority, shed)


# ── Adaptive Retry Controller ──────────────────────────────────────────────────

class AdaptiveRetryController:
    """
    Dynamically tunes retry budgets based on system health.
    Tracks error_rate and latency over sliding windows.
    """

    # Tunable thresholds
    HIGH_ERROR_RATE = 0.20   # >20% errors → increase delay
    LOW_ERROR_RATE = 0.05    # <5% errors  → relax delay
    HIGH_LATENCY = 5.0        # p95 > 5s → increase delay
    LOW_LATENCY = 1.0         # p95 < 1s → relax delay

    # Multipliers applied to base_delay
    DELAY_INCREASE_FACTOR = 2.0
    DELAY_DECREASE_FACTOR = 0.75

    def __init__(self):
        self._base_delay = 1.0   # seconds
        self._current_multiplier = 1.0

    @property
    def base_delay(self) -> float:
        return self._base_delay * self._current_multiplier

    async def tune(self, m: SystemMetrics) -> float:
        """
        Adjust retry delay multiplier based on current system health.
        Returns the new base_delay to use.
        """
        if m.error_rate_15m > self.HIGH_ERROR_RATE or m.p95_latency > self.HIGH_LATENCY:
            self._current_multiplier = min(
                self._current_multiplier * self.DELAY_INCREASE_FACTOR, 16.0
            )
        elif m.error_rate_15m < self.LOW_ERROR_RATE and m.p95_latency < self.LOW_LATENCY:
            self._current_multiplier = max(
                self._current_multiplier * self.DELAY_DECREASE_FACTOR, 0.25
            )

        # Persist current state to Redis for observability
        r = await _get_redis()
        await r.hset("adaptive_retry:state", mapping={
            "base_delay": str(self.base_delay),
            "multiplier": str(self._current_multiplier),
            "error_rate": str(m.error_rate_15m),
            "p95_latency": str(m.p95_latency),
            "updated_at": str(time.time()),
        })

        return self.base_delay

    async def get_state(self) -> dict:
        r = await _get_redis()
        raw = await r.hgetall("adaptive_retry:state")
        return raw or {
            "base_delay": str(self.base_delay),
            "multiplier": str(self._current_multiplier),
        }


# ── Metrics Collector (pulls from Redis) ─────────────────────────────────────

class MetricsCollector:
    """
    Aggregates current system metrics from Redis keys
    written by engine.py / dag_retry.py.
    """

    @staticmethod
    async def collect() -> SystemMetrics:
        r = await _get_redis()
        raw = await r.hgetall("system:metrics")
        defaults = {
            "queue_depth": "0",
            "cpu_usage": "0.0",
            "memory_usage": "0.0",
            "p95_latency": "0.0",
            "error_rate_15m": "0.0",
            "active_workers": "0",
            "ollama_healthy": "true",
            "redis_healthy": "true",
            "qdrant_healthy": "true",
        }
        raw = {**defaults, **raw}
        return SystemMetrics(
            queue_depth=int(raw["queue_depth"]),
            cpu_usage=float(raw["cpu_usage"]),
            memory_usage=float(raw["memory_usage"]),
            p95_latency=float(raw["p95_latency"]),
            error_rate_15m=float(raw["error_rate_15m"]),
            active_workers=int(raw["active_workers"]),
            ollama_healthy=raw["ollama_healthy"] == "true",
            redis_healthy=raw["redis_healthy"] == "true",
            qdrant_healthy=raw["qdrant_healthy"] == "true",
        )

    @staticmethod
    async def write(m: SystemMetrics) -> None:
        r = await _get_redis()
        await r.hset("system:metrics", mapping={
            "queue_depth": str(m.queue_depth),
            "cpu_usage": str(m.cpu_usage),
            "memory_usage": str(m.memory_usage),
            "p95_latency": str(m.p95_latency),
            "error_rate_15m": str(m.error_rate_15m),
            "active_workers": str(m.active_workers),
            "ollama_healthy": str(m.ollama_healthy).lower(),
            "redis_healthy": str(m.redis_healthy).lower(),
            "qdrant_healthy": str(m.qdrant_healthy).lower(),
            "timestamp": str(m.timestamp),
        })
