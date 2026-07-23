"""
Tests for cross_layer_invariant_engine.py — I1–I4 invariant verification.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from consistency.cross_layer_invariant_engine import (
    CausalDAG,
    CrossLayerInvariantEngine,
    CrossLayerReport,
    InvariantResult,
)

# ── Fixtures ────────────────────────────────────────────────────────────────

@dataclass
class MockEvent:
    ts: int
    event_id: str
    node_id: str = "node-0"
    event_type: str = "test.event"
    payload: dict = field(default_factory=dict)


@pytest.fixture
def sample_exec_events() -> list[MockEvent]:
    """Two-node cluster with SBS violations and drift."""
    return [
        MockEvent(ts=1_000_000_000, event_id="e1", node_id="n0",
                  event_type="node.start", payload={"term": 1}),
        MockEvent(ts=1_100_000_000, event_id="e2", node_id="n1",
                  event_type="node.start", payload={"term": 1}),
        MockEvent(ts=1_200_000_000, event_id="e3", node_id="n0",
                  event_type="sbs.violation", payload={"violation_type": "quorum"}),
        MockEvent(ts=1_300_000_000, event_id="e4", node_id="n0",
                  event_type="coherence.drift.detected",
                  payload={"causal_parents": ["e3"], "drift_score": 0.42}),
    ]


@pytest.fixture
def sample_replay_events() -> list[MockEvent]:
    """Identical event sequence from replay."""
    return [
        MockEvent(ts=1_000_000_000, event_id="e1", node_id="n0",
                  event_type="node.start", payload={"term": 1}),
        MockEvent(ts=1_100_000_000, event_id="e2", node_id="n1",
                  event_type="node.start", payload={"term": 1}),
        MockEvent(ts=1_200_000_000, event_id="e3", node_id="n0",
                  event_type="sbs.violation", payload={"violation_type": "quorum"}),
        MockEvent(ts=1_300_000_000, event_id="e4", node_id="n0",
                  event_type="coherence.drift.detected",
                  payload={"causal_parents": ["e3"], "drift_score": 0.42}),
    ]


@pytest.fixture
def mismatched_replay_events() -> list[MockEvent]:
    """Same sequence but SBS count and drift_score differ."""
    return [
        MockEvent(ts=1_000_000_000, event_id="e1", node_id="n0",
                  event_type="node.start", payload={"term": 1}),
        MockEvent(ts=1_100_000_000, event_id="e2", node_id="n1",
                  event_type="node.start", payload={"term": 1}),
        # no sbs.violation here — drift in replay
        MockEvent(ts=1_300_000_000, event_id="e4", node_id="n0",
                  event_type="coherence.drift.detected",
                  payload={"causal_parents": ["e3"], "drift_score": 0.99}),
    ]


def make_cluster_state(
    sbs_violations: int = 1,
    drift_score: float = 0.42,
    violation_type: str = "quorum",
) -> dict:
    return {
        "nodes": {
            "n0": {
                "status": "active",
                "sbs_violations": sbs_violations,
                "coherence_drift_score": drift_score,
                "last_violation_type": violation_type,
            },
            "n1": {"status": "active"},
        },
        "lattice": {},
        "quorum": {},
    }


def make_replay_state(
    sbs_violations: int = 1,
    drift_score: float = 0.42,
    violation_type: str = "quorum",
) -> dict:
    return {
        "nodes": {
            "n0": {
                "status": "active",
                "sbs_violations": sbs_violations,
                "coherence_drift_score": drift_score,
                "last_violation_type": violation_type,
            },
            "n1": {"status": "active"},
        },
        "lattice": {},
        "quorum": {},
    }


# ── CausalDAG tests ─────────────────────────────────────────────────────────

class TestCausalDAG:
    def test_add_and_retrieve_parents(self):
        dag = CausalDAG()
        dag.add_event("e1", causal_parents=[], payload={"x": 1})
        dag.add_event("e2", causal_parents=["e1"], payload={"y": 2})

        assert "e1" in dag.nodes
        assert "e2" in dag.nodes
        assert dag.nodes["e2"]["parents"] == {"e1"}

    def test_ancestors_transitive(self):
        dag = CausalDAG()
        dag.add_event("e1")
        dag.add_event("e2", causal_parents=["e1"])
        dag.add_event("e3", causal_parents=["e2"])
        dag.add_event("e4", causal_parents=["e3"])

        ancestors_e4 = dag.ancestors("e4")
        assert ancestors_e4 == {"e1", "e2", "e3"}

    def test_is_identical_true(self):
        a = CausalDAG()
        a.add_event("e1", causal_parents=[])
        a.add_event("e2", causal_parents=["e1"])

        b = CausalDAG()
        b.add_event("e1", causal_parents=[])
        b.add_event("e2", causal_parents=["e1"])

        identical, reason = a.is_identical(b)
        assert identical
        assert reason == "identical"

    def test_is_identical_false_different_parents(self):
        a = CausalDAG()
        a.add_event("e1", causal_parents=[])
        a.add_event("e2", causal_parents=["e1"])

        b = CausalDAG()
        b.add_event("e1", causal_parents=[])
        b.add_event("e2", causal_parents=[])  # missing parent

        identical, reason = b.is_identical(a)
        assert not identical
        assert "causal_parents differ" in reason

    def test_is_identical_false_different_nodes(self):
        a = CausalDAG()
        a.add_event("e1")

        b = CausalDAG()
        b.add_event("e1")
        b.add_event("e2")

        identical, reason = a.is_identical(b)
        assert not identical
        assert "node_ids differ" in reason


# ── CrossLayerInvariantEngine tests ────────────────────────────────────────

class TestCrossLayerInvariantEngine:
    def test_i1_passes_when_states_identical(self):
        """I1: identical cluster and replay state → PASS."""
        engine = CrossLayerInvariantEngine(
            cluster_state_fn=lambda: make_cluster_state(),
            replay_state_fn=lambda: make_replay_state(),
        )
        report = engine.verify([], [])
        assert report.i1_cluster_vs_replay.passed

    def test_i1_fails_on_node_drift(self):
        """I1: different node keys → FAIL with node_drift report."""
        def cluster_missing_n1():
            state = make_cluster_state()
            del state["nodes"]["n1"]
            return state

        engine = CrossLayerInvariantEngine(
            cluster_state_fn=cluster_missing_n1,
            replay_state_fn=lambda: make_replay_state(),
        )
        report = engine.verify([], [])
        assert not report.i1_cluster_vs_replay.passed
        assert "node_drift" in report.i1_cluster_vs_replay.details

    def test_i2_passes_identical_causal_dags(
        self, sample_exec_events, sample_replay_events
    ):
        """I2: identical event sequences → identical DAGs → PASS."""
        engine = CrossLayerInvariantEngine(
            cluster_state_fn=make_cluster_state,
            replay_state_fn=make_replay_state,
        )
        report = engine.verify(sample_exec_events, sample_replay_events)
        assert report.i2_causal_dag_equivalence.passed

    def test_i2_fails_on_different_causal_structure(
        self, sample_exec_events, mismatched_replay_events
    ):
        """I2: missing events → different DAG → FAIL."""
        engine = CrossLayerInvariantEngine(
            cluster_state_fn=make_cluster_state,
            replay_state_fn=make_replay_state,
        )
        report = engine.verify(sample_exec_events, mismatched_replay_events)
        assert not report.i2_causal_dag_equivalence.passed

    def test_i3_passes_identical_sbs_count(
        self, sample_exec_events, sample_replay_events
    ):
        """I3: same SBS violation count → PASS."""
        engine = CrossLayerInvariantEngine(
            cluster_state_fn=lambda: make_cluster_state(sbs_violations=1),
            replay_state_fn=lambda: make_replay_state(sbs_violations=1),
        )
        report = engine.verify(sample_exec_events, sample_replay_events)
        assert report.i3_sbs_violation_equivalence.passed

    def test_i3_fails_mismatched_sbs_count(
        self, sample_exec_events, sample_replay_events
    ):
        """I3: different SBS count → FAIL."""
        engine = CrossLayerInvariantEngine(
            cluster_state_fn=lambda: make_cluster_state(sbs_violations=2),
            replay_state_fn=lambda: make_replay_state(sbs_violations=0),
        )
        report = engine.verify(sample_exec_events, sample_replay_events)
        assert not report.i3_sbs_violation_equivalence.passed
        assert report.i3_sbs_violation_equivalence.drift > 0

    def test_i4_passes_identical_drift_score(
        self, sample_exec_events, sample_replay_events
    ):
        """I4: identical drift scores → PASS."""
        engine = CrossLayerInvariantEngine(
            cluster_state_fn=lambda: make_cluster_state(drift_score=0.42),
            replay_state_fn=lambda: make_replay_state(drift_score=0.42),
        )
        report = engine.verify(sample_exec_events, sample_replay_events)
        assert report.i4_drift_score_equivalence.passed

    def test_i4_fails_mismatched_drift_score(
        self, sample_exec_events, sample_replay_events
    ):
        """I4: different drift scores → FAIL with max_drift_score reported."""
        engine = CrossLayerInvariantEngine(
            cluster_state_fn=lambda: make_cluster_state(drift_score=0.99),
            replay_state_fn=lambda: make_replay_state(drift_score=0.01),
        )
        report = engine.verify(sample_exec_events, sample_replay_events)
        assert not report.i4_drift_score_equivalence.passed
        assert "max_drift_score" in report.i4_drift_score_equivalence.details

    def test_all_passed_true_when_everything_ok(
        self, sample_exec_events, sample_replay_events
    ):
        """all_passed = True only when all 4 invariants pass."""
        engine = CrossLayerInvariantEngine(
            cluster_state_fn=lambda: make_cluster_state(
                sbs_violations=1, drift_score=0.42
            ),
            replay_state_fn=lambda: make_replay_state(
                sbs_violations=1, drift_score=0.42
            ),
        )
        report = engine.verify(sample_exec_events, sample_replay_events)
        assert report.all_passed
        assert report.passed_checks == 4

    def test_all_passed_false_when_any_fails(
        self, sample_exec_events, mismatched_replay_events
    ):
        """all_passed = False as soon as any invariant fails."""
        engine = CrossLayerInvariantEngine(
            cluster_state_fn=lambda: make_cluster_state(
                sbs_violations=1, drift_score=0.42
            ),
            replay_state_fn=lambda: make_replay_state(
                sbs_violations=0, drift_score=0.99
            ),
        )
        report = engine.verify(sample_exec_events, mismatched_replay_events)
        assert not report.all_passed
        assert report.passed_checks < 4

    def test_report_to_dict(self):
        """CrossLayerReport.to_dict() returns serializable dict."""
        engine = CrossLayerInvariantEngine(
            cluster_state_fn=lambda: make_cluster_state(),
            replay_state_fn=lambda: make_replay_state(),
        )
        report = engine.verify([], [])
        d = report.to_dict()
        assert all(k in d for k in ("i1", "i2", "i3", "i4", "all_passed"))
        assert d["total"] == 4

    def test_verify_returns_cross_layer_report(self):
        """verify() returns CrossLayerReport, not dict."""
        engine = CrossLayerInvariantEngine(
            cluster_state_fn=make_cluster_state,
            replay_state_fn=make_replay_state,
        )
        result = engine.verify([], [])
        assert isinstance(result, CrossLayerReport)
        assert isinstance(result.i1_cluster_vs_replay, InvariantResult)

    def test_dict_drift_normalizes(self):
        """_dict_drift returns 0 for identical dicts, <1 for partial drift."""
        engine = CrossLayerInvariantEngine(
            cluster_state_fn=make_cluster_state,
            replay_state_fn=make_replay_state,
        )
        a = {"x": 1, "y": 2}
        b = {"x": 1, "y": 2}
        assert engine._dict_drift(a, b) == 0.0

        c = {"x": 1, "y": 999}
        drift = engine._dict_drift(a, c)
        assert 0.0 < drift <= 1.0

    def test_get_last_report(self):
        """get_last_report() returns last verification report."""
        engine = CrossLayerInvariantEngine(
            cluster_state_fn=make_cluster_state,
            replay_state_fn=make_replay_state,
        )
        assert engine.get_last_report() is None

        report1 = engine.verify([], [])
        last = engine.get_last_report()
        assert isinstance(last, CrossLayerReport)
        assert last is report1  # same object, not a new one

        report2 = engine.verify([], [])
        assert engine.get_last_report() is report2  # updated after second call

    def test_empty_event_lists_handled(self):
        """Empty event lists don't crash I2 check."""
        engine = CrossLayerInvariantEngine(
            cluster_state_fn=make_cluster_state,
            replay_state_fn=make_replay_state,
        )
        report = engine.verify([], [])
        # I1 may pass/fail depending on state fns
        # I2 should pass (empty DAGs are identical)
        assert report.i2_causal_dag_equivalence.passed

    def test_partial_causal_parents_listed(self):
        """Causal parents as list (not set) are handled correctly."""
        engine = CrossLayerInvariantEngine(
            cluster_state_fn=make_cluster_state,
            replay_state_fn=make_replay_state,
        )
        events = [
            MockEvent(
                ts=100, event_id="a", event_type="test",
                payload={"causal_parents": ["p1", "p2"]},
            )
        ]
        report = engine.verify(events, events)
        assert report.i2_causal_dag_equivalence.passed
