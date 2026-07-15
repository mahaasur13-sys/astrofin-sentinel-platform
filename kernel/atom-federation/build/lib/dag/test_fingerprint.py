"""
Tests for DAG incremental fingerprint — v8.5
"""
import pytest

from dag.fingerprint import (
    ChangeType,
    DAGFingerprintBridge,
    DAGValidator,
    IncrementalFingerprint,
    IncrementalNodeHash,
)


class TestIncrementalNodeHash:
    def test_compute_deterministic(self):
        inh1 = IncrementalNodeHash(
            node_id="A", content={"val": 1}, parent_ids=(), layer=0,
        ).compute()
        inh2 = IncrementalNodeHash(
            node_id="A", content={"val": 1}, parent_ids=(), layer=0,
        ).compute()
        assert inh1.full_hash == inh2.full_hash

    def test_different_content_different_hash(self):
        inh1 = IncrementalNodeHash(
            node_id="A", content={"val": 1}, parent_ids=(), layer=0,
        ).compute()
        inh2 = IncrementalNodeHash(
            node_id="A", content={"val": 2}, parent_ids=(), layer=0,
        ).compute()
        assert inh1.full_hash != inh2.full_hash

    def test_layer_from_parents(self):
        assert IncrementalNodeHash.layer_from_parents([], ()) == 0
        assert IncrementalNodeHash.layer_from_parents([0], ("p",)) == 1
        assert IncrementalNodeHash.layer_from_parents([0, 1], ("p0", "p1")) == 2


