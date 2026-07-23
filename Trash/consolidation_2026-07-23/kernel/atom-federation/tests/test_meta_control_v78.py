"""
Tests for Meta-Adaptive Control Layer — v7.8
"""
from unittest.mock import MagicMock

import pytest

from meta_control import (
    DriftPolicyAdaptor,
    ProofFeedbackController,
    StabilityWeightedArbitrator,
    TemporalGainScheduler,
)
from meta_control.proof_feedback_controller import WeightDelta
from orchestration import ControlSignal
from proof.proof_chain import ProofChain
from proof.proof_drift_detector import DriftEvent, DriftReport, DriftType
from proof.stability_prover import StabilityMetrics
from proof.temporal_verifier import TemporalVerificationReport

# ─── Fixtures ──────────────────────────────────────────────────────────────────


def make_chain_with_sources(*sources: str) -> ProofChain:
    """Build a minimal chain with one link per source."""
    chain = ProofChain()
    for i, src in enumerate(sources):
        record = MagicMock()
        record.source = src
        record.selected_action = MagicMock()
        record.selected_action.label = f"action:{src}"
        record.proof_status = "PASS"
        chain.append(record)
    return chain


def make_stability_metrics(is_stable: bool = True, overall: float = 0.85) -> StabilityMetrics:
    return StabilityMetrics(
        tick_range=(0, 10),
        action_stability=0.9,
        reasoning_stability=overall,
        causal_coherence=0.9,
        proof_continuity=1.0,
        overall_stability=overall,
        is_stable=is_stable,
    )


def make_drift_report(events: list[DriftEvent] = None) -> DriftReport:
    return DriftReport(
        tick_range=(0, 10),
        events=events or [],
        drift_score=0.0,
        is_drifted=False,
    )


def make_report(
    is_stable: bool = True,
    stability: StabilityMetrics = None,
    drift_events: list[DriftEvent] = None,
    sources: list[str] = None,
) -> TemporalVerificationReport:
    chain = make_chain_with_sources(*(sources or ["drl", "sbs"]))
    stability = stability or make_stability_metrics(is_stable=is_stable)
    drift_report = make_drift_report(drift_events or [])
    return TemporalVerificationReport(
        chain_length=chain.length,
        window=(0, 10),
        stability=stability,
        drift_report=drift_report,
        causal_graph_stats={},
        overall_passed=is_stable,
        recommendations=[],
        proof_chain=chain,
        verified_sources=list(sources or ["drl", "sbs"]),
    )


# ─── ProofFeedbackController ─────────────────────────────────────────────────


class TestProofFeedbackController:
    def test_stable_window_emits_global_boost(self):
        ctrl = ProofFeedbackController()
        report = make_report(is_stable=True)
        deltas = ctrl.compute(report)
        assert any(d.source == "system" and d.priority_adjustment > 0 for d in deltas)

    def test_source_switch_drift_penalty(self):
        ctrl = ProofFeedbackController(drift_penalty=0.15)
        report = make_report(
            is_stable=False,
            drift_events=[
                DriftEvent(
                    from_tick=4, to_tick=5,
                    drift_type=DriftType.SOURCE_SWITCH,
                    severity=0.3, description="",
                    from_source="sbs", to_source="drl",
                )
            ],
            sources=["drl", "sbs"],
        )
        deltas = ctrl.compute(report)
        drift_deltas = [d for d in deltas if d.source == "system" and d.priority_adjustment < 0]
        assert len(drift_deltas) >= 1

    def test_reasoning_collapse_penalty_amplified(self):
        ctrl = ProofFeedbackController(drift_penalty=0.15)
        report = make_report(
            is_stable=False,
            drift_events=[
                DriftEvent(
                    from_tick=4, to_tick=5,
                    drift_type=DriftType.REASONING_COLLAPSE,
                    severity=0.4, description="",
                )
            ],
            sources=["sbs"],
        )
        deltas = ctrl.compute(report)
        penalty = next((d.priority_adjustment for d in deltas
                        if d.priority_adjustment < 0), 0.0)
        assert penalty == pytest.approx(-0.15 * 1.5)

    def test_causal_break_penalty(self):
        ctrl = ProofFeedbackController(causal_break_penalty=0.25)
        report = make_report(
            is_stable=False,
            drift_events=[
                DriftEvent(
                    from_tick=2, to_tick=3,
                    drift_type=DriftType.CAUSAL_BREAK,
                    severity=0.5, description="",
                )
            ],
            sources=["coherence"],
        )
        deltas = ctrl.compute(report)
        penalty = next((d.priority_adjustment for d in deltas
                        if d.priority_adjustment < 0), 0.0)
        assert penalty == -0.25

    def test_proof_regression_penalty_doubles(self):
        ctrl = ProofFeedbackController(drift_penalty=0.15)
        report = make_report(
            is_stable=False,
            drift_events=[
                DriftEvent(
                    from_tick=6, to_tick=7,
                    drift_type=DriftType.PROOF_REGRESSION,
                    severity=0.6, description="",
                )
            ],
            sources=["drl"],
        )
        deltas = ctrl.compute(report)
        penalty = next((d.priority_adjustment for d in deltas
                        if d.priority_adjustment < 0), 0.0)
        assert penalty == pytest.approx(-0.15 * 2.0)

    def test_coherent_source_gets_boost(self):
        ctrl = ProofFeedbackController(stability_weight_boost=0.1)
        report = make_report(
            is_stable=False,
            drift_events=[
                DriftEvent(
                    from_tick=4, to_tick=5,
                    drift_type=DriftType.SOURCE_SWITCH,
                    severity=0.3, description="",
                    from_source="sbs", to_source="drl",
                )
            ],
            sources=["drl", "sbs"],
        )
        deltas = ctrl.compute(report)
        boost = next((d.priority_adjustment for d in deltas
                      if d.source == "sbs"), 0.0)
        assert boost == 0.1


