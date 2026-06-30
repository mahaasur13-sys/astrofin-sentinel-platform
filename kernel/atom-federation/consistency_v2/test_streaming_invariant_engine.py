"""
test_streaming_invariant_engine.py
==================================
Tests for StreamingInvariantEngine — continuous delta verification.
"""
from consistency_v2.streaming_invariant_engine import (
    StreamingInvariantEngine,
)


def _simple_delta(prev: dict, curr: dict) -> dict:
    """Minimal delta: just nodes that changed."""
    added = list(set(curr.get("nodes", {}) or {}) - set(prev.get("nodes", {}) or {}))
    deleted = list(set(prev.get("nodes", {}) or {}) - set(curr.get("nodes", {}) or {}))
    return {"added": added, "deleted": deleted}


def test_streaming_invariant_engine_sI1_pass():
    """sI1 passes when deltas are identical in both domains."""
    engine = StreamingInvariantEngine(
        get_state_delta_exec=_simple_delta,
        get_state_delta_replay=_simple_delta,
    )
    curr_e = {"nodes": {"node-1": {"status": "up"}}}
    curr_r = {"nodes": {"node-1": {"status": "up"}}}
    results = engine.verify(curr_e, curr_r, [], [])
    assert results[0].invariant_id == "sI1"
    assert results[0].passed is True
    assert results[0].delta_drift < 1e-9


def test_streaming_invariant_engine_sI1_fail():
    """sI1 fails when deltas diverge between domains."""
    def exec_delta(prev, curr):
        return {"added": list(set(curr.get("nodes", {}) or {}) - set(prev.get("nodes", {}) or {}))}
    def replay_delta(prev, curr):
        return {"added": ["wrong-node"]}

    engine = StreamingInvariantEngine(
        get_state_delta_exec=exec_delta,
        get_state_delta_replay=replay_delta,
    )
    curr_e = {"nodes": {"node-1": {}}}
    curr_r = {"nodes": {"node-1": {}}}
    results = engine.verify(curr_e, curr_r, [], [])
    assert results[0].invariant_id == "sI1"
    assert results[0].passed is False
    assert results[0].delta_drift > 0.0


def test_streaming_invariant_engine_sliding_window():
    """Sliding window returns only results within time range."""
    engine = StreamingInvariantEngine(
        get_state_delta_exec=_simple_delta,
        get_state_delta_replay=_simple_delta,
    )
    curr = {"nodes": {}}
    for _ in range(5):
        engine.verify(curr, curr, [], [])
    report = engine.get_sliding_report(window_s=0.0)
    assert report.total_checks == 0
    report = engine.get_sliding_report(window_s=3600.0)
    assert report.total_checks == 5
    assert report.passed_checks == 5
    assert report.all_passed is True


def test_streaming_invariant_engine_no_causal_fns():
    """sI2 and sI3 skip gracefully when no causal/SBS fns provided."""
    engine = StreamingInvariantEngine(
        get_state_delta_exec=_simple_delta,
        get_state_delta_replay=_simple_delta,
    )
    results = engine.verify({"nodes": {}}, {"nodes": {}}, [], [])
    sI2 = next(r for r in results if r.invariant_id == "sI2")
    sI3 = next(r for r in results if r.invariant_id == "sI3")
    assert sI2.passed is True
    assert sI3.passed is True
    assert "SKIP" in sI2.details


def test_streaming_invariant_engine_to_dict():
    """StreamingReport.to_dict() serializes correctly."""
    engine = StreamingInvariantEngine(
        get_state_delta_exec=_simple_delta,
        get_state_delta_replay=_simple_delta,
    )
    engine.verify({"nodes": {"n1": {}}}, {"nodes": {"n1": {}}}, [], [])
    report = engine.get_sliding_report(window_s=1.0)
    d = report.to_dict()
    assert "window_s" in d
    assert "checks" in d
    assert d["total"] == 1


if __name__ == "__main__":
    test_streaming_invariant_engine_sI1_pass()
    test_streaming_invariant_engine_sI1_fail()
    test_streaming_invariant_engine_sliding_window()
    test_streaming_invariant_engine_no_causal_fns()
    test_streaming_invariant_engine_to_dict()
    print("All StreamingInvariantEngine tests passed.")
