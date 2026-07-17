"""
test_persistence.py
~~~~~~~~~~~~~~~~~~~~
Tests for persistence layer: StateWindowStore, DecisionMemory, StabilityLedger.
"""

from meta_control.persistence.decision_memory import DecisionMemory
from meta_control.persistence.stability_ledger import (
    StabilityLedger,
    StabilityTrend,
)
from meta_control.persistence.state_window_store import StateWindowStore

# ─── StateWindowStore ────────────────────────────────────────────────────────

class TestStateWindowStore:
    def test_record_tick_returns_incrementing_tick(self):
        store = StateWindowStore(window_size=10)
        t1 = store.record_tick({"drl": 0.9}, {"drl": 0.8}, 1.0)
        t2 = store.record_tick({"sbs": 0.7}, {"sbs": 0.6}, 0.9)
        assert t2 == t1 + 1

    def test_record_tick_bounds_by_window_size(self):
        store = StateWindowStore(window_size=3)
        for i in range(5):
            store.record_tick({f"s{i}": 0.5}, {f"s{i}": 0.5}, 0.5)
        assert store.depth == 3
        assert store.current_tick == 5

    def test_record_outcome_backfills(self):
        store = StateWindowStore(window_size=10)
        tick = store.record_tick({"drl": 0.9}, {"drl": 0.8}, 1.0)
        store.record_outcome(tick, 0.95)
        ts = store.get_tick(tick)
        assert ts is not None
        assert ts.outcome == 0.95

    def test_record_outcome_returns_false_for_unknown_tick(self):
        store = StateWindowStore(window_size=10)
        ok = store.record_outcome(9999, 0.5)
        assert ok is False

    def test_rollback_to_removes_newer_ticks(self):
        store = StateWindowStore(window_size=10)
        t1 = store.record_tick({"drl": 0.9}, {"drl": 0.8}, 1.0)
        store.record_tick({"sbs": 0.7}, {"sbs": 0.6}, 0.9)
        store.record_tick({"coh": 0.5}, {"coh": 0.4}, 0.8)
        removed = store.rollback_to(t1)
        assert len(removed) == 2
        assert store.depth == 1
        # current_tick stays at 3 (highest assigned), but deque has only tick 1
        assert store.current_tick == 3
        # next tick will be 4
        assert store.record_tick({}, {}, 1.0) == 4

    def test_latest_tick(self):
        store = StateWindowStore(window_size=5)
        assert store.latest_tick() is None
        t = store.record_tick({"drl": 0.9}, {"drl": 0.8}, 1.0)
        latest = store.latest_tick()
        assert latest is not None
        assert latest.tick == t

    def test_avg_stability(self):
        store = StateWindowStore(window_size=5)
        store.record_tick({"drl": 0.9, "sbs": 0.7}, {"drl": 0.8}, 1.0)
        store.record_tick({"drl": 0.5, "sbs": 0.5}, {"drl": 0.6}, 0.9)
        avg = store.avg_stability(last_n=2)
        assert abs(avg - 0.65) < 0.01

    def test_source_stability_series(self):
        store = StateWindowStore(window_size=5)
        store.record_tick({"drl": 0.9}, {}, 1.0)
        store.record_tick({"drl": 0.5}, {}, 0.9)
        series = store.source_stability_series("drl")
        assert series == [0.9, 0.5]

    def test_outcome_series(self):
        store = StateWindowStore(window_size=5)
        store.record_tick({}, {}, 1.0, outcome=0.8)
        store.record_tick({}, {}, 0.9, outcome=None)
        store.record_tick({}, {}, 0.8, outcome=0.7)
        outcomes = store.outcome_series()
        assert outcomes == [0.8, 0.7]


# ─── DecisionMemory ─────────────────────────────────────────────────────────

