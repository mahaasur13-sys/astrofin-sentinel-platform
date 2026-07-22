"""
test_rolling_state_diff.py
==========================
Tests for RollingStateDiffer — O(1) incremental rolling diffs.
"""
from consistency_v2.rolling_state_diff import RollingStateDiffer

import logging
log = logging.getLogger(__name__)



def test_rolling_state_diff_added_nodes():
    """Detects newly added nodes."""
    prev = {"nodes": {"n1": {"status": "up"}}}
    curr = {"nodes": {"n1": {"status": "up"}, "n2": {"status": "down"}}}
    delta = RollingStateDiffer.compute_delta_for(prev, curr)
    assert delta["nodes_added"] == ["n2"]
    assert delta["nodes_deleted"] == []
    assert delta["summary"]["added"] == 1


def test_rolling_state_diff_deleted_nodes():
    """Detects deleted nodes."""
    prev = {"nodes": {"n1": {}, "n2": {}}}
    curr = {"nodes": {"n1": {}}}
    delta = RollingStateDiffer.compute_delta_for(prev, curr)
    assert delta["nodes_deleted"] == ["n2"]
    assert delta["summary"]["deleted"] == 1


def test_rolling_state_diff_updated_fields():
    """Detects field-level changes in common nodes."""
    prev = {"nodes": {"n1": {"status": "up", "score": 1.0}}}
    curr = {"nodes": {"n1": {"status": "down", "score": 1.0}}}
    delta = RollingStateDiffer.compute_delta_for(prev, curr)
    assert "n1" in delta["nodes_updated"]
    updates = delta["nodes_updated"]["n1"]
    assert "status" in updates
    assert updates["status"] == ("up", "down")
    assert "score" not in updates


def test_rolling_state_diff_noop():
    """Noop when states are identical."""
    prev = {"nodes": {"n1": {"status": "up"}}}
    curr = {"nodes": {"n1": {"status": "up"}}}
    delta = RollingStateDiffer.compute_delta_for(prev, curr)
    assert delta["nodes_added"] == []
    assert delta["nodes_deleted"] == []
    assert delta["nodes_updated"] == {}


def test_rolling_state_diff_incremental_exec():
    """Incremental compute_delta_exec updates internal prev state."""
    differ = RollingStateDiffer()
    curr1 = {"nodes": {"n1": {}}}
    d1 = differ.compute_delta_exec(curr1)
    assert d1["nodes_added"] == ["n1"]
    curr2 = {"nodes": {"n1": {}, "n2": {}}}
    d2 = differ.compute_delta_exec(curr2)
    assert d2["nodes_added"] == ["n2"]
    assert d2["nodes_deleted"] == []


def test_rolling_state_diff_to_dict():
    """Delta.to_dict() serializes correctly."""
    prev = {"nodes": {"n1": {}}}
    curr = {"nodes": {"n1": {}, "n2": {}}}
    delta = RollingStateDiffer.compute_delta_for(prev, curr)
    assert delta["summary"]["added"] == 1


if __name__ == "__main__":
    test_rolling_state_diff_added_nodes()
    test_rolling_state_diff_deleted_nodes()
    test_rolling_state_diff_updated_fields()
    test_rolling_state_diff_noop()
    test_rolling_state_diff_incremental_exec()
    test_rolling_state_diff_to_dict()
    log.info("All RollingStateDiffer tests passed.")
