from unittest.mock import patch


from tools.metrics_server import CACHE_HITS, CACHE_MISSES


import pytest
@pytest.mark.unit
def test_ephemeris_cache_increments_counters():
    """Повторный вызов calculate_natal_chart должен инкрементировать cache hit."""
    from core.ephemeris import (
        _natal_cache,
        calculate_natal_chart,
    )

    # Сбрасываем кеш
    _natal_cache.clear()
    before_hits = CACHE_HITS._value.get() if hasattr(CACHE_HITS, "_value") else 0
    before_misses = CACHE_MISSES._value.get() if hasattr(CACHE_MISSES, "_value") else 0

    # Мокаем внутреннюю функцию
    with patch("core.ephemeris._calculate_natal_chart_uncached", return_value={"sun": 0.0}):
        result1 = calculate_natal_chart("2025-01-01")
        result2 = calculate_natal_chart("2025-01-01")

    after_hits = CACHE_HITS._value.get() if hasattr(CACHE_HITS, "_value") else 0
    after_misses = CACHE_MISSES._value.get() if hasattr(CACHE_MISSES, "_value") else 0

    assert result1 == result2
    assert after_misses > before_misses, "Cache miss should be incremented"
    assert after_hits > before_hits, "Cache hit should be incremented"