class TestIncrementalFingerprint:
    def test_empty_graph(self):
        fp = IncrementalFingerprint().compute_fingerprint([])
        assert fp.total_nodes == 0
        assert fp.max_layer == 0

    def test_single_root(self):
        fp = IncrementalFingerprint().compute_fingerprint([
            {"node_id": "A", "parent_ids": []},
        ])
        assert fp.total_nodes == 1
        assert fp.root_hash != b""

    def test_two_layer_chain(self):
        fp = IncrementalFingerprint().compute_fingerprint([
            {"node_id": "A", "parent_ids": []},
            {"node_id": "B", "parent_ids": ["A"]},
        ])
        assert fp.total_nodes == 2

    def test_full_diamond(self):
        """A → B, A → C, B → D, C → D"""
        fp = IncrementalFingerprint().compute_fingerprint([
            {"node_id": "A", "parent_ids": []},
            {"node_id": "B", "parent_ids": ["A"]},
            {"node_id": "C", "parent_ids": ["A"]},
            {"node_id": "D", "parent_ids": ["B", "C"]},
        ])
        assert fp.total_nodes == 4

    def test_cycle_detection(self):
        with pytest.raises(ValueError, match="Cycle"):
            IncrementalFingerprint().compute_fingerprint([
                {"node_id": "A", "parent_ids": ["B"]},
                {"node_id": "B", "parent_ids": ["A"]},
            ])

    def test_incremental_update_add_node(self):
        base = [
            {"node_id": "A", "parent_ids": []},
            {"node_id": "B", "parent_ids": ["A"]},
        ]
        fp1 = IncrementalFingerprint().compute_fingerprint(base)
        extended = base + [{"node_id": "C", "parent_ids": ["A"]}]
        fp2 = IncrementalFingerprint().compute_fingerprint(extended)
        assert fp2.total_nodes == 3
        assert fp2.root_hash != fp1.root_hash

    def test_incremental_update_mutate_leaf(self):
        nodes = [
            {"node_id": "A", "parent_ids": []},
            {"node_id": "B", "parent_ids": ["A"], "val": 1},
        ]
        fp1 = IncrementalFingerprint().compute_fingerprint(nodes)
        nodes[1]["val"] = 2
        fp2 = IncrementalFingerprint().compute_fingerprint(nodes)
        assert fp2.root_hash != fp1.root_hash

    def test_idempotent_content_unchanged(self):
        nodes = [{"node_id": "A", "parent_ids": []}]
        fp1 = IncrementalFingerprint().compute_fingerprint(nodes)
        fp2 = IncrementalFingerprint().compute_fingerprint(nodes)
        assert fp1.root_hash == fp2.root_hash

    def test_dag_validator_valid(self):
        nodes = [
            {"node_id": "A", "parent_ids": []},
            {"node_id": "B", "parent_ids": ["A"]},
        ]
        is_valid, errors = DAGValidator.validate_dag(nodes)
        assert is_valid, errors

    def test_dag_validator_missing_parent(self):
        nodes = [{"node_id": "B", "parent_ids": ["X"]}]
        is_valid, errors = DAGValidator.validate_dag(nodes)
        assert not is_valid
        assert any("X" in e for e in errors)

    def test_dag_validator_no_root(self):
        nodes = [{"node_id": "A", "parent_ids": ["B"]},
                 {"node_id": "B", "parent_ids": ["A"]}]
        is_valid, errors = DAGValidator.validate_dag(nodes)
        assert not is_valid

    def test_dag_validator_cycle(self):
        nodes = [
            {"node_id": "A", "parent_ids": ["B"]},
            {"node_id": "B", "parent_ids": ["C"]},
            {"node_id": "C", "parent_ids": ["A"]},
        ]
        is_valid, errors = DAGValidator.validate_dag(nodes)
        assert not is_valid
        assert any("Cycle" in e for e in errors)

    def test_diff_detects_added(self):
        inc = IncrementalFingerprint()
        prev = inc.compute_fingerprint([{"node_id": "A", "parent_ids": []}])
        curr = inc.compute_fingerprint([
            {"node_id": "A", "parent_ids": []},
            {"node_id": "B", "parent_ids": ["A"]},
        ])
        changes = inc.diff(curr, prev)
        added = [c for c in changes if c.change_type == ChangeType.ADDED]
        assert len(added) == 1
        assert added[0].node_id == "B"

    def test_diff_detects_removed(self):
        inc = IncrementalFingerprint()
        prev = inc.compute_fingerprint([
            {"node_id": "A", "parent_ids": []},
            {"node_id": "B", "parent_ids": ["A"]},
        ])
        curr = inc.compute_fingerprint([{"node_id": "A", "parent_ids": []}])
        changes = inc.diff(curr, prev)
        removed = [c for c in changes if c.change_type == ChangeType.REMOVED]
        assert len(removed) == 1
        assert removed[0].node_id == "B"

    def test_diff_none_previous(self):
        inc = IncrementalFingerprint()
        curr = inc.compute_fingerprint([{"node_id": "A", "parent_ids": []}])
        changes = inc.diff(curr, None)
        assert all(c.change_type in (ChangeType.ADDED,) for c in changes)


class TestDAGFingerprintBridge:
    def test_compute_and_check(self):
        bridge = DAGFingerprintBridge()
        fp = bridge.compute([{"node_id": "A", "parent_ids": []}])
        assert bridge.check({"dag_fingerprint": fp}) is True

    def test_check_missing_returns_true(self):
        bridge = DAGFingerprintBridge()
        assert bridge.check({}) is True
        assert bridge.check({"other": 123}) is True

    def test_stable_since_same_hash(self):
        bridge = DAGFingerprintBridge()
        fp = bridge.compute([{"node_id": "A", "parent_ids": []}])
        assert bridge.stable_since(fp) is True

    def test_stable_since_different_hash(self):
        bridge = DAGFingerprintBridge()
        fp1 = bridge.compute([{"node_id": "A", "parent_ids": []}])
        fp2 = IncrementalFingerprint().compute_fingerprint([
            {"node_id": "A", "parent_ids": []},
            {"node_id": "B", "parent_ids": ["A"]},
        ])
        assert bridge.stable_since(fp2) is False
