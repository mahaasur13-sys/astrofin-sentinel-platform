"""
ProofFeedbackController — v7.8
Converts TemporalVerificationReport into arbitration weight adjustments.
"""
from __future__ import annotations

from dataclasses import dataclass

from proof.temporal_verifier import TemporalVerificationReport


@dataclass
class WeightDelta:
    source: str
    priority_adjustment: float   # +1 = promote, -1 = demote
    reason: str


class ProofFeedbackController:
    """
    Reads proof verdicts and emits WeightDelta for each source.
    Converts "the reasoning was unstable" → "reduce that source's arbitration weight".
    """

    def __init__(
        self,
        stability_weight_boost: float = 0.1,
        drift_penalty: float = 0.15,
        causal_break_penalty: float = 0.25,
    ):
        self.stability_weight_boost = stability_weight_boost
        self.drift_penalty = drift_penalty
        self.causal_break_penalty = causal_break_penalty

    def compute(self, report: TemporalVerificationReport) -> list[WeightDelta]:
        drift_events = report.drift_report.events
        if report.is_stable:
            return self._stable_case(report)

        deltas: list[WeightDelta] = []

        # Per-source drift penalties
        for drift in drift_events:
            if drift.drift_type.value == "source_switch":
                deltas.append(WeightDelta(
                    source=drift.source,
                    priority_adjustment=-self.drift_penalty,
                    reason=f"source_switch from {drift.from_tick}→{drift.to_tick}",
                ))
            elif drift.drift_type.value == "reasoning_collapse":
                deltas.append(WeightDelta(
                    source=drift.source,
                    priority_adjustment=-self.drift_penalty * 1.5,
                    reason="reasoning_collapse: continuity dropped",
                ))
            elif drift.drift_type.value == "causal_break":
                deltas.append(WeightDelta(
                    source=drift.source,
                    priority_adjustment=-self.causal_break_penalty,
                    reason="causal_break: proof chain disconnected",
                ))
            elif drift.drift_type.value == "proof_regression":
                deltas.append(WeightDelta(
                    source=drift.source,
                    priority_adjustment=-self.drift_penalty * 2.0,
                    reason="proof_regression: validity collapsed",
                ))

        # Reward coherent sources (those NOT in drift events)
        coherent_sources = self._coherent_sources(report)
        for src in coherent_sources:
            deltas.append(WeightDelta(
                source=src,
                priority_adjustment=+self.stability_weight_boost,
                reason="coherent source: stable reasoning",
            ))

        return deltas

    def _stable_case(self, report: TemporalVerificationReport) -> list[WeightDelta]:
        """When the window is stable, reward all active sources slightly."""
        return [
            WeightDelta(source="system", priority_adjustment=+self.stability_weight_boost,
                        reason="window_stable: global boost")
        ]

    def _coherent_sources(self, report: TemporalVerificationReport) -> set[str]:
        drifting = {d.source for d in report.drift_report.events}
        sources: set[str] = set()
        for link in report.proof_chain.links:
            sources.add(link.record.source)
        return sources - drifting