# ─── StabilityWeightedArbitrator ───────────────────────────────────────────────


class TestStabilityWeightedArbitrator:
    def test_register_source(self):
        arb = StabilityWeightedArbitrator()
        arb.register_source("drl", 0.8)
        assert arb.effective_weight("drl") == 0.8

    def test_apply_deltas_system_wide(self):
        arb = StabilityWeightedArbitrator()
        arb.register_source("drl", 0.5)
        arb.register_source("sbs", 0.5)
        arb.apply_deltas([WeightDelta(source="system", priority_adjustment=0.1,
                                       reason="stable")])
        assert arb.effective_weight("drl") == pytest.approx(0.6)
        assert arb.effective_weight("sbs") == pytest.approx(0.6)

    def test_drift_penalty_capped_at_zero(self):
        arb = StabilityWeightedArbitrator()
        arb.register_source("drl", 0.2)
        arb.apply_deltas([WeightDelta(source="drl", priority_adjustment=-0.5,
                                       reason="drift")])
        assert arb.effective_weight("drl") == 0.0

    def test_resolve_uses_effective_priority(self):
        arb = StabilityWeightedArbitrator()
        arb.register_source("drl", 0.3)
        arb.register_source("sbs", 0.8)
        arb.apply_deltas([WeightDelta(source="drl", priority_adjustment=0.2,
                                       reason="stable")])
        arb.submit(ControlSignal(source="drl", priority=0.3, payload={}))
        arb.submit(ControlSignal(source="sbs", priority=0.8, payload={}))
        winner = arb.resolve()
        assert winner.source == "sbs"

    def test_audit_trail(self):
        arb = StabilityWeightedArbitrator()
        arb.register_source("drl", 0.5)
        arb.apply_deltas([WeightDelta(source="drl", priority_adjustment=0.1,
                                       reason="stable")])
        audit = arb.audit_trail()
        assert "drl" in audit
        assert audit["drl"]["effective"] == pytest.approx(0.6)
        assert audit["drl"]["base"] == 0.5


# ─── DriftPolicyAdaptor ───────────────────────────────────────────────────────


