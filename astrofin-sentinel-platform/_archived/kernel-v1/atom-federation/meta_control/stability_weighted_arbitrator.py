"""
StabilityWeightedArbitrator — v7.8
ControlArbitrator that adjusts per-source weights based on ProofFeedbackController.
"""
from __future__ import annotations

from dataclasses import dataclass

from meta_control.proof_feedback_controller import WeightDelta
from orchestration import ControlArbitrator, ControlSignal


@dataclass
class SourceWeight:
    name: str
    base_priority: float
    stability_bonus: float = 0.0
    drift_penalty: float = 0.0

    @property
    def effective_priority(self) -> float:
        return max(0.0, self.base_priority + self.stability_bonus - self.drift_penalty)


class StabilityWeightedArbitrator(ControlArbitrator):
    """
    ControlArbitrator extended with per-source stability weights.
    Weights are adjusted by ProofFeedbackController after each temporal window.
    """

    def __init__(self):
        super().__init__()
        self._source_weights: dict[str, SourceWeight] = {}

    def register_source(self, source: str, base_priority: float):
        if source not in self._source_weights:
            self._source_weights[source] = SourceWeight(name=source, base_priority=base_priority)

    def apply_deltas(self, deltas: list[WeightDelta]):
        for delta in deltas:
            if delta.source == "system":
                # Apply to all registered sources
                for sw in self._source_weights.values():
                    sw.stability_bonus += delta.priority_adjustment
                continue
            if delta.source not in self._source_weights:
                self._source_weights[delta.source] = SourceWeight(
                    name=delta.source, base_priority=0.5
                )
            sw = self._source_weights[delta.source]
            if delta.priority_adjustment > 0:
                sw.stability_bonus += delta.priority_adjustment
            else:
                sw.drift_penalty += abs(delta.priority_adjustment)

    def resolve(self) -> ControlSignal:
        """Resolve using effective_priority (base + bonus - penalty)."""
        if not self._signals:
            raise RuntimeError("No control signals pending")

        best: ControlSignal | None = None
        best_score = -1.0

        for sig in list(self._signals):
            sw = self._source_weights.get(sig.source)
            score = sw.effective_priority if sw else sig.priority
            if score > best_score:
                best_score = score
                best = sig
            elif score == best_score and best is not None:
                # tie-break alphabetically
                if sig.source < best.source:
                    best = sig

        if best is not None:
            self._signals.remove(best)

        return best

    def effective_weight(self, source: str) -> float:
        sw = self._source_weights.get(source)
        return sw.effective_priority if sw else 0.0

    def audit_trail(self) -> dict:
        return {name: {"effective": sw.effective_priority, "base": sw.base_priority,
                       "bonus": sw.stability_bonus, "penalty": sw.drift_penalty}
                for name, sw in self._source_weights.items()}
