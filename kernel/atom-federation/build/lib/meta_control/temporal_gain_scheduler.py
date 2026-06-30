"""
TemporalGainScheduler — v7.8
Global gain scheduler that modulates per-source gains based on temporal stability.
Takes TemporalVerificationReport → adjusts gain multipliers.
"""
from __future__ import annotations

from dataclasses import dataclass

from proof.temporal_verifier import TemporalVerificationReport


@dataclass
class GainAdjustment:
    source: str
    multiplier: float   # multiply the base gain by this
    reason: str


class TemporalGainScheduler:
    """
    Modulates system-wide gain allocation based on proof-derived stability.

    Stable window   → increase global gain budget (system is trustworthy)
    Unstable window → decrease gain budget (reduce exposure to bad decisions)
    Drifting source → reduce that specific source's gain
    """

    def __init__(
        self,
        base_global_gain: float = 1.0,
        stability_gain_boost: float = 0.15,
        drift_gain_reduction: float = 0.20,
        stability_threshold: float = 0.75,
    ):
        self.base_global_gain = base_global_gain
        self.stability_gain_boost = stability_gain_boost
        self.drift_gain_reduction = drift_gain_reduction
        self.stability_threshold = stability_threshold

        # Current state
        self._global_multiplier: float = 1.0
        self._per_source_multipliers: dict[str, float] = {}
        self._window_history: list[float] = []  # stability scores

    def compute_adjustments(
        self,
        report: TemporalVerificationReport,
        base_gains: dict[str, float],
    ) -> list[GainAdjustment]:
        adjustments: list[GainAdjustment] = []
        self._window_history.append(report.overall_stability)
        if len(self._window_history) > 20:
            self._window_history.pop(0)

        # 1. Global multiplier based on window stability
        if report.is_stable:
            new_global = min(2.0, self._global_multiplier + self.stability_gain_boost)
        else:
            new_global = max(0.1, self._global_multiplier - self.drift_gain_reduction)
        self._global_multiplier = new_global

        adjustments.append(GainAdjustment(
            source="__global__",
            multiplier=new_global,
            reason=f"global stability={'stable' if report.is_stable else 'unstable'} "
                   f"(score={report.overall_stability:.3f})",
        ))

        # 2. Per-source adjustments based on drift events
        drifting_sources = {d.source for d in report.drift_events}
        for source in base_gains:
            if source == "__global__":
                continue
            if source in drifting_sources:
                adj = GainAdjustment(
                    source=source,
                    multiplier=1.0 - self.drift_gain_reduction,
                    reason=f"drifting source: {[d.drift_type.value for d in report.drift_events if d.source == source]}",
                )
                self._per_source_multipliers[source] = adj.multiplier
            else:
                # Coherent source — slight boost
                adj = GainAdjustment(
                    source=source,
                    multiplier=1.0 + self.stability_gain_boost * 0.5,
                    reason="coherent source",
                )
                self._per_source_multipliers[source] = adj.multiplier
            adjustments.append(adj)

        return adjustments

    def apply_adjustments(
        self,
        base_gains: dict[str, float],
        adjustments: list[GainAdjustment],
    ) -> dict[str, float]:
        """
        Apply the computed adjustments to base gains.
        Returns final per-source gains.
        """
        result: dict[str, float] = {}
        global_mult = 1.0

        for adj in adjustments:
            if adj.source == "__global__":
                global_mult = adj.multiplier
            else:
                self._per_source_multipliers[adj.source] = adj.multiplier

        for source, base in base_gains.items():
            mult = self._per_source_multipliers.get(source, 1.0)
            result[source] = base * mult * global_mult

        return result

    @property
    def global_multiplier(self) -> float:
        return self._global_multiplier

    def stability_trend(self) -> float:
        """Trend of stability over the last N windows: +1 = improving, -1 = degrading."""
        if len(self._window_history) < 5:
            return 0.0
        recent = self._window_history[-5:]
        # Simple linear slope
        n = len(recent)
        mean_x = (n - 1) / 2
        mean_y = sum(recent) / n
        num = sum((i - mean_x) * (v - mean_y) for i, v in enumerate(recent))
        den = sum((i - mean_x) ** 2 for i in range(n))
        if den == 0:
            return 0.0
        slope = num / den
        # Normalize to roughly [-1, 1]
        return max(-1.0, min(1.0, slope * 10))
