"""
test_realtime_divergence_detector.py
====================================
Tests for RealtimeDivergenceDetector.
"""
from consistency_v2.realtime_divergence_detector import (
    DivergenceType,
    RealtimeDivergenceDetector,
    _state_hash,
)


def test_state_hash_stable():
    """Same logical state produces same hash regardless of wallclock."""
    s1 = {"nodes": {"n1": {"status": "up"}}, "wallclock_ns": 1000}
    s2 = {"nodes": {"n1": {"status": "up"}}, "wallclock_ns": 2000}
    assert _state_hash(s1) == _state_hash(s2)


def test_state_hash_unstable():
    """Different logical states produce different hashes."""
    s1 = {"nodes": {"n1": {"status": "up"}}}
    s2 = {"nodes": {"n1": {"status": "down"}}}
    assert _state_hash(s1) != _state_hash(s2)


def test_realtime_divergence_detector_temporal_drift():
    """Detects when identical state reached at different wallclock times."""
    exec_state = {"nodes": {}, "wallclock_ns": 1000}
    replay_state = {"nodes": {}, "wallclock_ns": 1000}
    detector = RealtimeDivergenceDetector(
        exec_state_fn=lambda: exec_state,
        replay_state_fn=lambda: replay_state,
    )
    report = detector.verify()
    assert report.all_consistent is True

    # Now drift: identical state, 600ms apart (> CRITICAL threshold)
    exec_state["wallclock_ns"] = 1000
    replay_state["wallclock_ns"] = 1000600000
    report = detector.verify()
    assert report.all_consistent is False
    div = report.events[0]
    assert div.divergence_type == DivergenceType.TEMPORAL_DRIFT
    assert div.severity == "critical"


def test_realtime_divergence_detector_no_divergence():
    """No events when states are different (no temporal match)."""
    exec_state = {"nodes": {"n1": {}}, "wallclock_ns": 1000}
    replay_state = {"nodes": {"n2": {}}, "wallclock_ns": 2000}
    detector = RealtimeDivergenceDetector(
        exec_state_fn=lambda: exec_state,
        replay_state_fn=lambda: replay_state,
    )
    report = detector.verify()
    assert report.all_consistent is True


def test_realtime_divergence_detector_rate_divergence():
    """Detects when transition rates differ between domains."""
    exec_state = {"nodes": {"n1": {}}, "wallclock_ns": 100000000}
    replay_state = {"nodes": {"n1": {}}, "wallclock_ns": 100000000}
    detector = RealtimeDivergenceDetector(
        exec_state_fn=lambda: exec_state,
        replay_state_fn=lambda: replay_state,
        max_transition_history=100,
    )

    # Generate 10 transitions in exec
    for i in range(10):
        exec_state["wallclock_ns"] += 60000000000
        detector.verify()

    # Only 2 in replay
    replay_state["wallclock_ns"] = 100000000
    for i in range(2):
        replay_state["wallclock_ns"] += 60000000000
        detector.verify()

    report = detector.verify()
    print(f"Rate divergence: {report.to_dict()}")


def test_realtime_divergence_detector_coherence_trajectory():
    """Detects when coherence degrades at different rates."""
    exec_state = {"nodes": {"n1": {}}, "coherence": 0.1}
    replay_state = {"nodes": {"n1": {}}, "coherence": 0.1}

    def coherence_fn(state):
        return {"n1": state.get("coherence", 0.0)}

    detector = RealtimeDivergenceDetector(
        exec_state_fn=lambda: exec_state,
        replay_state_fn=lambda: replay_state,
        get_coherence_drift_fn=coherence_fn,
    )

    # Tick 1: baseline
    detector.verify()

    # Tick 2: exec jumps, replay stays
    exec_state["coherence"] = 0.9
    report = detector.verify()
    print(f"Coherence: {report.to_dict()}")


def test_realtime_divergence_detector_to_dict():
    """DivergenceReport.to_dict() serializes correctly."""
    exec_state = {"nodes": {}, "wallclock_ns": 1000}
    replay_state = {"nodes": {}, "wallclock_ns": 2000}
    detector = RealtimeDivergenceDetector(
        exec_state_fn=lambda: exec_state,
        replay_state_fn=lambda: replay_state,
    )
    report = detector.verify()
    d = report.to_dict()
    assert "total_checks" in d
    assert "all_consistent" in d


if __name__ == "__main__":
    test_state_hash_stable()
    test_state_hash_unstable()
    test_realtime_divergence_detector_temporal_drift()
    test_realtime_divergence_detector_no_divergence()
    test_realtime_divergence_detector_rate_divergence()
    test_realtime_divergence_detector_coherence_trajectory()
    test_realtime_divergence_detector_to_dict()
    print("All RealtimeDivergenceDetector tests passed.")
