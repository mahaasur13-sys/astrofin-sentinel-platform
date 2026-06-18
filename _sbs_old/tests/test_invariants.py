"""
Jepsen-style invariant tests for SBS v1.

Tests verify that GlobalInvariantEngine correctly detects violations
across DRL / CCL / F2 / DESC layers under adversarial conditions.

Coverage:
    - split-brain detection
    - quorum violation
    - leader uniqueness
    - monotonic commit index
    - duplicate ACK / Byzantine signal
    - temporal drift
    - sequence gaps
    - contract verification
"""

import pytest

from sbs.boundary_spec import SystemBoundarySpec
from sbs.global_invariant_engine import GlobalInvariantEngine, LayerState
from sbs.system_contract import SYSTEM_CONTRACT, InvariantType
from sbs.failure_classifier import FailureClassifier, FailureCategory, FailureSeverity


# ── SystemBoundarySpec tests ─────────────────────────────────────────────────

class TestSystemBoundarySpec:
    """Unit tests for SystemBoundarySpec.validate()."""

    def test_no_split_brain__pass(self):
        """System with 1 partition should pass when allow_split_brain=False."""
        spec = SystemBoundarySpec(allow_split_brain=False, max_partitions=1)
        state = {"partitions": 1, "quorum_ratio": 0.9}
        assert spec.validate(state) is True
        assert spec.get_violations() == ()

    def test_no_split_brain__fail(self):
        """System with 2 partitions must fail when allow_split_brain=False."""
        spec = SystemBoundarySpec(allow_split_brain=False, max_partitions=1)
        state = {"partitions": 2, "quorum_ratio": 0.9}
        assert spec.validate(state) is False
        violations = spec.get_violations()
        assert any("SPLIT_BRAIN" in v for v in violations)

    def test_quorum_violation__fail(self):
        """Quorum ratio below threshold must fail."""
        spec = SystemBoundarySpec(quorum_threshold=0.67)
        state = {"partitions": 0, "quorum_ratio": 0.5}
        assert spec.validate(state) is False
        violations = spec.get_violations()
        assert any("QUORUM_VIOLATION" in v for v in violations)

    def test_quorum_ok__pass(self):
        """Quorum ratio at exact threshold should pass."""
        spec = SystemBoundarySpec(quorum_threshold=0.67)
        state = {"partitions": 0, "quorum_ratio": 0.67}
        assert spec.validate(state) is True

    def test_uncommitted_read__fail(self):
        """Uncommitted reads must fail when prohibited."""
        spec = SystemBoundarySpec(allow_uncommitted_read=False)
        state = {"partitions": 0, "quorum_ratio": 0.9, "uncommitted_reads": 3}
        assert spec.validate(state) is False
        violations = spec.get_violations()
        assert any("UNCOMMITTED_READ" in v for v in violations)

    def test_duplicate_ack__fail(self):
        """Duplicate ACK signals Byzantine behavior."""
        spec = SystemBoundarySpec(allow_duplicate_ack=False)
        state = {"partitions": 0, "quorum_ratio": 0.9, "duplicate_ack": True}
        assert spec.validate(state) is False
        violations = spec.get_violations()
        assert any("BYZANTINE" in v for v in violations)

    def test_temporal_drift__fail(self):
        """Clock skew beyond threshold must fail when temporal_strictness=True."""
        spec = SystemBoundarySpec(enable_temporal_strictness=True, clock_skew_threshold_ms=50.0)
        state = {"partitions": 0, "quorum_ratio": 0.9, "clock_skew_ms": 150.0}
        assert spec.validate(state) is False
        violations = spec.get_violations()
        assert any("TEMPORAL_DRIFT" in v for v in violations)

    def test_temporal_drift__pass_when_disabled(self):
        """Clock skew is ignored when enable_temporal_strictness=False."""
        spec = SystemBoundarySpec(enable_temporal_strictness=False, clock_skew_threshold_ms=1.0)
        state = {"partitions": 0, "quorum_ratio": 0.9, "clock_skew_ms": 999.0}
        assert spec.validate(state) is True

    def test_sequence_violation__fail(self):
        """Event sequence gaps must fail when allow_event_reorder=False."""
        spec = SystemBoundarySpec(allow_event_reorder=False)
        state = {"partitions": 0, "quorum_ratio": 0.9, "event_sequence_gaps": 2}
        assert spec.validate(state) is False
        violations = spec.get_violations()
        assert any("SEQUENCE_VIOLATION" in v for v in violations)


# ── GlobalInvariantEngine tests ─────────────────────────────────────────────

