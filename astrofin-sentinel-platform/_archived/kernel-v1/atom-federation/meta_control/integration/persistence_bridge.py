"""
Persistence Bridge — v8.0
Injects v8 persistence into v7.x gain/proof/coherence loops.

Mapping to real persistence API:
  - StateWindowStore.record_tick(source_states, control_weights, global_gain, outcome) → tick
  - StateWindowStore.window() → list[TickRecord]
  - StateWindowStore.depth → int
  - StabilityLedger.record(source, stability, violated) → None
  - StabilityLedger.get_ledger(source) → SourceLedger | None
  - StabilityLedger.global_trend() → StabilityTrend
  - StabilityLedger.is_coherent(source) → bool
  - DecisionMemory.record(source, priority, payload, proof_verdict, temporal_confidence, outcome) → id
  - DecisionMemory.find_similar(payload, k) → list[tuple[DecisionRecord, float]]
"""
from __future__ import annotations

from dataclasses import dataclass

from meta_control.persistence.decision_memory import DecisionMemory
from meta_control.persistence.stability_ledger import StabilityLedger
from meta_control.persistence.state_window_store import StateWindowStore
from meta_control.proof_feedback_controller import ProofFeedbackController, WeightDelta
from meta_control.temporal_gain_scheduler import TemporalGainScheduler
from proof.temporal_verifier import TemporalVerificationReport

# ─── Stability-aware gain modulation ──────────────────────────────────────────

@dataclass
class StabilityAwareGainAdjustment:
    source: str
    multiplier: float
    reason: str
    source_stability: float = 0.0
    global_trend: float = 0.0
    window_depth: int = 0


class GainModulator:
    """
    TemporalGainScheduler extended with persistence-backed stability signals.

    gain(source, t) = f(base_gain, ledger_stability(source),
                        ledger_trend, window_depth, global_coherence)
    """

    def __init__(
        self,
        scheduler: TemporalGainScheduler,
        stability_ledger: StabilityLedger,
        state_window: StateWindowStore,
        stability_lookback: int = 5,
    ):
        self.scheduler = scheduler
        self.ledger = stability_ledger
        self.state_window = state_window
        self.stability_lookback = stability_lookback

    def compute_aware_adjustments(
        self,
        report: TemporalVerificationReport,
        base_gains: dict[str, float],
    ) -> list[StabilityAwareGainAdjustment]:
        raw_adjustments = self.scheduler.compute_adjustments(report, base_gains)

        window_depth = self.state_window.depth
        trend_obj = self.ledger.global_trend()
        global_trend = (
            1.0 if trend_obj.improving
            else (-1.0 if trend_obj.degrading else 0.0)
        )

        enriched: list[StabilityAwareGainAdjustment] = []

        for adj in raw_adjustments:
            if adj.source == "__global__":
                trend_signal = 1.0 + global_trend * 0.1
                depth_signal = min(1.2, window_depth / max(1, self.stability_lookback))
                modulated = adj.multiplier * trend_signal * depth_signal
                enriched.append(StabilityAwareGainAdjustment(
                    source="__global__",
                    multiplier=modulated,
                    reason=adj.reason,
                    source_stability=report.overall_stability,
                    global_trend=global_trend,
                    window_depth=window_depth,
                ))
            else:
                ls = self.ledger.get_ledger(adj.source)
                source_stability = ls.avg_stability if ls and ls.sample_count > 0 else 0.5
                stability_signal = source_stability / 0.75
                modulated = adj.multiplier * stability_signal
                enriched.append(StabilityAwareGainAdjustment(
                    source=adj.source,
                    multiplier=modulated,
                    reason=adj.reason,
                    source_stability=source_stability,
                    global_trend=global_trend,
                    window_depth=window_depth,
                ))

        return enriched

    def apply_aware(
        self,
        base_gains: dict[str, float],
        adjustments: list[StabilityAwareGainAdjustment],
    ) -> dict[str, float]:
        result: dict[str, float] = {}
        global_mult = 1.0

        for adj in adjustments:
            if adj.source == "__global__":
                global_mult = adj.multiplier
            else:
                result[adj.source] = base_gains.get(adj.source, 0.0) * adj.multiplier

        for source, base in base_gains.items():
            if source not in result:
                result[source] = base * global_mult

        return result


# ─── Outcome-aware weight modulation ──────────────────────────────────────────

