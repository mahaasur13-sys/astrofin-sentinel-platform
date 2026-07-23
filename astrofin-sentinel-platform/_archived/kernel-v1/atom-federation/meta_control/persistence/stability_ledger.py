"""
stability_ledger.py
~~~~~~~~~~~~~~~~~~~~
Long-term stability aggregates per source.
Unlike StateWindowStore (bounded tick window), this accumulates:
  - per-source stability averages over configurable epochs
  - violation counts per source per epoch
  - global stability trend (improving / degrading / stable)

Provides the `is_coherent(source, threshold)` check used by
temporal_gain_scheduler to compute per-source gain multipliers.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class SourceLedger:
    """Accumulated stability stats for a single source over current epoch."""
    source: str
    total_stability: float = 0.0
    total_violations: int = 0
    sample_count: int = 0
    epoch_start: float = field(default_factory=time.time)

    @property
    def avg_stability(self) -> float:
        return self.total_stability / self.sample_count if self.sample_count else 1.0

    @property
    def violation_rate(self) -> float:
        return self.total_violations / self.sample_count if self.sample_count else 0.0

    def record(self, stability: float, violated: bool) -> None:
        self.total_stability += stability
        if violated:
            self.total_violations += 1
        self.sample_count += 1

    def reset(self) -> None:
        self.total_stability = 0.0
        self.total_violations = 0
        self.sample_count = 0
        self.epoch_start = time.time()


@dataclass
class StabilityTrend:
    """Global stability trend across all sources."""
    improving: bool
    stable: bool
    degrading: bool
    global_avg_stability: float
    global_violation_rate: float
    dominant_drift: str | None = None


class StabilityLedger:
    """
    Long-term stability accumulator with epoch-based reset.

    Tracks per-source stability and violation rates over configurable epochs.
    Used to determine:
      - which sources are coherent (stable_avg > threshold)
      - which sources are drifting (violation_rate > threshold)
      - global stability trend for TemporalGainScheduler
    """

    def __init__(
        self,
        epoch_duration: float = 300.0,
        coherence_threshold: float = 0.7,
        violation_threshold: float = 0.15,
    ) -> None:
        self._epoch_duration = epoch_duration
        self._coherence_threshold = coherence_threshold
        self._violation_threshold = violation_threshold
        self._ledgers: dict[str, SourceLedger] = defaultdict(
            lambda: SourceLedger(source="")
        )
        self._last_global_check = time.time()

    def _get_or_create_ledger(self, source: str) -> SourceLedger:
        """Get or create a ledger, assigning source name on first creation."""
        ledger = self._ledgers[source]
        if ledger.source == "":
            ledger.source = source
        return ledger

    def _try_epoch_reset(self, ledger: SourceLedger) -> None:
        """Reset epoch if duration exceeded. Called lazily on query, not on record."""
        elapsed = time.time() - ledger.epoch_start
        if elapsed >= self._epoch_duration:
            ledger.reset()

    # ─── core interface ───────────────────────────────────────────────────────

    def record(
        self,
        source: str,
        stability: float,
        violated: bool = False,
    ) -> None:
        """Record a stability sample for a source."""
        ledger = self._get_or_create_ledger(source)
        ledger.record(stability, violated)

    def is_coherent(self, source: str) -> bool:
        """True if source avg stability exceeds coherence_threshold."""
        ledger = self._ledgers.get(source)
        if ledger is None or ledger.sample_count == 0:
            return True  # no data → assume coherent
        self._try_epoch_reset(ledger)
        return ledger.avg_stability >= self._coherence_threshold

    def is_drifting(self, source: str) -> bool:
        """True if source violation rate exceeds violation_threshold."""
        ledger = self._ledgers.get(source)
        if ledger is None or ledger.sample_count == 0:
            return False  # no data → not drifting
        self._try_epoch_reset(ledger)
        return ledger.violation_rate >= self._violation_threshold

    def global_trend(self) -> StabilityTrend:
        """
        Compute global stability trend across all sources.
        Compares current epoch avg to the global average.
        """
        now = time.time()
        # Lazy epoch advance on all ledgers
        for ledger in self._ledgers.values():
            self._try_epoch_reset(ledger)

        all_avg = [l.avg_stability for l in self._ledgers.values() if l.sample_count > 0]
        all_viol = [l.violation_rate for l in self._ledgers.values() if l.sample_count > 0]
        global_avg = sum(all_avg) / len(all_avg) if all_avg else 1.0
        global_viol = sum(all_viol) / len(all_viol) if all_viol else 0.0

        improving = global_avg > 0.85
        degrading = global_viol > self._violation_threshold * 2
        stable = not improving and not degrading

        drifting = [(s, l.violation_rate) for s, l in self._ledgers.items()
                    if l.sample_count > 0 and l.violation_rate > self._violation_threshold]
        dominant = max(drifting, key=lambda x: x[1])[0] if drifting else None

        self._last_global_check = now
        return StabilityTrend(
            improving=improving,
            stable=stable,
            degrading=degrading,
            global_avg_stability=global_avg,
            global_violation_rate=global_viol,
            dominant_drift=dominant,
        )

    # ─── introspection ─────────────────────────────────────────────────────────

    def source_statuses(self) -> dict[str, dict[str, float | bool]]:
        """Quick dump of all source coherence/drift statuses."""
        return {
            source: {
                "avg_stability": ledger.avg_stability,
                "violation_rate": ledger.violation_rate,
                "is_coherent": self.is_coherent(source),
                "is_drifting": self.is_drifting(source),
                "sample_count": ledger.sample_count,
                "epoch_age_s": time.time() - ledger.epoch_start,
            }
            for source, ledger in self._ledgers.items()
        }

    def get_ledger(self, source: str) -> SourceLedger | None:
        return self._ledgers.get(source)

    @property
    def coherence_threshold(self) -> float:
        return self._coherence_threshold

    @property
    def violation_threshold(self) -> float:
        return self._violation_threshold
