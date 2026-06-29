from __future__ import annotations

from tools.metrics_server import CACHE_HITS, CACHE_MISSES


import pytest


@pytest.mark.unit
def test_belief_get_cache_increments_counters():
    """Повторный вызов get() для одного агента должен инкрементировать hit/miss."""
    from core.belief import BeliefTracker

    # Создаём трекер с временной базой
    tracker = BeliefTracker()

    # Очищаем кеш, если он есть (сейчас его нет, но появится после правок)
    if hasattr(tracker, "_cache"):
        tracker._cache.clear()

    before_hits = CACHE_HITS._value.get() if hasattr(CACHE_HITS, "_value") else 0
    before_misses = CACHE_MISSES._value.get() if hasattr(CACHE_MISSES, "_value") else 0

    # Подготовим тестового агента: вставим строку напрямую в базу
    tracker.update_from_session(
        {
            "all_signals": [{"agent_name": "TestAgent", "signal": "LONG"}],
            "final_recommendation": {"signal": "LONG"},
            "session_id": "test-session",
        }
    )

    # Теперь дважды вызовем get("TestAgent")
    state1 = tracker.get("TestAgent")
    state2 = tracker.get("TestAgent")

    after_hits = CACHE_HITS._value.get() if hasattr(CACHE_HITS, "_value") else 0
    after_misses = CACHE_MISSES._value.get() if hasattr(CACHE_MISSES, "_value") else 0

    assert state1 is not None
    assert state1.agent_name == "TestAgent"
    assert state2.agent_name == "TestAgent"
    assert after_misses > before_misses, f"Cache miss should be incremented: {before_misses} -> {after_misses}"
    assert after_hits > before_hits, f"Cache hit should be incremented: {before_hits} -> {after_hits}"
