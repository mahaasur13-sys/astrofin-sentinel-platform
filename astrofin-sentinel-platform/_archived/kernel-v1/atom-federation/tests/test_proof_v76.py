"""
Tests for v7.6 — Formal Proof Kernel.
"""
from orchestration import ControlSignal
from proof import (
    DecisionProver,
    DecisionRecord,
    InvariantRegistry,
    InvariantType,
    ProofKernel,
    VerificationEngine,
)
from proof.proof_trace import (
    DominanceResult,
    NodeType,
    ProofTrace,
    RejectedBranch,
)

# ─── ProofTrace ──────────────────────────────────────────────────────────────

class TestProofTraceBasics:
    def test_build_input_state(self):
        pt = ProofTrace()
        state = {"pending": 3, "gain": 1.5}
        node = pt.build_input_state(state)
        assert node.node_type == NodeType.INPUT_STATE
        assert node.metadata == state
        assert node.proof_id is not None

    def test_add_arbiter_stage(self):
        pt = ProofTrace()
        record = DecisionRecord(decision_id="d0", timestamp=0.0, input_state={})
        pt.add_arbiter_stage(
            record,
            winner_source="drl",
            winner_priority=0.9,
            all_submitted=[
                {"source": "drl", "priority": 0.9},
                {"source": "sbs", "priority": 0.5},
            ],
        )
        assert record.arbitration_node is not None
        assert record.arbitration_node.metadata["winner"] == "drl"
        # 2 children: winner (not REJECTED) + sbs (REJECTED)
        assert len(record.arbitration_node.children) == 2

    def test_add_gain_stage(self):
        pt = ProofTrace()
        record = DecisionRecord(decision_id="d0", timestamp=0.0, input_state={})
        pt.add_gain_stage(record, {"drl": 0.8, "sbs": 0.2})
        assert record.gain_node is not None
        assert record.gain_node.metadata["normalized"] == {"drl": 0.8, "sbs": 0.2}

    def test_add_conflict_stage(self):
        pt = ProofTrace()
        record = DecisionRecord(decision_id="d0", timestamp=0.0, input_state={})
        pt.add_conflict_stage(
            record,
            winner="drl",
            candidates=["drl", "sbs"],
            matrix_entries={("sbs", "drl"): 1.0},
        )
        assert record.conflict_node is not None
        assert record.conflict_node.metadata["winner"] == "drl"

    def test_finalize_links_nodes(self):
        pt = ProofTrace()
        record = DecisionRecord(decision_id="d0", timestamp=0.0, input_state={})
        pt.add_arbiter_stage(record, "drl", 0.9, [{"source": "drl", "priority": 0.9}])
        pt.add_gain_stage(record, {"drl": 1.0})
        pt.set_action(record, "drl", {"priority": 0.9})
        pt.finalize(record)
        # finalize() uses insert(0, …) so chain link lands at children[0]
        # (signal children end up at children[1:] after prepends)
        assert record.arbitration_node.children[0] is record.gain_node
        assert record.gain_node.children[0] is record.selected_action

    def test_export_dag(self):
        pt = ProofTrace()
        record = DecisionRecord(decision_id="d0", timestamp=1.0, input_state={"x": 1})
        pt.add_arbiter_stage(record, "drl", 0.9, [{"source": "drl", "priority": 0.9}])
        dag = pt.export_dag(record)
        assert dag["decision_id"] == "d0"
        assert dag["arbitration_node"]["label"] == "arbitration:winner=drl"

    def test_rejected_branch_record(self):
        pt = ProofTrace()
        record = DecisionRecord(decision_id="d0", timestamp=0.0, input_state={})
        pt.add_rejected(
            record,
            source="sbs",
            reason="priority lower",
            dominance=DominanceResult.STRICTLY_DOMINATES,
            priority=0.5,
            selected_priority=0.9,
        )
        assert len(record.rejected_branches) == 1
        assert record.rejected_branches[0].source == "sbs"
        assert record.rejected_branches[0].dominance == DominanceResult.STRICTLY_DOMINATES


# ─── DecisionRecord ────────────────────────────────────────────────────────────

class TestDecisionRecord:
    def test_to_dict_roundtrip(self):
        record = DecisionRecord(
            decision_id="d_test",
            timestamp=100.0,
            input_state={"pending": 2},
            proof_status="PASS",
            validity_score=0.95,
            invariants_checked=["I1", "I2"],
        )
        d = record.to_dict()
        assert d["decision_id"] == "d_test"
        assert d["proof_status"] == "PASS"
        assert d["validity_score"] == 0.95
        assert d["invariants_checked"] == ["I1", "I2"]