class TestGlobalInvariantEngine:
    """Cross-layer invariant tests."""

    def test_all_healthy__pass(self):
        """All layers healthy → engine returns True."""
        spec = SystemBoundarySpec()
        engine = GlobalInvariantEngine(spec)

        drl = {"leader": "node-1", "term": 3, "partitions": 0, "quorum_ratio": 0.9}
        ccl = {"leader": "node-1", "term": 3, "stale_reads": 0}
        f2 = {"leader": "node-1", "term": 3, "quorum_ratio": 0.9, "commit_index": 10}
        desc = {"leader": "node-1", "term": 3, "commit_index": 10}

        assert engine.evaluate(drl, ccl, f2, desc) is True
        assert engine.get_violations() == []

    def test_multiple_leaders__fail(self):
        """Two layers reporting different leaders → leader uniqueness violation."""
        spec = SystemBoundarySpec()
        engine = GlobalInvariantEngine(spec)

        drl = {"leader": "node-1", "term": 3, "partitions": 0}
        ccl = {"leader": "node-2", "term": 3}  # Different leader
        f2 = {"leader": "node-1", "term": 3, "quorum_ratio": 0.9}
        desc = {"leader": "node-1", "term": 3, "commit_index": 5}

        assert engine.evaluate(drl, ccl, f2, desc) is False
        violations = engine.get_violations()
        assert any("LEADER_UNIQUENESS" in v for v in violations)

    def test_commit_index_regression__fail(self):
        """DESC commit index decreasing → monotonic violation."""
        spec = SystemBoundarySpec()
        engine = GlobalInvariantEngine(spec)

        # First call — commit_index = 10
        drl = {"partitions": 0, "quorum_ratio": 0.9}
        ccl = {}
        f2 = {"quorum_ratio": 0.9}
        desc = {"commit_index": 10}
        engine.evaluate(drl, ccl, f2, desc)

        # Second call — commit_index = 8 (regression!)
        desc = {"commit_index": 8}
        assert engine.evaluate(drl, ccl, f2, desc) is False
        violations = engine.get_violations()
        assert any("COMMIT_INDEX_REGRESSION" in v for v in violations)

    def test_term_order_violation__fail(self):
        """Terms out of order across layers → term monotonicity violation."""
        spec = SystemBoundarySpec()
        engine = GlobalInvariantEngine(spec)

        drl = {"term": 5, "partitions": 0}
        ccl = {"term": 3}  # Lower term than DRL
        f2 = {"quorum_ratio": 0.9}
        desc = {"commit_index": 0}

        assert engine.evaluate(drl, ccl, f2, desc) is False
        violations = engine.get_violations()
        assert any("TERM_ORDER_VIOLATION" in v for v in violations)

    def test_split_brain__fail(self):
        """Total partitions > max_partitions → split-brain violation."""
        spec = SystemBoundarySpec(allow_split_brain=False, max_partitions=1)
        engine = GlobalInvariantEngine(spec)

        drl = {"partitions": 1}
        ccl = {"partitions": 1}  # Total = 2 > max_partitions
        f2 = {"quorum_ratio": 0.9}
        desc = {}

        assert engine.evaluate(drl, ccl, f2, desc) is False
        violations = engine.get_violations()
        assert any("SPLIT_BRAIN" in v for v in violations)


# ── SYSTEM_CONTRACT tests ─────────────────────────────────────────────────────

class TestSystemContract:
    """SYSTEM_CONTRACT hard constraints tests."""

    def test_verify_valid(self):
        """Matching invariant value → True."""
        assert SYSTEM_CONTRACT.verify("no_split_brain_commit", True) is True

    def test_verify_invalid(self):
        """Mismatching invariant value → False."""
        assert SYSTEM_CONTRACT.verify("no_split_brain_commit", False) is False

    def test_verify_unknown_raises(self):
        """Unknown invariant name → KeyError."""
        with pytest.raises(KeyError):
            SYSTEM_CONTRACT.verify("unknown_invariant_xyz", True)

    def test_verify_all_all_pass(self):
        """All invariants match → (True, [])."""
        reported = {name: True for name in SYSTEM_CONTRACT.list_invariants()}
        ok, violations = SYSTEM_CONTRACT.verify_all(reported)
        assert ok is True
        assert violations == []

    def test_verify_all_one_fail(self):
        """One invariant mismatch → (False, [violation])."""
        reported = {name: True for name in SYSTEM_CONTRACT.list_invariants()}
        reported["no_split_brain_commit"] = False
        ok, violations = SYSTEM_CONTRACT.verify_all(reported)
        assert ok is False
        assert len(violations) == 1
        assert "CONTRACT_VIOLATION" in violations[0]

    def test_verify_all_unknown(self):
        """Unknown invariant in reported → (False, [UNKNOWN_INVARIANT])."""
        ok, violations = SYSTEM_CONTRACT.verify_all({"unknown_xyz": True})
        assert ok is False
        assert any("UNKNOWN_INVARIANT" in v for v in violations)


# ── FailureClassifier tests ───────────────────────────────────────────────────

