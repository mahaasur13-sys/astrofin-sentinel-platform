from dataclasses import dataclass


@dataclass
class FeedbackSignal:
    layer: str
    urgency: float
    stability_impact: float


class FeedbackPrioritySolver:
    """
    Computes global priority of feedback loops.
    priority = urgency * 0.7 + stability_impact * 0.3
    """

    URGENCY_WEIGHT = 0.7
    STABILITY_WEIGHT = 0.3

    def compute_priority(self, signal: FeedbackSignal) -> float:
        return signal.urgency * self.URGENCY_WEIGHT + signal.stability_impact * self.STABILITY_WEIGHT

    def rank(self, signals: dict[str, FeedbackSignal]) -> dict[str, float]:
        return {
            k: self.compute_priority(v)
            for k, v in signals.items()
        }

    def rank_sorted(self, signals: dict[str, FeedbackSignal]) -> list[tuple[str, float]]:
        """Return [(layer, priority), ...] sorted highest-first."""
        scored = self.rank(signals)
        return sorted(scored.items(), key=lambda x: -x[1])
