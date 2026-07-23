import pytest

from orchestration import (
    ConflictResolutionMatrix,
    ControlArbitrator,
    ControlSignal,
    FeedbackPrioritySolver,
    FeedbackSignal,
    SystemWideGainScheduler,
)

# ─── ControlArbitrator ────────────────────────────────────────────────────────

class TestControlArbitratorBasics:
    def test_submit_and_resolve_single(self):
        arb = ControlArbitrator()
        sig = ControlSignal(source="drl", priority=0.8, payload={"delta": 0.1})
        arb.submit(sig)
        winner = arb.resolve()
        assert winner.source == "drl"
        assert winner.priority == 0.8

    def test_resolve_empty_raises(self):
        arb = ControlArbitrator()
        with pytest.raises(RuntimeError, match="No control signals"):
            arb.resolve()

    def test_highest_priority_wins(self):
        arb = ControlArbitrator()
        arb.submit(ControlSignal(source="sbs", priority=0.5, payload={}))
        arb.submit(ControlSignal(source="drl", priority=0.9, payload={}))
        arb.submit(ControlSignal(source="coherence", priority=0.7, payload={}))
        winner = arb.resolve()
        assert winner.source == "drl"

    def test_tie_break_by_source_name(self):
        arb = ControlArbitrator()
        arb.submit(ControlSignal(source="aaa", priority=1.0, payload={}))
        arb.submit(ControlSignal(source="bbb", priority=1.0, payload={}))
        winner = arb.resolve()
        assert winner.source == "aaa"  # "aaa" < "bbb" alphabetically

    def test_resolve_many_returns_sorted(self):
        arb = ControlArbitrator()
        arb.submit(ControlSignal(source="sbs", priority=0.5, payload={}))
        arb.submit(ControlSignal(source="drl", priority=0.9, payload={}))
        arb.submit(ControlSignal(source="coherence", priority=0.7, payload={}))
        ordered = arb.resolve_many()
        assert [s.source for s in ordered] == ["drl", "coherence", "sbs"]
        assert arb.pending_count == 3  # resolve_many does NOT clear

    def test_pending_count(self):
        arb = ControlArbitrator()
        assert arb.pending_count == 0
        arb.submit(ControlSignal(source="drl", priority=0.5, payload={}))
        assert arb.pending_count == 1


# ─── FeedbackPrioritySolver ───────────────────────────────────────────────────

class TestFeedbackPrioritySolver:
    def test_compute_priority_formula(self):
        solver = FeedbackPrioritySolver()
        sig = FeedbackSignal(layer="drl", urgency=0.9, stability_impact=0.5)
        expected = 0.9 * 0.7 + 0.5 * 0.3
        assert solver.compute_priority(sig) == pytest.approx(expected)

    def test_rank_orders_correctly(self):
        solver = FeedbackPrioritySolver()
        signals = {
            "sbs": FeedbackSignal(layer="sbs", urgency=0.5, stability_impact=0.3),
            "drl": FeedbackSignal(layer="drl", urgency=0.9, stability_impact=0.5),
            "coherence": FeedbackSignal(layer="coherence", urgency=0.7, stability_impact=0.4),
        }
        priorities = solver.rank(signals)
        assert priorities["drl"] > priorities["coherence"]
        assert priorities["coherence"] > priorities["sbs"]

    def test_rank_sorted(self):
        solver = FeedbackPrioritySolver()
        signals = {
            "sbs": FeedbackSignal(layer="sbs", urgency=0.5, stability_impact=0.3),
            "drl": FeedbackSignal(layer="drl", urgency=0.9, stability_impact=0.5),
        }
        ranked = solver.rank_sorted(signals)
        assert ranked[0] == ("drl", pytest.approx(0.9 * 0.7 + 0.5 * 0.3))


# ─── SystemWideGainScheduler ─────────────────────────────────────────────────

class TestSystemWideGainScheduler:
    def test_normalize_under_limit(self):
        sched = SystemWideGainScheduler(max_global_gain=2.0)
        gains = {"drl": 0.5, "sbs": 0.5}
        result = sched.normalize(gains)
        total = sum(abs(v) for v in result.values())
        assert total <= 2.0

    def test_normalize_clamps_at_max(self):
        sched = SystemWideGainScheduler(max_global_gain=1.0)
        gains = {"drl": 1.0, "sbs": 1.0}
        result = sched.normalize(gains)
        total = sum(abs(v) for v in result.values())
        assert total <= 1.0

    def test_normalize_empty(self):
        sched = SystemWideGainScheduler(max_global_gain=2.0)
        result = sched.normalize({})
        assert result == {}

    def test_normalize_and_cap(self):
        sched = SystemWideGainScheduler(max_global_gain=10.0)
        gains = {"drl": 5.0, "sbs": 5.0}
        result = sched.normalize_and_cap(gains, per_layer_cap=1.5)
        for v in result.values():
            assert abs(v) <= 1.5


# ─── ConflictResolutionMatrix ─────────────────────────────────────────────────

class TestConflictResolutionMatrix:
    def test_single_candidate(self):
        m = ConflictResolutionMatrix()
        assert m.resolve(["drl"]) == "drl"

    def test_resolve_empty_raises(self):
        m = ConflictResolutionMatrix()
        with pytest.raises(ValueError, match="No candidates"):
            m.resolve([])

    def test_pairwise_winner(self):
        m = ConflictResolutionMatrix()
        m.set_priority("drl", "sbs", 1.0)
        assert m.pairwise_winner("drl", "sbs") == "drl"
        assert m.pairwise_winner("sbs", "drl") == "drl"

    def test_resolve_with_matrix(self):
        m = ConflictResolutionMatrix()
        # drl beats sbs and coherence
        m.set_priority("drl", "sbs", 1.0)
        m.set_priority("drl", "coherence", 1.0)
        # sbs beats coherence
        m.set_priority("sbs", "coherence", 1.0)
        winner = m.resolve(["sbs", "drl", "coherence"])
        assert winner == "drl"

    def test_pairwise_winner_default(self):
        m = ConflictResolutionMatrix()
        # No preference registered → stable sort order wins
        assert m.pairwise_winner("drl", "sbs") == "sbs"  # later alphabetically

    def test_matrix_clear(self):
        m = ConflictResolutionMatrix()
        m.set_priority("a", "b", 1.0)
        assert m._matrix[("a", "b")] == 1.0
        # re-init clears
        m.__init__()
        assert len(m._matrix) == 0