@dataclass
class OutcomeAwareWeightDelta:
    source: str
    priority_adjustment: float
    reason: str
    similar_decisions_count: int = 0
    avg_outcome_score: float = 0.0
    causal_confidence: float = 0.0


class WeightModulator:
    """
    ProofFeedbackController extended with persistence-backed outcome memory.

    weight_delta(source, t) = f(raw_delta, avg_outcome_history(source),
                                 causal_confidence_from_chain)
    """

    def __init__(
        self,
        controller: ProofFeedbackController,
        decision_memory: DecisionMemory,
        causal_confidence_bias: float = 0.05,
    ):
        self.controller = controller
        self.memory = decision_memory
        self.bias = causal_confidence_bias

    def compute_weight_deltas(
        self,
        report: TemporalVerificationReport,
    ) -> list[OutcomeAwareWeightDelta]:
        raw_deltas = self.controller.compute(report)
        causal_conf = report.stability.causal_coherence
        enriched: list[OutcomeAwareWeightDelta] = []

        for delta in raw_deltas:
            if delta.source == "system":
                signal = 1.0 + (causal_conf - 0.5) * self.bias
                enriched.append(OutcomeAwareWeightDelta(
                    source="system",
                    priority_adjustment=delta.priority_adjustment * signal,
                    reason=delta.reason,
                    causal_confidence=causal_conf,
                ))
            else:
                past = self.memory.find_similar(
                    {"source": delta.source}, k=5,
                )
                n = len(past)
                scored = [rec for rec, _ in past if rec.outcome is not None]
                avg_score = (
                    sum(r.outcome for r in scored) / len(scored)
                    if scored else 0.5
                )
                history_signal = avg_score
                enriched.append(OutcomeAwareWeightDelta(
                    source=delta.source,
                    priority_adjustment=delta.priority_adjustment * history_signal,
                    reason=delta.reason,
                    similar_decisions_count=n,
                    avg_outcome_score=avg_score,
                    causal_confidence=causal_conf,
                ))

        return enriched


# ─── Persistence-aware coherence enrichment ───────────────────────────────────

@dataclass
class CoherenceEnrichment:
    base_coherence: float
    persistence_delta: float
    enriched_coherence: float
    trend: float
    window_depth: int
    source_count: int
    coherence_sources: list[str]


class CoherenceEnricher:
    """
    coherence(t) = base_coherence(v7) + Δ(persistence)

    Δ incorporates:
    - StabilityLedger: per-source stability + trend
    - StateWindowStore: tick window depth + state diversity
    """

    def __init__(
        self,
        state_window: StateWindowStore,
        stability_ledger: StabilityLedger,
        decision_memory: DecisionMemory,
        coherence_weight_stability: float = 0.4,
        coherence_weight_trend: float = 0.3,
        coherence_weight_depth: float = 0.3,
    ):
        self.state_window = state_window
        self.ledger = stability_ledger
        self.memory = decision_memory
        self.w_stability = coherence_weight_stability
        self.w_trend = coherence_weight_trend
        self.w_depth = coherence_weight_depth

    def enrich(
        self,
        base_coherence: float,
        active_sources: list[str],
    ) -> CoherenceEnrichment:
        window_depth = self.state_window.depth

        stability_scores = []
        for src in active_sources:
            ls = self.ledger.get_ledger(src)
            if ls and ls.sample_count > 0:
                stability_scores.append(ls.avg_stability)
        avg_stability = sum(stability_scores) / len(stability_scores) if stability_scores else 0.0

        trend_obj = self.ledger.global_trend()
        trend = (
            1.0 if trend_obj.improving
            else (-1.0 if trend_obj.degrading else 0.0)
        )

        if window_depth > 0:
            window = self.state_window.window()
            unique_states = len({t.tick for t in window})
            depth_signal = min(1.0, unique_states / max(1, window_depth))
        else:
            depth_signal = 0.0

        persistence_delta = (
            self.w_stability * avg_stability
            + self.w_trend * (trend + 1.0) * 0.5
            + self.w_depth * depth_signal
        )

        coherent_srcs = [
            src for src in active_sources
            if self.ledger.is_coherent(src)
        ]

        return CoherenceEnrichment(
            base_coherence=base_coherence,
            persistence_delta=persistence_delta,
            enriched_coherence=base_coherence + persistence_delta,
            trend=trend,
            window_depth=window_depth,
            source_count=len(active_sources),
            coherence_sources=coherent_srcs,
        )


