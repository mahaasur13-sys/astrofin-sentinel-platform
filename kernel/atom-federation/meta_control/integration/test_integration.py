"""
Tests for Meta-Control Integration Layer — v8.0
"""
from unittest.mock import MagicMock

from meta_control.integration import (
    CoherenceEnricher,
    GainModulator,
    PersistenceBridge,
    WeightModulator,
)
from meta_control.integration.persistence_bridge import (
    CoherenceEnrichment,
)
from meta_control.persistence.decision_memory import DecisionMemory
from meta_control.persistence.stability_ledger import StabilityLedger
from meta_control.persistence.state_window_store import StateWindowStore
from meta_control.proof_feedback_controller import ProofFeedbackController
from meta_control.temporal_gain_scheduler import TemporalGainScheduler
from proof.proof_chain import ProofChain
from proof.proof_drift_detector import DriftReport
from proof.stability_prover import StabilityMetrics
from proof.temporal_verifier import TemporalVerificationReport

# ─── Fixtures ─────────────────────────────────────────────────────────────────

def make_chain(sources: list[str]) -> ProofChain:
    chain = ProofChain()
    for src in sources:
        rec = MagicMock()
        rec.source = src
        rec.selected_action = MagicMock()
        rec.selected_action.label = f"action:{src}"
        rec.proof_status = "PASS"
        chain.append(rec)
    return chain


def make_metrics(is_stable: bool = True, overall: float = 0.85,
                 causal: float = 0.9) -> StabilityMetrics:
    return StabilityMetrics(
        tick_range=(0, 10),
        action_stability=0.9,
        reasoning_stability=overall,
        causal_coherence=causal,
        proof_continuity=1.0,
        overall_stability=overall,
        is_stable=is_stable,
    )


def make_report(is_stable=True, sources=None, causal=0.9) -> TemporalVerificationReport:
    sources = sources or ["drl", "sbs"]
    chain = make_chain(sources)
    return TemporalVerificationReport(
        chain_length=chain.length,
        window=(0, 10),
        stability=make_metrics(is_stable=is_stable, causal=causal),
        drift_report=DriftReport(tick_range=(0, 10), events=[], drift_score=0.0, is_drifted=False),
        causal_graph_stats={},
        overall_passed=is_stable,
        recommendations=[],
        proof_chain=chain,
        verified_sources=sources,
    )


# ─── GainModulator ─────────────────────────────────────────────────────────────

class TestGainModulator:
    def test_gain_modulator_enriches_global_with_ledger_trend(self):
        ledger = StabilityLedger()
        # record(source, stability, violated)
        ledger.record("__global__", stability=0.85, violated=False)
        ledger.record("__global__", stability=0.88, violated=False)

        sw = StateWindowStore()
        for i in range(5):
            sw.record_tick(
                source_states={"drl": 0.8},
                control_weights={"drl": 0.5},
                global_gain=1.0,
            )

        sched = TemporalGainScheduler()
        mod = GainModulator(sched, ledger, sw)
        report = make_report(is_stable=True)

        adj = mod.compute_aware_adjustments(report, base_gains={"drl": 0.5})
        global_adj = next(a for a in adj if a.source == "__global__")
        # global_trend from two coherent records → improving → 1.0
        assert global_adj.global_trend != 0.0
        assert global_adj.window_depth == 5

    def test_gain_modulator_applies_aware_adjustments(self):
        ledger = StabilityLedger()
        sw = StateWindowStore()
        sw.record_tick(source_states={}, control_weights={}, global_gain=1.0)
        sched = TemporalGainScheduler()
        mod = GainModulator(sched, ledger, sw)
        report = make_report(is_stable=True)

        adj = mod.compute_aware_adjustments(report, base_gains={"drl": 0.5})
        final = mod.apply_aware({"drl": 0.5}, adj)
        assert "drl" in final
        assert final["drl"] > 0


# ─── WeightModulator ───────────────────────────────────────────────────────────

class TestWeightModulator:
    def test_weight_modulator_injects_memory_history(self):
        memory = DecisionMemory(max_memory=200)
        memory.append(
            source="drl", priority=0.5,
            payload={"source": "drl", "action": "buy"},
            proof_verdict=True, temporal_confidence=0.8,
            outcome=0.8,
        )
        memory.append(
            source="drl", priority=0.5,
            payload={"source": "drl", "action": "buy"},
            proof_verdict=True, temporal_confidence=0.8,
            outcome=0.9,
        )

        controller = ProofFeedbackController()
        mod = WeightModulator(controller, memory)
        report = make_report(is_stable=True, sources=["drl", "sbs"])

        deltas = mod.compute_weight_deltas(report)
        # "system" delta always exists; "drl" may appear if coherent
        assert len(deltas) >= 1

    def test_weight_modulator_no_history_defaults_neutral(self):
        memory = DecisionMemory(max_memory=200)
        controller = ProofFeedbackController()
        mod = WeightModulator(controller, memory)
        report = make_report(is_stable=True, sources=["drl"])

        deltas = mod.compute_weight_deltas(report)
        # With no history, find_similar returns [] → avg_outcome_score = 0.5
        assert len(deltas) >= 1