# ─── DecisionProver ─────────────────────────────────────────────────────────────

class TestDecisionProver:
    def test_prove_single_candidate_trivially_optimal(self):
        prover = DecisionProver()
        record = DecisionRecord(
            decision_id="d0",
            timestamp=0.0,
            input_state={},
            selected_action=ProofTrace()._make_node(
                NodeType.ACTION, "action:drl", {"priority": 0.9}
            ),
            rejected_branches=[],
        )
        result = prover.prove(record)
        assert result.optimal is True
        assert result.proof_status == "PASS"
        assert "Single candidate" in result.dominance_reasons[0]

    def test_prove_rejected_dominated(self):
        prover = DecisionProver()
        pt = ProofTrace()
        record = DecisionRecord(
            decision_id="d0",
            timestamp=0.0,
            input_state={},
            selected_action=pt._make_node(NodeType.ACTION, "action:drl", {"priority": 0.9}),
            rejected_branches=[
                RejectedBranch(
                    source="sbs",
                    reason="priority lower",
                    dominance=DominanceResult.STRICTLY_DOMINATES,
                    priority=0.5,
                    selected_priority=0.9,
                ),
            ],
        )
        result = prover.prove(record)
        assert result.optimal is True
        assert "I1" in result.dominance_reasons[0]

    def test_validity_score_bounded(self):
        prover = DecisionProver()
        record = DecisionRecord(
            decision_id="d0",
            timestamp=0.0,
            input_state={},
            selected_action=ProofTrace()._make_node(NodeType.ACTION, "action:drl", {"priority": 0.9}),
            rejected_branches=[],
        )
        result = prover.prove(record)
        assert 0.0 <= result.validity_score <= 1.0


# ─── InvariantRegistry ──────────────────────────────────────────────────────────

class TestInvariantRegistry:
    def test_builtin_invariants_registered(self):
        reg = InvariantRegistry()
        names = [s["name"] for s in reg.list_all()]
        assert "I1" in names
        assert "I2" in names
        assert "I3" in names
        assert "I4" in names
        assert "I5" in names

    def test_i1_gain_within_limit(self):
        reg = InvariantRegistry()
        pt = ProofTrace()
        record = DecisionRecord(
            decision_id="d0",
            timestamp=0.0,
            input_state={"_meta_max_global_gain": 2.0},
            gain_node=pt._make_node(
                NodeType.GAIN_NORMALIZATION,
                "gain_normalization",
                {"normalized": {"drl": 1.0, "sbs": 0.5}},
            ),
        )
        assert reg.check(record)["I1"] is True

    def test_i1_gain_exceeds_limit(self):
        reg = InvariantRegistry()
        pt = ProofTrace()
        record = DecisionRecord(
            decision_id="d0",
            timestamp=0.0,
            input_state={"_meta_max_global_gain": 1.0},
            gain_node=pt._make_node(
                NodeType.GAIN_NORMALIZATION,
                "gain_normalization",
                {"normalized": {"drl": 1.0, "sbs": 0.5}},
            ),
        )
        assert reg.check(record)["I1"] is False

    def test_i2_winner_priority_above_rejected(self):
        reg = InvariantRegistry()
        pt = ProofTrace()
        record = DecisionRecord(
            decision_id="d0",
            timestamp=0.0,
            input_state={},
            selected_action=pt._make_node(NodeType.ACTION, "action:drl", {"priority": 0.9}),
            rejected_branches=[
                RejectedBranch(
                    source="sbs", reason="", dominance=DominanceResult.STRICTLY_DOMINATES,
                    priority=0.5, selected_priority=0.9,
                ),
            ],
        )
        assert reg.check(record)["I2"] is True

    def test_enable_disable(self):
        reg = InvariantRegistry()
        reg.disable("I1")
        assert reg.enabled_count == 4
        reg.enable("I1")
        assert reg.enabled_count == 5

    def test_custom_invariant(self):
        reg = InvariantRegistry()
        reg.register(
            name="CUSTOM",
            inv_type=InvariantType.SAFETY,
            description="Custom test invariant",
            check_fn=lambda r: r.proof_status == "PASS",
        )
        record = DecisionRecord(
            decision_id="d0", timestamp=0.0, input_state={}, proof_status="PASS"
        )
        assert reg.check(record)["CUSTOM"] is True


