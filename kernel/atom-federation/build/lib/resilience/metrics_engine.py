"""
StabilityMetricsEngine v6.4 — Runtime stability scoring.

Produces a StabilitySnapshot every interval:
  - stability_score (0.0–1.0): overall cluster health
  - components: per-subsystem scores
  - rto_ms: estimated recovery time objective
  - convergence_time_ms: time for cluster to stabilize after fault
  - recovery_rate: fraction of ops that succeeded during chaos

Usage:
    engine = StabilityMetricsEngine(window_seconds=60)
    engine.record_violation("sbs", severity="critical")
    engine.record_recovery(node_id="node-c")
    snapshot = engine.get_snapshot()
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass

__all__ = ["StabilityMetricsEngine", "StabilitySnapshot"]


@dataclass
class StabilitySnapshot:
    """Point-in-time cluster stability measurement."""
    ts: float
    stability_score: float           # 0.0 (down) → 1.0 (perfect)
    quorum_health: float             # 0.0 → 1.0
    network_health: float            # 0.0 → 1.0
    sbs_health: float                # 0.0 → 1.0
    routing_health: float            # 0.0 → 1.0
    rto_ms: float                    # Estimated RTO in ms
    convergence_time_ms: float        # Last convergence event in ms
    recovery_rate: float             # Fraction of ops succeeding (0.0–1.0)
    violation_count_60s: int
    node_count_total: int
    node_count_healthy: int
    anomaly_count: int

    def is_healthy(self, threshold: float = 0.7) -> bool:
        return self.stability_score >= threshold

    def to_dict(self) -> dict:
        return {
            "ts": self.ts,
            "stability_score": round(self.stability_score, 4),
            "quorum_health": round(self.quorum_health, 4),
            "network_health": round(self.network_health, 4),
            "sbs_health": round(self.sbs_health, 4),
            "routing_health": round(self.routing_health, 4),
            "rto_ms": round(self.rto_ms, 1),
            "convergence_time_ms": round(self.convergence_time_ms, 1),
            "recovery_rate": round(self.recovery_rate, 4),
            "violation_count_60s": self.violation_count_60s,
            "node_count_total": self.node_count_total,
            "node_count_healthy": self.node_count_healthy,
            "anomaly_count": self.anomaly_count,
        }


class StabilityMetricsEngine:
    """
    Tracks cluster health over a rolling window and produces stability scores.

    Records:
      - violations (SBS, network, quorum)
      - node state changes (up/down/evicted)
      - RPC success/failure
      - convergence events
      - anomaly detections
    """

    def __init__(
        self,
        window_seconds: float = 60.0,
        violation_decay: float = 0.1,
        node_count: int = 3,
    ) -> None:
        self._window = window_seconds
        self._decay = violation_decay
        self._node_count = node_count
        self._lock = threading.Lock()

        # Rolling event buffers (timestamp, value)
        self._violations: deque[tuple[float, str, str]] = deque()  # (ts, subsystem, severity)
        self._recoveries: deque[tuple[float, str]] = deque()       # (ts, node_id)
        self._ops_success: deque[tuple[float, int]] = deque()      # (ts, count)
        self._ops_failure: deque[tuple[float, int]] = deque()     # (ts, count)
        self._anomalies: deque[tuple[float, str]] = deque()       # (ts, type)
        self._convergence_events: deque[tuple[float, float]] = deque()  # (ts, duration_ms)

        # Node tracking
        self._node_health: dict[str, str] = {}  # node_id → state
        self._healthy_node_count = node_count

        # Snapshot cache
        self._last_snapshot_ts = 0.0
        self._last_snapshot: StabilitySnapshot | None = None

        # Violation penalties per subsystem (for score calculation)
        self._penalty_weights = {
            "sbs": 0.4,
            "quorum": 0.3,
            "network": 0.2,
            "routing": 0.1,
        }

    # ── Record events ───────────────────────────────────────────────────

    def record_violation(
        self,
        subsystem: str = "sbs",
        severity: str = "critical",
    ) -> None:
        """Record a violation event."""
        with self._lock:
            now = time.monotonic()
            self._violations.append((now, subsystem, severity))
            self._anomalies.append((now, f"{subsystem}.{severity}"))

    def record_recovery(self, node_id: str, duration_ms: float = 0.0) -> None:
        """Record a node recovery event."""
        with self._lock:
            now = time.monotonic()
            self._recoveries.append((now, node_id))
            if node_id in self._node_health:
                self._node_health[node_id] = "healthy"
            self._healthy_node_count = sum(
                1 for s in self._node_health.values() if s == "healthy"
            )
            if duration_ms > 0:
                self._convergence_events.append((now, duration_ms))

    def record_node_down(self, node_id: str) -> None:
        with self._lock:
            self._node_health[node_id] = "down"
            self._healthy_node_count = sum(
                1 for s in self._node_health.values() if s == "healthy"
            )

    def record_node_up(self, node_id: str) -> None:
        with self._lock:
            self._node_health[node_id] = "healthy"
            self._healthy_node_count = sum(
                1 for s in self._node_health.values() if s == "healthy"
            )

    def record_op_success(self, count: int = 1) -> None:
        with self._lock:
            self._ops_success.append((time.monotonic(), count))

    def record_op_failure(self, count: int = 1) -> None:
        with self._lock:
            self._ops_failure.append((time.monotonic(), count))

    def record_convergence(self, duration_ms: float) -> None:
        with self._lock:
            self._convergence_events.append((time.monotonic(), duration_ms))

    def record_anomaly(self, anomaly_type: str) -> None:
        with self._lock:
            self._anomalies.append((time.monotonic(), anomaly_type))

    # ── Compute snapshot ─────────────────────────────────────────────────

    def get_snapshot(self, force: bool = False) -> StabilitySnapshot:
        """Compute stability snapshot (cached, refreshes every 1s)."""
        now = time.monotonic()
        if not force and (now - self._last_snapshot_ts) < 1.0 and self._last_snapshot is not None:
            return self._last_snapshot

        with self._lock:
            self._last_snapshot_ts = now
            self._last_snapshot = self._compute_snapshot(now)
            return self._last_snapshot

    def _compute_snapshot(self, now: float) -> StabilitySnapshot:
        # ── Prune old events ──────────────────────────────────────────────
        window = self._window
        cutoff = now - window

        def prune(deque_obj: deque) -> None:
            while deque_obj and deque_obj[0][0] < cutoff:
                deque_obj.popleft()

        prune(self._violations)
        prune(self._recoveries)
        prune(self._ops_success)
        prune(self._ops_failure)
        prune(self._anomalies)
        prune(self._convergence_events)

        # ── Subsystem scores ──────────────────────────────────────────────
        sbs_score = self._subsystem_score("sbs", cutoff, now)
        quorum_score = self._subsystem_score("quorum", cutoff, now)
        network_score = self._subsystem_score("network", cutoff, now)
        routing_score = self._subsystem_score("routing", cutoff, now)

        # ── Quorum health ─────────────────────────────────────────────────
        total = max(self._node_count, 1)
        healthy = max(self._healthy_node_count, 0)
        quorum_health = healthy / total

        # ── Network health ────────────────────────────────────────────────
        violations_in_window = len(self._violations)
        network_health = max(0.0, 1.0 - (violations_in_window * self._decay))

        # ── SBS health ────────────────────────────────────────────────────
        sbs_violations = sum(1 for _, sub, _ in self._violations if sub == "sbs")
        sbs_health = max(0.0, 1.0 - (sbs_violations * self._decay))

        # ── Routing health ───────────────────────────────────────────────
        routing_violations = sum(1 for _, sub, _ in self._violations if sub == "routing")
        routing_health = max(0.0, 1.0 - (routing_violations * self._decay))

        # ── Recovery rate ─────────────────────────────────────────────────
        total_ops = sum(c for _, c in self._ops_success) + sum(c for _, c in self._ops_failure)
        success_ops = sum(c for _, c in self._ops_success)
        recovery_rate = success_ops / max(total_ops, 1)

        # ── RTO ───────────────────────────────────────────────────────────
        rto_ms = self._estimate_rto(violations_in_window, quorum_health)

        # ── Convergence time ──────────────────────────────────────────────
        if self._convergence_events:
            convergence_time_ms = sum(d for _, d in self._convergence_events) / len(self._convergence_events)
        else:
            convergence_time_ms = 0.0

        # ── Weighted stability score ──────────────────────────────────────
        stability_score = (
            self._penalty_weights["sbs"] * sbs_score
            + self._penalty_weights["quorum"] * quorum_health
            + self._penalty_weights["network"] * network_health
            + self._penalty_weights["routing"] * routing_health
        )
        stability_score = max(0.0, min(1.0, stability_score))

        return StabilitySnapshot(
            ts=now,
            stability_score=stability_score,
            quorum_health=quorum_health,
            network_health=network_health,
            sbs_health=sbs_health,
            routing_health=routing_health,
            rto_ms=rto_ms,
            convergence_time_ms=convergence_time_ms,
            recovery_rate=recovery_rate,
            violation_count_60s=violations_in_window,
            node_count_total=self._node_count,
            node_count_healthy=self._healthy_node_count,
            anomaly_count=len(self._anomalies),
        )

    def _subsystem_score(
        self,
        subsystem: str,
        cutoff: float,
        now: float,
    ) -> float:
        violations = [
            (ts, sev) for ts, sub, sev in self._violations
            if sub == subsystem and ts >= cutoff
        ]
        if not violations:
            return 1.0
        critical = sum(1 for _, sev in violations if sev == "critical")
        warning = sum(1 for _, sev in violations if sev == "warning")
        penalty = critical * 0.3 + warning * 0.1
        return max(0.0, 1.0 - penalty)

    def _estimate_rto(self, violations: int, quorum_health: float) -> float:
        """
        Heuristic RTO estimation:
        - Baseline: 500ms
        - +200ms per violation
        - +500ms if quorum_health < 0.5
        """
        base_ms = 500.0
        per_violation_ms = 200.0
        rto = base_ms + (violations * per_violation_ms)
        if quorum_health < 0.5:
            rto += 500.0
        return min(rto, 10000.0)  # cap at 10s

    # ── Alert threshold ──────────────────────────────────────────────────

    def is_stable(self, threshold: float = 0.7) -> bool:
        return self.get_snapshot().is_healthy(threshold)

    def is_critical(self, threshold: float = 0.3) -> bool:
        return self.get_snapshot().stability_score < threshold

    # ── History ──────────────────────────────────────────────────────────

    def get_recent_violations(self, last_n: int = 10) -> list[tuple[float, str, str]]:
        with self._lock:
            return sorted(self._violations, key=lambda x: -x[0])[:last_n]

    def dump(self) -> dict:
        snap = self.get_snapshot()
        return {
            "snapshot": snap.to_dict(),
            "is_healthy": snap.is_healthy(),
            "is_critical": self.is_critical(),
        }