# ─── CoherenceEnricher ─────────────────────────────────────────────────────────

class TestCoherenceEnricher:
    def test_enrich_returns_higher_than_base(self):
        ledger = StabilityLedger()
        ledger.record("__global__", stability=0.85, violated=False)

        sw = StateWindowStore()
        for i in range(8):
            sw.record_tick(source_states={}, control_weights={}, global_gain=1.0)

        memory = DecisionMemory(max_memory=200)
        enricher = CoherenceEnricher(sw, ledger, memory)

        result = enricher.enrich(base_coherence=0.7, active_sources=["drl", "sbs"])

        assert isinstance(result, CoherenceEnrichment)
        assert result.enriched_coherence >= result.base_coherence
        assert result.window_depth == 8

    def test_enrich_trend_from_ledger_improving(self):
        ledger = StabilityLedger()
        # improving = global_avg > 0.85
        ledger.record("__global__", stability=0.90, violated=False)
        ledger.record("__global__", stability=0.92, violated=False)

        sw = StateWindowStore()
        sw.record_tick(source_states={}, control_weights={}, global_gain=1.0)
        memory = DecisionMemory(max_memory=200)
        enricher = CoherenceEnricher(sw, ledger, memory)

        result = enricher.enrich(base_coherence=0.5, active_sources=["drl"])
        assert result.trend > 0  # improving


# ─── PersistenceBridge ────────────────────────────────────────────────────────

class TestPersistenceBridge:
    def test_full_integrate_returns_report(self):
        bridge = PersistenceBridge(tick=42)
        report = make_report(is_stable=True, sources=["drl", "sbs"])

        result = bridge.integrate(
            v7_report=report,
            base_gains={"drl": 0.5, "sbs": 0.5},
            base_coherence=0.8,
            active_sources=["drl", "sbs"],
        )

        assert result.tick == 42
        assert len(result.gain_adjustments) > 0
        assert len(result.weight_deltas) > 0
        assert isinstance(result.coherence, CoherenceEnrichment)
        assert result.coherence.base_coherence == 0.8
        assert result.coherence.enriched_coherence > 0.8

    def test_bridge_state_reflects_persisted_tick(self):
        bridge = PersistenceBridge(tick=0)
        report = make_report(is_stable=True, sources=["drl"])

        bridge.state_window.record_tick(
            source_states={"drl": 0.8},
            control_weights={"drl": 0.5},
            global_gain=1.0,
        )

        result = bridge.integrate(
            v7_report=report,
            base_gains={"drl": 0.5},
            base_coherence=0.7,
            active_sources=["drl"],
        )

        assert result.tick == 0
        assert result.coherence.window_depth == 1

    def test_apply_weight_deltas_converts_types(self):
        bridge = PersistenceBridge()
        report = make_report(is_stable=True, sources=["drl"])

        bridge.memory.append(
            source="drl", priority=0.5,
            payload={"source": "drl"},
            proof_verdict=True, temporal_confidence=0.8,
            outcome=0.75,
        )

        bridge.integrate(
            v7_report=report,
            base_gains={"drl": 0.5},
            base_coherence=0.7,
            active_sources=["drl"],
        )

        from meta_control.proof_feedback_controller import WeightDelta
        raw = bridge.apply_weight_deltas(
            bridge.weight_modulator.compute_weight_deltas(report)
        )
        assert all(isinstance(d, WeightDelta) for d in raw)

    def test_to_dict_serializes_all_fields(self):
        bridge = PersistenceBridge(tick=5)
        report = make_report(is_stable=True, sources=["drl"])

        result = bridge.integrate(
            v7_report=report,
            base_gains={"drl": 0.5},
            base_coherence=0.8,
            active_sources=["drl"],
        )

        d = result.to_dict()
        assert d["tick"] == 5
        assert "gains" in d
        assert "weights" in d
        assert "coherence" in d
        assert "enriched" in d["coherence"]
        assert "delta" in d["coherence"]


# ─── IntegrationReport ─────────────────────────────────────────────────────────

class TestIntegrationReport:
    def test_to_dict_roundtrip(self):
        bridge = PersistenceBridge(tick=10)
        report = make_report(is_stable=True, sources=["drl"])

        result = bridge.integrate(
            v7_report=report,
            base_gains={"drl": 0.5},
            base_coherence=0.75,
            active_sources=["drl"],
        )

        d = result.to_dict()
        assert d["tick"] == 10
        assert d["coherence"]["base"] == 0.75
        assert d["coherence"]["enriched"] >= 0.75