# ─── VerificationEngine ─────────────────────────────────────────────────────────

class TestVerificationEngine:
    def test_verify_single_candidate_pass(self):
        eng = VerificationEngine()
        pt = ProofTrace()
        record = DecisionRecord(
            decision_id="d0",
            timestamp=0.0,
            input_state={"_meta_max_global_gain": 2.0},
            selected_action=pt._make_node(NodeType.ACTION, "action:drl", {"priority": 0.8}),
            gain_node=pt._make_node(
                NodeType.GAIN_NORMALIZATION,
                "gain_normalization",
                {"normalized": {"drl": 1.0, "sbs": 0.5}},
            ),
            rejected_branches=[],
        )
        report = eng.verify(record)
        assert report.overall_passed is True
        assert len(report.failed_invariants) == 0

    def test_verify_gain_exceeds_max_fails_actuator(self):
        eng = VerificationEngine()
        pt = ProofTrace()
        record = DecisionRecord(
            decision_id="d0",
            timestamp=0.0,
            input_state={"_meta_max_global_gain": 1.0},
            selected_action=pt._make_node(NodeType.ACTION, "action:drl", {"priority": 0.8}),
            gain_node=pt._make_node(
                NodeType.GAIN_NORMALIZATION,
                "gain_normalization",
                {"normalized": {"drl": 1.0, "sbs": 0.5}},
            ),
            rejected_branches=[],
        )
        report = eng.verify(record)
        # I1 fails and actuator layer fails
        assert "I1" in report.failed_invariants
        failed_actuator = any(lc.layer == "actuator" and not lc.passed for lc in report.layer_checks)
        assert failed_actuator

    def test_verify_batch(self):
        eng = VerificationEngine()
        pt = ProofTrace()
        records = [
            DecisionRecord(
                decision_id=f"d{i}",
                timestamp=0.0,
                input_state={"_meta_max_global_gain": 2.0},
                selected_action=pt._make_node(NodeType.ACTION, f"action:src{i}", {"priority": 0.8}),
                gain_node=pt._make_node(
                    NodeType.GAIN_NORMALIZATION,
                    "gain_normalization",
                    {"normalized": {"drl": 1.0, "sbs": 0.5}},
                ),
                rejected_branches=[],
            )
            for i in range(3)
        ]
        reports = eng.verify_batch(records)
        assert len(reports) == 3
        assert all(r.overall_passed for r in reports)


# ─── ProofKernel ────────────────────────────────────────────────────────────────

class TestProofKernelBasics:
    def test_submit_resolve_roundtrip(self):
        kernel = ProofKernel()
        kernel.submit(ControlSignal(source="drl", priority=0.9, payload={"delta": 0.1}))
        kernel.submit(ControlSignal(source="sbs", priority=0.5, payload={}))
        winner, record = kernel.resolve()
        assert winner.source == "drl"
        assert record.decision_id == "d_0"
        assert record.arbitration_node is not None
        assert record.gain_node is not None
        assert record.selected_action is not None

    def test_proof_status_pass(self):
        kernel = ProofKernel()
        kernel.submit(ControlSignal(source="drl", priority=0.9, payload={}))
        _, record = kernel.resolve()
        assert record.proof_status == "PASS"

    def test_rejected_branches_stored(self):
        kernel = ProofKernel()
        kernel.submit(ControlSignal(source="drl", priority=0.9, payload={}))
        kernel.submit(ControlSignal(source="sbs", priority=0.5, payload={}))
        _, record = kernel.resolve()
        rejected_sources = [b.source for b in record.rejected_branches]
        assert "sbs" in rejected_sources
        assert "drl" not in rejected_sources

    def test_history_append(self):
        kernel = ProofKernel()
        kernel.submit(ControlSignal(source="drl", priority=0.9, payload={}))
        kernel.resolve()
        assert len(kernel.history) == 1
        assert kernel.last_record() is not None
        assert kernel.last_record().decision_id == "d_0"

    def test_verify_returns_report(self):
        kernel = ProofKernel()
        kernel.submit(ControlSignal(source="drl", priority=0.9, payload={}))
        _, record = kernel.resolve()
        report = kernel.verify(record)
        assert report.decision_id == record.decision_id
        assert report.overall_passed is True

    def test_last_record_none_initially(self):
        kernel = ProofKernel()
        assert kernel.last_record() is None

    def test_registry_accessible(self):
        kernel = ProofKernel()
        assert kernel.registry is not None
        assert kernel.registry.enabled_count == 5