# ─── Integration report ────────────────────────────────────────────────────────

@dataclass
class IntegrationReport:
    gain_adjustments: list[StabilityAwareGainAdjustment]
    weight_deltas: list[OutcomeAwareWeightDelta]
    coherence: CoherenceEnrichment
    tick: int

    def to_dict(self) -> dict:
        return {
            "tick": self.tick,
            "gains": [
                {"source": a.source, "multiplier": a.multiplier, "reason": a.reason,
                 "stability": a.source_stability, "trend": a.global_trend,
                 "window_depth": a.window_depth}
                for a in self.gain_adjustments
            ],
            "weights": [
                {"source": d.source, "delta": d.priority_adjustment,
                 "reason": d.reason, "past_count": d.similar_decisions_count,
                 "avg_outcome": d.avg_outcome_score}
                for d in self.weight_deltas
            ],
            "coherence": {
                "base": self.coherence.base_coherence,
                "delta": self.coherence.persistence_delta,
                "enriched": self.coherence.enriched_coherence,
                "trend": self.coherence.trend,
                "window_depth": self.coherence.window_depth,
                "sources": self.coherence.coherence_sources,
            },
        }


class PersistenceBridge:
    """
    Top-level integration point: v7.x controller + v8 persistence layer.

    Usage:
        bridge = PersistenceBridge(tick=42)

        # Record current tick in persistence layer
        bridge.state_window.record_tick(
            source_states={"drl": 0.85, "sbs": 0.78},
            control_weights={"drl": 0.6, "sbs": 0.4},
            global_gain=1.0,
            outcome=None,
        )
        bridge.ledger.record("drl", stability=0.85, violated=False)
        bridge.memory.record(source="drl", priority=0.5, payload={},
                            proof_verdict=True, temporal_confidence=0.8, outcome=None)

        # Integrate v7 report with v8 persistence
        report = bridge.integrate(
            v7_report=temporal_verification_report,
            base_gains={"drl": 0.5, "sbs": 0.5},
            base_coherence=0.82,
            active_sources=["drl", "sbs"],
        )
        final_gains   = bridge.gain_modulator.apply_aware(base_gains, report.gain_adjustments)
        final_weights = bridge.apply_weight_deltas(report.weight_deltas)
        enriched_c    = report.coherence.enriched_coherence
    """

    def __init__(
        self,
        tick: int = 0,
        stability_ledger: StabilityLedger | None = None,
        state_window: StateWindowStore | None = None,
        decision_memory: DecisionMemory | None = None,
        scheduler: TemporalGainScheduler | None = None,
        feedback_controller: ProofFeedbackController | None = None,
    ):
        self.tick = tick
        self.ledger = stability_ledger or StabilityLedger()
        self.state_window = state_window or StateWindowStore()
        self.memory = decision_memory or DecisionMemory(max_memory=200)
        self.scheduler = scheduler or TemporalGainScheduler()
        self.feedback_controller = feedback_controller or ProofFeedbackController()
        self.gain_modulator = GainModulator(
            self.scheduler, self.ledger, self.state_window,
        )
        self.weight_modulator = WeightModulator(
            self.feedback_controller, self.memory,
        )
        self.coherence_enricher = CoherenceEnricher(
            self.state_window, self.ledger, self.memory,
        )

    def integrate(
        self,
        v7_report: TemporalVerificationReport,
        base_gains: dict[str, float],
        base_coherence: float,
        active_sources: list[str] | None = None,
    ) -> IntegrationReport:
        if active_sources is None:
            active_sources = list(base_gains.keys())

        gain_adj = self.gain_modulator.compute_aware_adjustments(v7_report, base_gains)
        weight_deltas = self.weight_modulator.compute_weight_deltas(v7_report)
        coherence = self.coherence_enricher.enrich(base_coherence, active_sources)

        return IntegrationReport(
            gain_adjustments=gain_adj,
            weight_deltas=weight_deltas,
            coherence=coherence,
            tick=self.tick,
        )

    def apply_weight_deltas(
        self,
        deltas: list[OutcomeAwareWeightDelta],
    ) -> list[WeightDelta]:
        return [
            WeightDelta(
                source=d.source,
                priority_adjustment=d.priority_adjustment,
                reason=d.reason,
            )
            for d in deltas
        ]
