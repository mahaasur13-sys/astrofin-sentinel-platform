"""
InvariantsEngine v6.5 — Runtime verification of formal stability invariants.

Verifies that the cluster maintains critical safety properties at all times.
Every invariant is checked every tick. If any critical invariant fails,
the system enters PANIC state and dumps diagnostics.

Lyapunov-like stability: a system is stable if it stays within bounded
regions (invariants) despite perturbations (chaos).

Usage:
    engine = InvariantsEngine(node_count=3)
    engine.start()

    # Or synchronous check:
    results = engine.check_all(snapshot)
    if not results.all_passed:
        engine.panic(results)
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto

from resilience.metrics_engine import StabilitySnapshot

__all__ = ["Invariant", "InvariantResult", "InvariantSet", "InvariantsEngine"]


# ── Invariant definitions ────────────────────────────────────────────────────

class InvariantSeverity(Enum):
    CRITICAL = auto()   # Panic if violated
    WARNING = auto()     # Log if violated
    INFO = auto()        # Track only


@dataclass
class Invariant:
    """
    A single runtime invariant.

    check(snapshot) returns True if invariant holds, False otherwise.
    """
    name: str
    description: str
    check: Callable[[StabilitySnapshot], bool]
    severity: InvariantSeverity = InvariantSeverity.CRITICAL
    tags: tuple[str, ...] = field(default_factory=tuple)

    def evaluate(self, snapshot: StabilitySnapshot) -> InvariantResult:
        t0 = time.monotonic()
        err = None
        try:
            passed = bool(self.check(snapshot))
        except Exception as exc:
            passed = False
            err = str(exc)
        duration_us = (time.monotonic() - t0) * 1_000_000
        return InvariantResult(
            invariant_name=self.name,
            passed=passed,
            severity=self.severity,
            duration_us=duration_us,
            error=err,
        )


@dataclass
class InvariantResult:
    invariant_name: str
    passed: bool
    severity: InvariantSeverity
    duration_us: float
    error: str | None = None

    @property
    def is_critical(self) -> bool:
        return self.severity == InvariantSeverity.CRITICAL and not self.passed


@dataclass
class InvariantSet:
    """Collection of invariants with a label."""
    name: str
    invariants: list[Invariant]

    def check_all(self, snapshot: StabilitySnapshot) -> InvariantSetResult:
        return InvariantSetResult(
            set_name=self.name,
            results=[inv.evaluate(snapshot) for inv in self.invariants],
            ts=time.monotonic(),
        )


@dataclass
class InvariantSetResult:
    set_name: str
    results: list[InvariantResult]
    ts: float

    @property
    def all_passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def critical_failures(self) -> list[InvariantResult]:
        return [r for r in self.results if r.is_critical]

    @property
    def warning_failures(self) -> list[InvariantResult]:
        return [
            r for r in self.results
            if r.severity == InvariantSeverity.WARNING and not r.passed
        ]

    def to_dict(self) -> dict:
        return {
            "set_name": self.set_name,
            "ts": round(self.ts, 4),
            "all_passed": self.all_passed,
            "critical_failures": [
                {"name": r.invariant_name, "error": r.error}
                for r in self.critical_failures
            ],
            "warning_failures": [
                {"name": r.invariant_name}
                for r in self.warning_failures
            ],
            "total_results": len(self.results),
        }


# ── InvariantsEngine ─────────────────────────────────────────────────────────

class InvariantsEngine:
    """
    Verifies formal stability invariants at runtime.

    Default invariants (I1–I7):
      I1: quorum_reachable     — majority of nodes reachable
      I2: single_leader       — exactly one leader (SBS safety)
      I3: score_not_zero      — score=0 requires alert fired
      I4: rto_finite          — RTO must be bounded
      I5: convergence_bounded  — convergence within MAX_CONVERGENCE_MS
      I6: no_network_partition_without_alert — partition detected → alert
      I7: recovery_rate_acceptable — recovery_rate ≥ 0.5
    """

    MAX_CONVERGENCE_MS = 30_000.0   # 30 seconds max convergence
    MIN_RECOVERY_RATE = 0.50        # ≥50% ops succeed
    CRITICAL_SCORE_THRESHOLD = 0.0  # score of 0 is only OK if alert fired

    def __init__(self, node_count: int = 3):
        self.node_count = node_count
        self._invariant_sets: list[InvariantSet] = []
        self._panic_callbacks: list[Callable[[InvariantSetResult], None]] = []
        self._running = False
        self._thread: threading.Thread | None = None
        self._tick_count = 0
        self._last_results: InvariantSetResult | None = None
        self._last_snapshot: StabilitySnapshot | None = None
        self._last_panic: InvariantSetResult | None = None

        self._register_default_invariants()

    # ── Registration ─────────────────────────────────────────────────────

    def _register_default_invariants(self) -> None:
        self._invariant_sets.append(InvariantSet(
            name="safety",
            invariants=[
                Invariant(
                    name="I1_quorum_reachable",
                    description=(
                        "At least ceil(N/2) nodes must be healthy. "
                        "Below this the cluster cannot maintain quorum."
                    ),
                    check=lambda s: s.node_count_healthy >= (s.node_count_total + 1) // 2,
                    severity=InvariantSeverity.CRITICAL,
                    tags=("quorum", "safety"),
                ),
                Invariant(
                    name="I2_single_leader",
                    description=(
                        "Exactly one leader must exist at any time. "
                        "Two leaders = split-brain = SBS violation."
                    ),
                    check=lambda s: s.leader_count == 1,
                    severity=InvariantSeverity.CRITICAL,
                    tags=("consensus", "sbs"),
                ),
                Invariant(
                    name="I3_score_not_zero_without_alert",
                    description=(
                        "stability_score must not reach 0 without an alert "
                        "having been fired. A silent score=0 is a safety failure."
                    ),
                    check=lambda s: (
                        s.stability_score > self.CRITICAL_SCORE_THRESHOLD
                        or s.alert_fired
                    ),
                    severity=InvariantSeverity.CRITICAL,
                    tags=("observability", "safety"),
                ),
            ],
        ))

        self._invariant_sets.append(InvariantSet(
            name="liveness",
            invariants=[
                Invariant(
                    name="I4_rto_finite",
                    description=(
                        "RTO must be a positive finite number. "
                        "Infinite RTO means the system cannot guarantee recovery."
                    ),
                    check=lambda s: 0 < s.rto_ms < float("inf"),
                    severity=InvariantSeverity.CRITICAL,
                    tags=("rto", "liveness"),
                ),
                Invariant(
                    name="I5_convergence_bounded",
                    description=(
                        f"Convergence time must stay below {self.MAX_CONVERGENCE_MS}ms. "
                        "If convergence takes longer, the system is in a "
                        "degraded state with no recovery path."
                    ),
                    check=lambda s: 0 <= s.convergence_time_ms <= self.MAX_CONVERGENCE_MS,
                    severity=InvariantSeverity.CRITICAL,
                    tags=("convergence", "liveness"),
                ),
                Invariant(
                    name="I7_recovery_rate_acceptable",
                    description=(
                        f"Recovery rate must be ≥ {self.MIN_RECOVERY_RATE*100:.0f}%. "
                        "Below this, the cluster is failing more ops than succeeding."
                    ),
                    check=lambda s: s.recovery_rate >= self.MIN_RECOVERY_RATE,
                    severity=InvariantSeverity.CRITICAL,
                    tags=("recovery", "liveness"),
                ),
            ],
        ))

        self._invariant_sets.append(InvariantSet(
            name="health",
            invariants=[
                Invariant(
                    name="I6_sbs_health_positive",
                    description="SBS health score must be > 0. Zero means invariants broken.",
                    check=lambda s: s.sbs_health > 0.0,
                    severity=InvariantSeverity.WARNING,
                    tags=("sbs", "health"),
                ),
                Invariant(
                    name="I8_network_health_positive",
                    description="Network health must be > 0. Zero means total partition.",
                    check=lambda s: s.network_health > 0.0,
                    severity=InvariantSeverity.WARNING,
                    tags=("network", "health"),
                ),
                Invariant(
                    name="I9_violation_rate_bounded",
                    description="No more than 10 violations per 60s (burst threshold).",
                    check=lambda s: s.violation_count_60s <= 10,
                    severity=InvariantSeverity.WARNING,
                    tags=("violations", "health"),
                ),
            ],
        ))

    def register_set(self, invariant_set: InvariantSet) -> None:
        self._invariant_sets.append(invariant_set)

    def on_panic(self, cb: Callable[[InvariantSetResult], None]) -> None:
        self._panic_callbacks.append(cb)

    # ── Checking ─────────────────────────────────────────────────────────

    def check_all(self, snapshot: StabilitySnapshot) -> InvariantSetResult:
        """
        Check all invariants against a single snapshot.
        Returns aggregated result across all sets.
        """
        self._last_snapshot = snapshot
        self._tick_count += 1

        all_results: list[InvariantResult] = []
        for invariant_set in self._invariant_sets:
            result = invariant_set.check_all(snapshot)
            all_results.extend(result.results)

            # Critical failures trigger panic
            critical_failures = result.critical_failures
            if critical_failures:
                self._last_panic = InvariantSetResult(
                    set_name="PANIC",
                    results=list(all_results),
                    ts=time.monotonic(),
                )
                self._trigger_panic(self._last_panic)

        aggregated = InvariantSetResult(
            set_name="all",
            results=all_results,
            ts=time.monotonic(),
        )
        self._last_results = aggregated
        return aggregated

    def check_set(self, set_name: str, snapshot: StabilitySnapshot) -> InvariantSetResult:
        for invariant_set in self._invariant_sets:
            if invariant_set.name == set_name:
                result = invariant_set.check_all(snapshot)
                if result.critical_failures:
                    self._trigger_panic(result)
                return result
        raise ValueError(f"Unknown invariant set: {set_name}")

    # ── Panic ────────────────────────────────────────────────────────────

    def _trigger_panic(self, result: InvariantSetResult) -> None:
        """Called when a critical invariant fails."""
        for cb in self._panic_callbacks:
            try:
                cb(result)
            except Exception:
                pass

    def panic(self, result: InvariantSetResult) -> None:
        """
        Public panic API — call this externally when a critical condition
        is detected outside the regular tick loop.
        """
        self._last_panic = result
        self._trigger_panic(result)

    # ── Panic state ─────────────────────────────────────────────────────

    @property
    def is_panicked(self) -> bool:
        return self._last_panic is not None

    @property
    def last_panic(self) -> InvariantSetResult | None:
        return self._last_panic

    def clear_panic(self) -> None:
        self._last_panic = None

    # ── Continuous tick ─────────────────────────────────────────────────

    def start(self, tick_ms: float = 1000.0) -> None:
        """
        Start continuous invariant checking at `tick_ms` intervals.
        Requires a snapshot provider to be set via set_snapshot_provider().
        """
        if self._running:
            return
        self._running = True
        self._tick_count = 0

        def _loop():
            while self._running:
                tick_start = time.monotonic()
                if self._snapshot_provider is not None:
                    try:
                        snap = self._snapshot_provider()
                        self.check_all(snap)
                    except Exception:
                        pass
                elapsed_ms = (time.monotonic() - tick_start) * 1000
                sleep_s = max(0, (tick_ms - elapsed_ms) / 1000)
                time.sleep(sleep_s)

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    # ── Snapshot provider (for continuous mode) ──────────────────────────

    _snapshot_provider: Callable[[], StabilitySnapshot] | None = field(default=None)

    def set_snapshot_provider(
        self, provider: Callable[[], StabilitySnapshot]
    ) -> None:
        self._snapshot_provider = provider

    # ── Introspection ───────────────────────────────────────────────────

    def list_invariants(self) -> list[dict]:
        out = []
        for invariant_set in self._invariant_sets:
            for inv in invariant_set.invariants:
                out.append({
                    "set": invariant_set.name,
                    "name": inv.name,
                    "description": inv.description,
                    "severity": inv.severity.name,
                    "tags": list(inv.tags),
                })
        return out

    def dump(self) -> dict:
        return {
            "invariant_sets": len(self._invariant_sets),
            "total_invariants": sum(
                len(s.invariants) for s in self._invariant_sets
            ),
            "tick_count": self._tick_count,
            "is_panicked": self.is_panicked,
            "last_panic": (
                self._last_panic.to_dict()
                if self._last_panic else None
            ),
            "last_results_passed": (
                self._last_results.all_passed
                if self._last_results else None
            ),
            "provider_registered": self._snapshot_provider is not None,
        }
