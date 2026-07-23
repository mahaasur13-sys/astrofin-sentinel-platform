from dataclasses import dataclass
from enum import Enum


class StabilityState(Enum):
    STABLE = "stable"
    WARNING = "warning"
    CRITICAL = "critical"
    COLLAPSE = "collapse"


@dataclass
class EnvelopeBounds:
    min_val: float
    max_val: float


@dataclass
class EnvelopeReport:
    state: StabilityState
    violation_score: float
    violated_metrics: dict[str, float]


class StabilityEnvelope:
    def __init__(self):
        self.bounds: dict[str, EnvelopeBounds] = {
            "plan_stability_index": EnvelopeBounds(0.6, 1.0),
            "coherence_drop_rate": EnvelopeBounds(0.0, 0.15),
            "replanning_frequency": EnvelopeBounds(0.0, 0.4),
            "oscillation_index": EnvelopeBounds(0.0, 0.3),
        }

    def check_metric(self, name: str, value: float) -> float:
        bounds = self.bounds[name]

        if value < bounds.min_val:
            return (bounds.min_val - value) / max(bounds.min_val, 1e-6)

        if value > bounds.max_val:
            return (value - bounds.max_val) / max(bounds.max_val, 1e-6)

        return 0.0

    def violation_score(self, metrics: dict[str, float]) -> float:
        total = 0.0
        count = 0

        for name, value in metrics.items():
            if name not in self.bounds:
                continue

            v = self.check_metric(name, value)
            total += v
            count += 1

        return total / max(count, 1)

    def classify(self, score: float) -> StabilityState:
        if score == 0.0:
            return StabilityState.STABLE
        elif score < 0.25:
            return StabilityState.WARNING
        elif score < 0.6:
            return StabilityState.CRITICAL
        else:
            return StabilityState.COLLAPSE

    def evaluate(self, metrics: dict[str, float]) -> EnvelopeReport:
        violations = {}

        for name, value in metrics.items():
            if name not in self.bounds:
                continue

            v = self.check_metric(name, value)
            if v > 0:
                violations[name] = v

        score = self.violation_score(metrics)
        state = self.classify(score)

        return EnvelopeReport(
            state=state,
            violation_score=score,
            violated_metrics=violations,
        )
