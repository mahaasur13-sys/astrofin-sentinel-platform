"""
Tests for v7.7 — Temporal Proof Continuity Layer.
"""
import pytest

from proof import (
    CausalLinkType,
    CausalProofGraph,
    ProofChain,
    ProofDriftDetector,
    StabilityMetrics,
    StabilityProver,
    TemporalVerifier,
)
from proof.proof_trace import (
    DecisionRecord,
    NodeType,
    ProofTrace,
)

# ─── ProofChain ────────────────────────────────────────────────────────────────

class TestProofChain:
    def test_append_single_link(self):
        chain = ProofChain()
        record = DecisionRecord(
            decision_id="d0", timestamp=0.0, input_state={}
        )
        link = chain.append(record)
        assert link.tick == 0
        assert link.parent_tick is None
        assert link.causal_depth == 0
        assert chain.length == 1
        assert chain.latest_tick == 0

    def test_append_links_are_sequential(self):
        chain = ProofChain()
        for i in range(3):
            record = DecisionRecord(
                decision_id=f"d{i}", timestamp=float(i), input_state={}
            )
            link = chain.append(record)
            assert link.tick == i
            assert link.parent_tick == (None if i == 0 else i - 1)
            assert link.causal_depth == i

    def test_append_continuity_same_source(self):
        chain = ProofChain()
        pt = ProofTrace()
        for i in range(2):
            record = DecisionRecord(
                decision_id=f"d{i}", timestamp=float(i), input_state={},
                selected_action=pt._make_node(NodeType.ACTION, "action:drl", {"priority": 0.9})
            )
            chain.append(record)
        # Same source → high continuity
        assert chain.links[1].continuity_score >= 0.9

    def test_append_continuity_switch_source(self):
        chain = ProofChain()
        pt = ProofTrace()
        record0 = DecisionRecord(
            decision_id="d0", timestamp=0.0, input_state={},
            selected_action=pt._make_node(NodeType.ACTION, "action:drl", {"priority": 0.9})
        )
        record1 = DecisionRecord(
            decision_id="d1", timestamp=1.0, input_state={},
            selected_action=pt._make_node(NodeType.ACTION, "action:sbs", {"priority": 0.5})
        )
        chain.append(record0)
        chain.append(record1)
        # Switch → lower continuity
        assert chain.links[1].continuity_score < 0.9

    def test_get_link(self):
        chain = ProofChain()
        record = DecisionRecord(decision_id="d0", timestamp=0.0, input_state={})
        chain.append(record)
        assert chain.get_link(0) is chain.links[0]
        assert chain.get_link(999) is None

    def test_window(self):
        chain = ProofChain()
        for i in range(5):
            chain.append(DecisionRecord(decision_id=f"d{i}", timestamp=float(i), input_state={}))
        assert len(chain.window(1, 3)) == 3
        assert chain.window(10, 20) == []

    def test_causal_path(self):
        chain = ProofChain()
        for i in range(3):
            chain.append(DecisionRecord(decision_id=f"d{i}", timestamp=float(i), input_state={}))
        assert chain.causal_path(2) == [0, 1, 2]
        assert chain.causal_path(0) == [0]

    def test_chain_validity(self):
        chain = ProofChain()
        assert chain.chain_validity() == 0.0
        pt = ProofTrace()
        for i in range(3):
            record = DecisionRecord(
                decision_id=f"d{i}", timestamp=float(i), input_state={},
                selected_action=pt._make_node(NodeType.ACTION, "action:drl", {"priority": 0.9})
            )
            chain.append(record)
        assert 0.0 <= chain.chain_validity() <= 1.0


# ─── CausalProofGraph ───────────────────────────────────────────────────────────

class TestCausalProofGraph:
    def test_add_vertex(self):
        g = CausalProofGraph()
        g.add_vertex(5)
        assert 5 in g.vertices
        g.add_vertex(5)  # no-op
        assert len(g.vertices) == 1

    def test_add_edge(self):
        g = CausalProofGraph()
        g.add_edge(0, 1, CausalLinkType.PRIORITY_PROPAGATION, weight=0.8)
        assert g.vertex_count == 2
        assert g.edge_count == 1
        assert 1 in g.successors(0)
        assert 0 in g.predecessors(1)

    def test_out_in_edges(self):
        g = CausalProofGraph()
        g.add_edge(0, 1, CausalLinkType.PRIORITY_PROPAGATION)
        g.add_edge(0, 2, CausalLinkType.GAIN_CARRY)
        out = g.out_edges(0)
        assert len(out) == 2
        assert g.in_edges(2)[0].from_tick == 0

    def test_causal_path_direct(self):
        g = CausalProofGraph()
        g.add_edge(0, 1, CausalLinkType.PRIORITY_PROPAGATION)
        g.add_edge(1, 2, CausalLinkType.GAIN_CARRY)
        assert g.causal_path(0, 2) == [0, 1, 2]

    def test_causal_path_no_path(self):
        g = CausalProofGraph()
        g.add_vertex(0)
        g.add_vertex(5)
        assert g.causal_path(0, 5) == []

    def test_propagation_strength(self):
        g = CausalProofGraph()
        g.add_edge(0, 1, CausalLinkType.PRIORITY_PROPAGATION, weight=0.9)
        g.add_edge(1, 2, CausalLinkType.PRIORITY_PROPAGATION, weight=0.9)
        # 0.9 * 0.9 = 0.81
        assert g.propagation_strength(0, 2) == pytest.approx(0.81)

    def test_build_from_chain(self):
        chain = ProofChain()
        pt = ProofTrace()
        for i in range(3):
            record = DecisionRecord(
                decision_id=f"d{i}", timestamp=float(i), input_state={},
                selected_action=pt._make_node(NodeType.ACTION, "action:drl", {"priority": 0.9})
            )
            chain.append(record)

        g = CausalProofGraph()
        g.build_from_chain(chain)
        # 2 ticks pairs × 2 link types each (PRIORITY_PROPAGATION + INVARIANT_STABILITY)
        assert g.edge_count == 4
        # PRIORITY_PROPAGATION edges only
        edges = [e for e in g.edges if e.link_type == CausalLinkType.PRIORITY_PROPAGATION]
        assert len(edges) == 2


