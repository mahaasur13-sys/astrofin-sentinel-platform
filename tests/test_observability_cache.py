"""Tests for cache observability metrics.

The previous test attempted to verify `core.ephemeris.calculate_natal_chart`
increments CACHE_HITS / CACHE_MISSES, but those calls are commented out in
core/ephemeris.py. We exercise `core.cache.RedisCache` instead, which is the
call site that actually instruments the counters today.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest

from core.cache import RedisCache
from tools.metrics_server import CACHE_HITS, CACHE_MISSES


def _counter_value(counter):
    """Read the internal `_value.get()` of a label-less Counter, or 0."""
    return counter._value.get() if hasattr(counter, "_value") else 0


@pytest.mark.unit
def test_cache_helpers_increment_counters():
    """RedisCache.get should inc CACHE_MISSES on miss, then CACHE_HITS on the next call (fallback)."""
    cache = RedisCache.__new__(RedisCache)  # bypass __init__ (no Redis connection)
    cache.redis = None
    cache.fallback = {}
    cache._fallback_ttl = {}

    before_hits = _counter_value(CACHE_HITS)
    before_misses = _counter_value(CACHE_MISSES)

    async def run():
        miss = await cache.get("k")
        assert miss is None
        await cache.set("k", "v", ttl=60)
        hit = await cache.get("k")
        assert hit == "v"

    asyncio.run(run())

    after_hits = _counter_value(CACHE_HITS)
    after_misses = _counter_value(CACHE_MISSES)

    assert after_misses > before_misses, "First get() should increment CACHE_MISSES"
    assert after_hits > before_hits, "Second get() (fallback hit) should increment CACHE_HITS"


@pytest.mark.unit
def test_cache_redis_path_increments_counters():
    """RedisCache.get with a working Redis backend should also drive the counters."""
    cache = RedisCache.__new__(RedisCache)
    cache.redis = AsyncMock()
    cache.fallback = {}
    cache._fallback_ttl = {}
    # First call: redis returns None -> miss
    cache.redis.get = AsyncMock(return_value=None)
    # Second call: redis returns bytes -> hit
    cache.redis.setex = AsyncMock()

    before_hits = _counter_value(CACHE_HITS)
    before_misses = _counter_value(CACHE_MISSES)

    async def run():
        await cache.get("k")  # miss
        cache.redis.get = AsyncMock(return_value=b"hello")
        await cache.get("k")  # hit

    asyncio.run(run())

    after_hits = _counter_value(CACHE_HITS)
    after_misses = _counter_value(CACHE_MISSES)

    assert after_misses > before_misses
    assert after_hits > before_hits