class TestDecisionMemory:
    def test_append_increments_id(self):
        mem = DecisionMemory(max_memory=100)
        id1 = mem.append("drl", 0.9, {"delta": 0.1}, True, 0.8)
        id2 = mem.append("sbs", 0.5, {}, False, 0.6)
        assert id2 == id1 + 1

    def test_recent_returns_newest_last(self):
        mem = DecisionMemory(max_memory=10)
        for i in range(5):
            mem.append(f"s{i}", 0.5, {"i": i}, True, 0.7)
        recent = mem.recent(3)
        assert len(recent) == 3
        assert recent[-1].source == "s4"

    def test_find_similar_exact_match(self):
        mem = DecisionMemory(max_memory=50)
        mem.append("drl", 0.9, {"delta": 0.1, "threshold": 0.05}, True, 0.8)
        mem.append("sbs", 0.5, {"delta": 0.2, "threshold": 0.05}, True, 0.7)
        results = mem.find_similar({"delta": 0.1, "threshold": 0.05}, k=2)
        assert len(results) == 2
        assert results[0][1] == 1.0
        assert results[0][0].source == "drl"

    def test_find_similar_partial_match(self):
        mem = DecisionMemory(max_memory=50)
        mem.append("drl", 0.9, {"delta": 0.1, "threshold": 0.05}, True, 0.8)
        results = mem.find_similar({"delta": 0.1, "threshold": 0.1}, k=1)
        assert results[0][1] == 0.5

    def test_find_similar_no_shared_keys(self):
        mem = DecisionMemory(max_memory=50)
        mem.append("drl", 0.9, {"delta": 0.1}, True, 0.8)
        results = mem.find_similar({"unrelated": 99}, k=1)
        assert results[0][1] == 0.0

    def test_outcome_stats(self):
        mem = DecisionMemory(max_memory=100)
        mem.append("drl", 0.9, {}, True, 0.8, outcome=0.8)
        mem.append("sbs", 0.5, {}, True, 0.7, outcome=0.6)
        mem.append("coh", 0.6, {}, True, 0.9, outcome=0.7)
        stats = mem.outcome_stats()
        assert stats["count"] == 3
        assert abs(stats["mean"] - 0.7) < 0.01
        assert stats["min"] == 0.6
        assert stats["max"] == 0.8

    def test_proof_reliability(self):
        mem = DecisionMemory(max_memory=100)
        mem.append("drl", 0.9, {}, True, 0.8, outcome=0.9)
        mem.append("sbs", 0.5, {}, False, 0.7, outcome=0.3)
        mem.append("coh", 0.6, {}, True, 0.9, outcome=0.2)
        reliability = mem.proof_reliability()
        assert abs(reliability - 0.666) < 0.01

    def test_record_outcome_backfills(self):
        mem = DecisionMemory(max_memory=100)
        did = mem.append("drl", 0.9, {}, True, 0.8)
        mem.record_outcome(did, 0.85)
        rec = mem.get(did)
        assert rec is not None
        assert rec.outcome == 0.85
        assert rec.outcome_timestamp is not None

    def test_max_memory_eviction(self):
        mem = DecisionMemory(max_memory=3)
        ids = [mem.append(f"s{i}", 0.5, {}, True, 0.7) for i in range(5)]
        assert mem.count == 3
        assert mem.get(ids[0]) is None
        assert mem.get(ids[2]) is not None


# ─── StabilityLedger ─────────────────────────────────────────────────────────

class TestStabilityLedger:
    def test_record_and_is_coherent(self):
        ledger = StabilityLedger(epoch_duration=3600, coherence_threshold=0.7)
        ledger.record("drl", 0.9, violated=False)
        ledger.record("drl", 0.8, violated=False)
        assert ledger.is_coherent("drl") is True

    def test_record_and_is_drifting(self):
        ledger = StabilityLedger(epoch_duration=3600, violation_threshold=0.15)
        for _ in range(10):
            ledger.record("drl", 0.3, violated=True)
        assert ledger.is_drifting("drl") is True

    def test_global_trend(self):
        ledger = StabilityLedger(epoch_duration=3600)
        ledger.record("drl", 0.9, violated=False)
        ledger.record("sbs", 0.7, violated=False)
        trend = ledger.global_trend()
        assert isinstance(trend, StabilityTrend)
        assert trend.global_avg_stability >= 0.8

    def test_source_statuses(self):
        ledger = StabilityLedger(epoch_duration=3600)
        ledger.record("drl", 0.9, violated=False)
        ledger.record("sbs", 0.4, violated=True)
        statuses = ledger.source_statuses()
        assert "drl" in statuses
        assert "sbs" in statuses
        assert statuses["drl"]["is_coherent"] is True
        assert statuses["sbs"]["is_drifting"] is True

    def test_auto_epoch_reset_discards_expired_data(self):
        import time
        ledger = StabilityLedger(epoch_duration=0.1)
        ledger.record("drl", 0.9, violated=False)
        time.sleep(0.15)
        _ = ledger.is_coherent("drl")
        ledger.record("drl", 0.5, violated=False)
        statuses = ledger.source_statuses()
        assert statuses["drl"]["sample_count"] == 1

    def test_unknown_source_defaults(self):
        ledger = StabilityLedger(coherence_threshold=0.7, violation_threshold=0.15)
        assert ledger.is_coherent("unknown") is True
        assert ledger.is_drifting("unknown") is False