# ─── StabilityProver ───────────────────────────────────────────────────────────

class TestStabilityProver:
    def test_stability_single_tick(self):
        chain = ProofChain()
        pt = ProofTrace()
        record = DecisionRecord(
            decision_id="d0", timestamp=0.0, input_state={},
            selected_action=pt._make_node(NodeType.ACTION, "action:drl", {"priority": 0.9})
        )
        chain.append(record)

        prover = StabilityProver(stability_threshold=0.75)
        m = prover.compute(chain)
        assert m.action_stability == 1.0
        assert m.is_stable is True

    def test_stability_all_same_source(self):
        chain = ProofChain()
        pt = ProofTrace()
        for i in range(5):
            record = DecisionRecord(
                decision_id=f"d{i}", timestamp=float(i), input_state={},
                selected_action=pt._make_node(NodeType.ACTION, "action:drl", {"priority": 0.9})
            )
            chain.append(record)

        prover = StabilityProver(stability_threshold=0.75)
        m = prover.compute(chain)
        assert m.action_stability == 1.0  # no transitions
        assert m.is_stable is True

    def test_stability_source_switching(self):
        chain = ProofChain()
        pt = ProofTrace()
        sources = ["drl", "sbs", "drl", "sbs", "drl"]
        for i, src in enumerate(sources):
            record = DecisionRecord(
                decision_id=f"d{i}", timestamp=float(i), input_state={},
                selected_action=pt._make_node(NodeType.ACTION, f"action:{src}", {"priority": 0.9})
            )
            chain.append(record)

        prover = StabilityProver(stability_threshold=0.75)
        m = prover.compute(chain)
        # 4 transitions out of 4 max → action_stability = 0.0
        assert m.action_stability == 0.0

    def test_stability_metrics_to_dict(self):
        m = StabilityMetrics(
            tick_range=(0, 5),
            action_stability=0.8,
            reasoning_stability=0.75,
            causal_coherence=0.9,
            proof_continuity=1.0,
            overall_stability=0.86,
            is_stable=True,
        )
        d = m.to_dict()
        assert d["action_stability"] == 0.8
        assert d["is_stable"] is True


# ─── ProofDriftDetector ────────────────────────────────────────────────────────

class TestProofDriftDetector:
    def test_no_drift_same_source(self):
        chain = ProofChain()
        pt = ProofTrace()
        for i in range(3):
            record = DecisionRecord(
                decision_id=f"d{i}", timestamp=float(i), input_state={},
                selected_action=pt._make_node(NodeType.ACTION, "action:drl", {"priority": 0.9})
            )
            chain.append(record)

        detector = ProofDriftDetector(severity_threshold=0.6)
        report = detector.detect(chain)
        assert report.is_drifted is False
        assert report.drift_score == 0.0

    def test_drift_source_switch(self):
        chain = ProofChain()
        pt = ProofTrace()
        sources = ["drl", "sbs"]
        for i, src in enumerate(sources):
            record = DecisionRecord(
                decision_id=f"d{i}", timestamp=float(i), input_state={},
                selected_action=pt._make_node(NodeType.ACTION, f"action:{src}", {"priority": 0.9})
            )
            chain.append(record)

        detector = ProofDriftDetector(severity_threshold=0.6)
        report = detector.detect(chain)
        assert len(report.events) >= 1
        assert any(e.drift_type == "source_switch" for e in report.events)

    def test_drift_continuity_drop(self):
        chain = ProofChain()
        pt = ProofTrace()
        record0 = DecisionRecord(
            decision_id="d0", timestamp=0.0, input_state={},
            selected_action=pt._make_node(NodeType.ACTION, "action:drl", {"priority": 0.9})
        )
        record1 = DecisionRecord(
            decision_id="d1", timestamp=1.0, input_state={},
            selected_action=pt._make_node(NodeType.ACTION, "action:sbs", {"priority": 0.5})
        )
        chain.append(record0)
        chain.append(record1)

        detector = ProofDriftDetector(
            severity_threshold=0.6,
            continuity_drop_threshold=0.3
        )
        report = detector.detect(chain)
        # continuity drops from ~0.95 to 0.6 → event detected
        assert any(e.drift_type == "reasoning_collapse" for e in report.events)

    def test_drift_proof_regression(self):
        chain = ProofChain()
        pt = ProofTrace()
        record0 = DecisionRecord(
            decision_id="d0", timestamp=0.0, input_state={},
            proof_status="PASS",
            selected_action=pt._make_node(NodeType.ACTION, "action:drl", {"priority": 0.9})
        )
        record1 = DecisionRecord(
            decision_id="d1", timestamp=1.0, input_state={},
            proof_status="FAIL",
            selected_action=pt._make_node(NodeType.ACTION, "action:drl", {"priority": 0.9})
        )
        chain.append(record0)
        chain.append(record1)

        detector = ProofDriftDetector(severity_threshold=0.5)
        report = detector.detect(chain)
        assert any(e.drift_type == "proof_regression" for e in report.events)
        assert report.is_drifted is True


