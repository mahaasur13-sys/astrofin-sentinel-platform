"""
system_observer.py — Stability metrics + feedback-loop monitors
────────────────────────────────────────────────────────────────
Collects and computes:
  - system_stability_index (SSI): 0..1 (1=perfect, 0=turbulent)
  - retry_amplification_rate (RAR): retries issued / failures observed
  - DAG_recompute_ratio (DCR): nodes recomputed / total nodes executed
  - shedding_trigger_frequency (STF): load-shed events / time window
  - GREEN↔RED bounce detection (oscillation)
  - per-metric degradation history
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum

# ──────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────

class StabilityLevel(str, Enum):
    STEADY   = "STEADY"   # SSI > 0.85
    MARGINAL = "MARGINAL" # 0.5 < SSI ≤ 0.85
    TURBULENT= "TURBULENT"# SSI ≤ 0.5


# ──────────────────────────────────────────────────────────────
# Metric Snapshots
# ──────────────────────────────────────────────────────────────

@dataclass
class StabilitySnapshot:
    ts: float
    queue_depth: int
    cpu_pct: float
    mem_pct: float
    error_rate: float
    p95_latency_ms: float
    degradation_level: str  # GREEN / YELLOW / RED

    # Counters for this window
    retries_issued: int = 0
    failures_observed: int = 0
    nodes_executed: int = 0
    nodes_recomputed: int = 0
    shed_events: int = 0
    green_red_bounces: int = 0

    # Computed rates
    retry_amplification_rate: float = 0.0
    dag_recompute_ratio: float = 0.0
    system_stability_index: float = 1.0


@dataclass
class SheddingOscillation:
    timestamp: float
    from_level: str
    to_level: str


# ──────────────────────────────────────────────────────────────
# System Observer
# ──────────────────────────────────────────────────────────────

class SystemObserver:
    """
    Passive monitor: call .record() on every event you want to track.
    Call .compute() to get current StabilitySnapshot.
    """

    def __init__(
        self,
        window_seconds: float = 60.0,
        history_size: int = 1000,
    ):
        self._window = window_seconds
        self._history: deque[StabilitySnapshot] = deque(maxlen=history_size)
        self._lock = threading.Lock()

        # Event counters (sliding window via timestamps)
        self._events: dict[str, list[float]] = {
            "retry": [],
            "failure": [],
            "node_exec": [],
            "node_recompute": [],
            "shed": [],
            "degradation_change": [],
        }
        self._oscillations: deque[SheddingOscillation] = deque(maxlen=100)

        # Last degradation level seen (for bounce detection)
        self._last_deg_level: str | None = None

        # Metrics source — set externally or via Redis
        self._metrics_getter: callable | None = None

    def set_metrics_getter(self, getter: callable) -> None:
        """Callable that returns (queue_depth, cpu_pct, mem_pct, error_rate, p95_lat_ms)."""
        self._metrics_getter = getter

    # ── Recording ──────────────────────────────────────────────

    def record_retry(self):
        with self._lock:
            self._events["retry"].append(time.time())

    def record_failure(self):
        with self._lock:
            self._events["failure"].append(time.time())

    def record_node_executed(self):
        with self._lock:
            self._events["node_exec"].append(time.time())

    def record_node_recomputed(self):
        with self._lock:
            self._events["node_recompute"].append(time.time())

    def record_shed_event(self):
        with self._lock:
            self._events["shed"].append(time.time())

    def record_degradation_change(self, new_level: str):
        with self._lock:
            self._events["degradation_change"].append(time.time())
            if self._last_deg_level is not None:
                if self._last_deg_level == "GREEN" and new_level == "RED":
                    self._oscillations.append(SheddingOscillation(
                        ts=time.time(),
                        from_level="GREEN",
                        to_level="RED",
                    ))
                elif self._last_deg_level == "RED" and new_level == "GREEN":
                    self._oscillations.append(SheddingOscillation(
                        ts=time.time(),
                        from_level="RED",
                        to_level="GREEN",
                    ))
            self._last_deg_level = new_level

    # ── Sliding window filter ───────────────────────────────────

    def _windowed(self, event_type: str) -> int:
        now = time.time()
        cutoff = now - self._window
        times = self._events.get(event_type, [])
        # inline filter (list comprehension is fine for small lists)
        return sum(1 for t in times if t > cutoff)

    def _windowed_ratio(self, numerator: str, denominator: str) -> float:
        num = self._windowed(numerator)
        den = self._windowed(denominator)
        return num / den if den > 0 else 0.0

    # ── Stability Index computation ────────────────────────────

    def _compute_ssi(
        self,
        rar: float,
        dcr: float,
        stf: float,
        oscillation_count: int,
        error_rate: float,
    ) -> float:
        """
        SSI = weighted product of sub-scores.
        RAR: 1 retry/failure = 1.0 (ideal), >3 = 0 (bad)
        DCR: 0 recompute = 1.0, >50% recompute = 0
        STF: 0 shed events/min = 1.0, >30 = 0
        Oscillation: 0 = 1.0, >5 bounces/min = 0
        Error rate: 0% = 1.0, >20% = 0
        """
        rar_score = max(0.0, min(1.0, 1.0 - (rar - 1.0) / 3.0)) if rar >= 1.0 else 1.0
        dcr_score = max(0.0, 1.0 - dcr * 2.0)
        stf_score = max(0.0, min(1.0, 1.0 - stf / 30.0))
        osc_score = max(0.0, 1.0 - oscillation_count / 5.0)
        err_score = max(0.0, min(1.0, 1.0 - error_rate / 0.2))

        return rar_score * 0.25 + dcr_score * 0.2 + stf_score * 0.2 + osc_score * 0.15 + err_score * 0.2

    # ── Snapshot ───────────────────────────────────────────────

    def compute(self) -> StabilitySnapshot:
        now = time.time()

        with self._lock:
            # Collect system metrics
            if self._metrics_getter:
                qd, cpu, mem, err, p95 = self._metrics_getter()
            else:
                qd, cpu, mem, err, p95 = 0, 0.0, 0.0, 0.0, 0.0

            # Count events in window
            retries = self._windowed("retry")
            failures = self._windowed("failure")
            nodes_exec = self._windowed("node_exec")
            nodes_recomp = self._windowed("node_recompute")
            shed_events = self._windowed("shed")
            self._windowed("degradation_change")

            # Oscillations in window
            cutoff = now - self._window
            recent_osc = sum(1 for o in self._oscillations if o.timestamp > cutoff)

            # Rates
            rar = retries / failures if failures > 0 else 0.0
            dcr = nodes_recomp / nodes_exec if nodes_exec > 0 else 0.0
            stf = shed_events * 60.0 / self._window  # events per minute

            # Degradation level from metrics
            deg = self._degradation_level(cpu, mem, qd, err, p95)

            # SSI
            ssi = self._compute_ssi(rar, dcr, stf, recent_osc, err)

            snap = StabilitySnapshot(
                ts=now,
                queue_depth=qd,
                cpu_pct=cpu,
                mem_pct=mem,
                error_rate=err,
                p95_latency_ms=p95,
                degradation_level=deg.value if hasattr(deg, 'value') else str(deg),
                retries_issued=retries,
                failures_observed=failures,
                nodes_executed=nodes_exec,
                nodes_recomputed=nodes_recomp,
                shed_events=shed_events,
                green_red_bounces=recent_osc,
                retry_amplification_rate=rar,
                dag_recompute_ratio=dcr,
                system_stability_index=ssi,
            )

            self._history.append(snap)
            return snap

    def _degradation_level(
        self,
        cpu: float,
        mem: float,
        queue_depth: int,
        error_rate: float,
        p95_ms: float,
    ) -> StabilityLevel:
        if cpu > 90 or mem > 85 or queue_depth > 1000 or error_rate > 0.2 or p95_ms > 500:
            return StabilityLevel.TURBULENT
        if cpu > 70 or mem > 70 or queue_depth > 500 or error_rate > 0.1 or p95_ms > 200:
            return StabilityLevel.MARGINAL
        return StabilityLevel.STEADY

    def get_stability_level(self) -> StabilityLevel:
        snap = self.compute()
        return self._degradation_level(
            snap.cpu_pct, snap.mem_pct, snap.queue_depth,
            snap.error_rate, snap.p95_latency_ms,
        )

    def get_history(self) -> list[StabilitySnapshot]:
        with self._lock:
            return list(self._history)

    def get_summary(self) -> dict:
        """One-line human-readable status."""
        snap = self.compute()
        osc = self._oscillations[-1] if self._oscillations else None
        return {
            "stability_index": round(snap.system_stability_index, 3),
            "stability_level": self.get_stability_level().value,
            "retry_amplification_rate": round(snap.retry_amplification_rate, 2),
            "dag_recompute_ratio": round(snap.dag_recompute_ratio, 3),
            "shed_per_minute": round(snap.shed_events * 60 / self._window, 2),
            "green_red_bounces": snap.green_red_bounces,
            "last_oscillation": {
                "ts": osc.timestamp if osc else None,
                "from": osc.from_level if osc else None,
                "to": osc.to_level if osc else None,
            } if osc else None,
            "queue_depth": snap.queue_depth,
            "cpu_pct": round(snap.cpu_pct, 1),
            "error_rate": round(snap.error_rate, 3),
        }