class TestFailureClassifier:
    """FailureClassifier taxonomy tests."""

    def test_network_partition(self):
        """'partition' type → NETWORK_PARTITION, HIGH severity."""
        classifier = FailureClassifier()
        result = classifier.classify({"type": "partition", "layer": "DRL", "description": "net split"})
        assert result.category == FailureCategory.NETWORK_PARTITION
        assert result.severity == FailureSeverity.HIGH

    def test_message_loss(self):
        """'drop' type → MESSAGE_LOSS."""
        classifier = FailureClassifier()
        result = classifier.classify({"type": "drop", "layer": "DRL"})
        assert result.category == FailureCategory.MESSAGE_LOSS
        assert result.severity == FailureSeverity.MEDIUM

    def test_byzantine(self):
        """'byzantine' type → BYZANTINE_BEHAVIOR, CRITICAL."""
        classifier = FailureClassifier()
        result = classifier.classify({"type": "byzantine", "layer": "F2"})
        assert result.category == FailureCategory.BYZANTINE_BEHAVIOR
        assert result.severity == FailureSeverity.CRITICAL

    def test_clock_skew(self):
        """'clock_skew' type → TEMPORAL_DRIFT."""
        classifier = FailureClassifier()
        result = classifier.classify({"type": "clock_skew", "layer": "DRL"})
        assert result.category == FailureCategory.TEMPORAL_DRIFT
        assert result.severity == FailureSeverity.MEDIUM

    def test_consensus_violation(self):
        """'consensus_violation' type → CONSENSUS_BREAK, CRITICAL."""
        classifier = FailureClassifier()
        result = classifier.classify({"type": "consensus_violation", "layer": "CCL"})
        assert result.category == FailureCategory.CONSENSUS_BREAK
        assert result.severity == FailureSeverity.CRITICAL

    def test_quorum_violation(self):
        """'quorum_violation' type → QUORUM_VIOLATION."""
        classifier = FailureClassifier()
        result = classifier.classify({"type": "quorum_violation", "layer": "F2"})
        assert result.category == FailureCategory.QUORUM_VIOLATION
        assert result.severity == FailureSeverity.HIGH

    def test_unknown_type(self):
        """Unknown type → UNKNOWN_FAILURE."""
        classifier = FailureClassifier()
        result = classifier.classify({"type": "completely_unknown_type_xyz", "layer": "TEST"})
        assert result.category == FailureCategory.UNKNOWN_FAILURE
        assert result.severity == FailureSeverity.HIGH

    def test_classify_batch(self):
        """Batch classification returns correct count."""
        classifier = FailureClassifier()
        events = [
            {"type": "partition", "layer": "DRL"},
            {"type": "drop", "layer": "DRL"},
            {"type": "byzantine", "layer": "F2"},
        ]
        results = classifier.classify_batch(events)
        assert len(results) == 3
        assert results[0].category == FailureCategory.NETWORK_PARTITION
        assert results[1].category == FailureCategory.MESSAGE_LOSS
        assert results[2].category == FailureCategory.BYZANTINE_BEHAVIOR

    def test_classified_failure_str(self):
        """ClassifiedFailure __str__ is human-readable."""
        classifier = FailureClassifier()
        result = classifier.classify({"type": "partition", "layer": "DRL", "description": "net split"})
        s = str(result)
        assert "HIGH" in s
        assert "NETWORK_PARTITION" in s
        assert "DRL" in s


# ── LayerState tests ──────────────────────────────────────────────────────────

class TestLayerState:
    """LayerState normalization tests."""

    def test_from_dict_full(self):
        """All fields populated → all fields set correctly."""
        state = LayerState.from_dict("DRL", {
            "leader": "node-1",
            "term": 7,
            "commit_index": 42,
            "partitions": 0,
            "quorum_ratio": 0.9,
            "stale_reads": 0,
            "duplicate_ack": False,
            "clock_skew_ms": 12.5,
            "event_sequence_gaps": 0,
        })
        assert state.name == "DRL"
        assert state.leader == "node-1"
        assert state.term == 7
        assert state.commit_index == 42
        assert state.partitions == 0
        assert state.quorum_ratio == 0.9
        assert state.stale_reads == 0
        assert state.duplicate_ack is False
        assert state.clock_skew_ms == 12.5
        assert state.event_sequence_gaps == 0

    def test_from_dict_missing_fields(self):
        """Missing fields → defaults applied."""
        state = LayerState.from_dict("F2", {})
        assert state.leader is None
        assert state.term == 0
        assert state.commit_index == 0
        assert state.partitions == 0
        assert state.quorum_ratio == 0.0
        assert state.stale_reads == 0
        assert state.duplicate_ack is False
        assert state.clock_skew_ms == 0.0
        assert state.event_sequence_gaps == 0