class TestDriftPolicyAdaptor:
    def test_register_policy(self):
        adaptor = DriftPolicyAdaptor()
        adaptor.register_policy("arbitration", {"switch_threshold": 0.5,
                                                 "coherence_weight": 0.7})
        p = adaptor.get_policy("arbitration")
        assert p["switch_threshold"] == 0.5
        assert p["coherence_weight"] == 0.7

    def test_source_switch_adjusts_switch_threshold(self):
        adaptor = DriftPolicyAdaptor()
        adaptor.register_policy("arbitration", {"switch_threshold": 0.5,
                                                 "coherence_weight": 0.7})
        chain = make_chain_with_sources("drl")
        report = TemporalVerificationReport(
            chain_length=chain.length,
            window=(0, 5),
            stability=make_stability_metrics(is_stable=False, overall=0.5),
            drift_report=DriftReport(
                tick_range=(0, 5),
                events=[
                    DriftEvent(
                        from_tick=2, to_tick=3,
                        drift_type=DriftType.SOURCE_SWITCH,
                        severity=0.3, description="",
                        from_source="sbs", to_source="drl",
                    )
                ],
                drift_score=0.3,
                is_drifted=False,
            ),
            causal_graph_stats={},
            overall_passed=False,
            recommendations=[],
            proof_chain=chain,
            verified_sources=["drl"],
        )
        changes = adaptor.compute_policy_changes(report)
        assert len(changes) >= 1
        assert changes[0].policy_name == "arbitration"
        assert changes[0].parameter == "switch_threshold"

    def test_policy_change_clamped_to_one(self):
        adaptor = DriftPolicyAdaptor()
        adaptor.register_policy("proof", {"validity_threshold": 0.95})
        chain = make_chain_with_sources("drl")
        report = TemporalVerificationReport(
            chain_length=chain.length,
            window=(0, 5),
            stability=make_stability_metrics(is_stable=False, overall=0.3),
            drift_report=DriftReport(
                tick_range=(0, 5),
                events=[
                    DriftEvent(
                        from_tick=3, to_tick=4,
                        drift_type=DriftType.PROOF_REGRESSION,
                        severity=1.0, description="",
                    )
                ],
                drift_score=0.9,
                is_drifted=True,
            ),
            causal_graph_stats={},
            overall_passed=False,
            recommendations=[],
            proof_chain=chain,
            verified_sources=["drl"],
        )
        changes = adaptor.compute_policy_changes(report)
        assert all(0.0 <= c.new_value <= 1.0 for c in changes)

    def test_drift_frequency(self):
        adaptor = DriftPolicyAdaptor()
        adaptor._drift_history = [
            DriftType.SOURCE_SWITCH, DriftType.REASONING_COLLAPSE,
            DriftType.SOURCE_SWITCH, DriftType.CAUSAL_BREAK,
        ]
        freq = adaptor.drift_frequency(DriftType.SOURCE_SWITCH, window=4)
        assert freq == 0.5


# ─── TemporalGainScheduler ─────────────────────────────────────────────────────


class TestTemporalGainScheduler:
    def test_stable_window_increases_global_multiplier(self):
        sched = TemporalGainScheduler()
        report = make_report(
            is_stable=True,
            stability=make_stability_metrics(is_stable=True, overall=0.85),
        )
        adj = sched.compute_adjustments(report, base_gains={"drl": 0.5})
        global_adj = next(a for a in adj if a.source == "__global__")
        assert global_adj.multiplier > 1.0

    def test_unstable_window_decreases_global_multiplier(self):
        sched = TemporalGainScheduler()
        report = make_report(
            is_stable=False,
            stability=make_stability_metrics(is_stable=False, overall=0.4),
            drift_events=[
                DriftEvent(
                    from_tick=3, to_tick=4,
                    drift_type=DriftType.REASONING_COLLAPSE,
                    severity=0.5, description="",
                )
            ],
        )
        adj = sched.compute_adjustments(report, base_gains={"drl": 0.5})
        global_adj = next(a for a in adj if a.source == "__global__")
        assert global_adj.multiplier < 1.0

    def test_drift_source_gets_reduction(self):
        sched = TemporalGainScheduler(drift_gain_reduction=0.2)
        report = make_report(
            is_stable=False,
            drift_events=[
                DriftEvent(
                    from_tick=1, to_tick=2,
                    drift_type=DriftType.REASONING_COLLAPSE,
                    severity=0.4, description="",
                )
            ],
            sources=["drl", "sbs"],
        )
        adj = sched.compute_adjustments(report, base_gains={"drl": 0.5, "sbs": 0.5})
        # REASONING_COLLAPSE has source="system" (not a specific agent source),
        # so the global multiplier drops to 0.8
        global_adj = next((a for a in adj if a.source == "__global__"), None)
        assert global_adj is not None
        assert global_adj.multiplier == pytest.approx(0.8)

    def test_apply_adjustments_combines_all_multipliers(self):
        sched = TemporalGainScheduler()
        report = make_report(
            is_stable=True,
            stability=make_stability_metrics(is_stable=True, overall=0.85),
        )
        base_gains = {"drl": 0.5}
        adj = sched.compute_adjustments(report, base_gains)
        final = sched.apply_adjustments(base_gains, adj)
        assert "drl" in final
        assert final["drl"] > 0

    def test_stability_trend_improving(self):
        sched = TemporalGainScheduler()
        sched._window_history = [0.5, 0.55, 0.6, 0.7, 0.85]
        trend = sched.stability_trend()
        assert trend > 0

    def test_stability_trend_degrading(self):
        sched = TemporalGainScheduler()
        sched._window_history = [0.85, 0.7, 0.6, 0.55, 0.5]
        trend = sched.stability_trend()
        assert trend < 0