# ─── TemporalVerifier ───────────────────────────────────────────────────────────

class TestTemporalVerifier:
    def test_verify_stable_chain(self):
        chain = ProofChain()
        pt = ProofTrace()
        for i in range(5):
            record = DecisionRecord(
                decision_id=f"d{i}", timestamp=float(i), input_state={},
                selected_action=pt._make_node(NodeType.ACTION, "action:drl", {"priority": 0.9})
            )
            chain.append(record)

        verifier = TemporalVerifier(stability_threshold=0.75, drift_threshold=0.6)
        report = verifier.verify(chain)
        assert report.overall_passed is True
        assert report.stability.is_stable is True
        assert report.drift_report.is_drifted is False
        assert len(report.recommendations) == 0

    def test_verify_unstable_chain(self):
        chain = ProofChain()
        pt = ProofTrace()
        sources = ["drl", "sbs", "drl", "sbs", "drl"]
        for i, src in enumerate(sources):
            record = DecisionRecord(
                decision_id=f"d{i}", timestamp=float(i), input_state={},
                selected_action=pt._make_node(NodeType.ACTION, f"action:{src}", {"priority": 0.9})
            )
            chain.append(record)

        verifier = TemporalVerifier(stability_threshold=0.75, drift_threshold=0.6)
        report = verifier.verify(chain)
        assert report.stability.action_stability == 0.0
        # recommendations include both reasoning stability + action stability warnings
        assert any("frequently" in r for r in report.recommendations)

    def test_verify_empty_chain(self):
        chain = ProofChain()
        verifier = TemporalVerifier()
        report = verifier.verify(chain)
        assert report.overall_passed is False
        assert "empty" in report.recommendations[0]

    def test_verify_window(self):
        chain = ProofChain()
        pt = ProofTrace()
        for i in range(5):
            record = DecisionRecord(
                decision_id=f"d{i}", timestamp=float(i), input_state={},
                selected_action=pt._make_node(NodeType.ACTION, "action:drl", {"priority": 0.9})
            )
            chain.append(record)

        verifier = TemporalVerifier()
        report = verifier.verify(chain, window=(1, 3))
        assert report.window == (1, 3)

    def test_verify_batch(self):
        chain1 = ProofChain()
        chain2 = ProofChain()
        pt = ProofTrace()
        for chain, src in [(chain1, "drl"), (chain2, "sbs")]:
            for i in range(3):
                record = DecisionRecord(
                    decision_id=f"d{i}", timestamp=float(i), input_state={},
                    selected_action=pt._make_node(NodeType.ACTION, f"action:{src}", {"priority": 0.9})
                )
                chain.append(record)

        verifier = TemporalVerifier()
        reports = verifier.verify_batch([chain1, chain2])
        assert len(reports) == 2

    def test_temporal_report_to_dict(self):
        chain = ProofChain()
        pt = ProofTrace()
        record = DecisionRecord(
            decision_id="d0", timestamp=0.0, input_state={},
            selected_action=pt._make_node(NodeType.ACTION, "action:drl", {"priority": 0.9})
        )
        chain.append(record)

        verifier = TemporalVerifier()
        report = verifier.verify(chain)
        d = report.to_dict()
        assert "stability" in d
        assert "drift" in d
        assert "overall_passed" in d

    def test_build_graph(self):
        chain = ProofChain()
        pt = ProofTrace()
        for i in range(3):
            record = DecisionRecord(
                decision_id=f"d{i}", timestamp=float(i), input_state={},
                selected_action=pt._make_node(NodeType.ACTION, "action:drl", {"priority": 0.9})
            )
            chain.append(record)

        verifier = TemporalVerifier()
        graph = verifier.build_graph(chain)
        assert graph.vertex_count >= 2
        assert graph.edge_count >= 1
