"""
Tests for explainable_divergence_engine.py
"""

from consistency_v3.explainable_divergence_engine import (
    DivergenceRootCause,
    DivergenceRootCauseGraph,
    ExplainableDivergenceEngine,
)


class TestDivergenceRootCause:
    def test_to_dict(self):
        cause = DivergenceRootCause(
            domain="mem",
            field="used_bytes",
            exec_value=100,
            replay_value=50,
            diff_magnitude=50.0,
            propagation_depth=2,
            severity_score=5.0,
            mitigation_hint="Reduce allocations.",
            is_root=True,
        )
        d = cause.to_dict()
        assert d["domain"] == "mem"
        assert d["field"] == "used_bytes"
        assert d["severity_score"] == 5.0
        assert d["is_root"] is True


class TestDivergenceRootCauseGraph:
    def test_add_node(self):
        graph = DivergenceRootCauseGraph()
        cause = DivergenceRootCause(domain="net", field="latency_ms", diff_magnitude=10.0)
        graph.add_node(cause)
        assert "net::latency_ms" in graph.nodes

    def test_root_causes_no_edges(self):
        graph = DivergenceRootCauseGraph()
        graph.add_node(DivergenceRootCause(domain="a", field="x", diff_magnitude=1.0))
        graph.add_node(DivergenceRootCause(domain="b", field="y", diff_magnitude=2.0))
        roots = graph.root_causes()
        assert len(roots) == 2

    def test_root_causes_with_edge(self):
        graph = DivergenceRootCauseGraph()
        cause_a = DivergenceRootCause(domain="a", field="x", diff_magnitude=1.0)
        cause_b = DivergenceRootCause(domain="b", field="y", diff_magnitude=2.0)
        graph.add_node(cause_a)
        graph.add_node(cause_b)
        graph.add_edge("a::x", "b::y")
        roots = graph.root_causes()
        assert len(roots) == 1
        assert roots[0].domain == "a"

    def test_topological_sort(self):
        graph = DivergenceRootCauseGraph()
        for i in range(3):
            graph.add_node(DivergenceRootCause(domain=f"d{i}", field="f", diff_magnitude=1.0))
        graph.add_edge("d0::f", "d1::f")
        graph.add_edge("d1::f", "d2::f")
        sorted_keys = graph.topological_sort()
        assert sorted_keys.index("d0::f") < sorted_keys.index("d1::f")
        assert sorted_keys.index("d1::f") < sorted_keys.index("d2::f")

    def test_to_dict(self):
        graph = DivergenceRootCauseGraph()
        graph.add_node(DivergenceRootCause(domain="x", field="y", diff_magnitude=3.0))
        d = graph.to_dict()
        assert "nodes" in d
        assert "edges" in d
        assert "root_causes" in d


class TestExplainableDivergenceEngine:
    def test_explain_basic(self):
        engine = ExplainableDivergenceEngine()
        exec_state = {"mem": {"used_bytes": 100}, "cpu": {"util": 0.8}}
        replay_state = {"mem": {"used_bytes": 50}, "cpu": {"util": 0.8}}

        graph = engine.explain(
            exec_state=exec_state,
            replay_state=replay_state,
            fingerprint_exec="abc123",
            fingerprint_replay="def456",
            semantic_distance=50.0,
            dominant_axis=0,
        )
        assert isinstance(graph, DivergenceRootCauseGraph)
        assert len(graph.nodes) > 0

    def test_explain_identical_states(self):
        engine = ExplainableDivergenceEngine()
        state = {"x": {"val": 42}}
        graph = engine.explain(
            exec_state=state,
            replay_state=state,
            fingerprint_exec="same",
            fingerprint_replay="same",
            semantic_distance=0.0,
            dominant_axis=-1,
        )
        # Identical states may produce empty or minimal graph
        assert isinstance(graph, DivergenceRootCauseGraph)

    def test_explain_with_causal_deps(self):
        engine = ExplainableDivergenceEngine()
        engine.register_causal_dependency("b", "y", depends_on_domain="a", depends_on_field="x")
        graph = engine.explain(
            exec_state={"a": {"x": 10}, "b": {"y": 20}},
            replay_state={"a": {"x": 1}, "b": {"y": 2}},
            fingerprint_exec="abc",
            fingerprint_replay="xyz",
            semantic_distance=100.0,
            dominant_axis=0,
        )
        assert isinstance(graph, DivergenceRootCauseGraph)

    def test_mitigation_hint_resolved(self):
        engine = ExplainableDivergenceEngine()
        graph = engine.explain(
            exec_state={"foo": {"bar": 1}},
            replay_state={"foo": {"bar": 2}},
            fingerprint_exec="f1",
            fingerprint_replay="f2",
            semantic_distance=10.0,
            dominant_axis=4,  # temporal drift
        )
        for node in graph.nodes.values():
            assert node.mitigation_hint != ""

    def test_severity_propagation(self):
        engine = ExplainableDivergenceEngine()
        graph = engine.explain(
            exec_state={"a": {"x": 100}, "b": {"y": 200}},
            replay_state={"a": {"x": 1}, "b": {"y": 2}},
            fingerprint_exec="abc",
            fingerprint_replay="xyz",
            semantic_distance=50.0,
            dominant_axis=0,
        )
        for node in graph.nodes.values():
            assert node.severity_score >= 0.0
            assert node.severity_score <= 10.0

    def test_custom_mitigation_hints(self):
        engine = ExplainableDivergenceEngine()
        exec_state = {"dom": {"fld": 1}}
        graph = engine.explain(
            exec_state=exec_state,
            replay_state={"dom": {"fld": 2}},
            fingerprint_exec="a",
            fingerprint_replay="b",
            semantic_distance=5.0,
            dominant_axis=0,
        )
        # Should have a mitigation hint for each node
        for node in graph.nodes.values():
            assert isinstance(node.mitigation_hint, str)
