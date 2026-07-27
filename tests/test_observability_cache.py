from __future__ import annotations

from unittest.mock import patch

from tools.metrics_server import CACHE_HITS, CACHE_MISSES

import pytest


@pytest.mark.unit
def test_ephemeris_cache_increments_counters() -> None:
    """Повторный вызов calculate_natal_chart должен инкрементировать cache hit."""
    from core.ephemeris import _natal_cache, calculate_natal_chart

    _natal_cache.clear()
    before_hits = CACHE_HITS._value.get() if hasattr(CACHE_HITS, "_value") else 0
    before_misses = CACHE_MISSES._value.get() if hasattr(CACHE_MISSES, "_value") else 0

    # Mock the underlying provider to return a valid chart without real ephemeris
    from datetime import datetime
    from core.ephemeris import NatalChart, _default_provider

    mock_chart = NatalChart(
        planets={},
        houses=[],
        timestamp=datetime(2025, 1, 1),
        latitude=55.0,
        longitude=37.0,
    )

    with (
        patch.object(_default_provider, "calculate_planet", return_value=(0.0, 0.0)),
        patch.object(_default_provider, "calculate_houses", return_value=[]),
    ):
        result1 = calculate_natal_chart(datetime(2025, 1, 1), 55.0, 37.0)
        result2 = calculate_natal_chart(datetime(2025, 1, 1), 55.0, 37.0)

    after_hits = CACHE_HITS._value.get() if hasattr(CACHE_HITS, "_value") else 0
    after_misses = CACHE_MISSES._value.get() if hasattr(CACHE_MISSES, "_value") else 0

    assert result1 is not None
    assert result2 is not None
    assert after_misses > before_misses, f"Cache miss should be incremented: {before_misses} -> {after_misses}"
    assert after_hits > before_hits, f"Cache hit should be incremented: {before_hits} -> {after_hits}"
