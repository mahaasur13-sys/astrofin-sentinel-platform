from __future__ import annotations

import asyncio

import pytest

from core.cache import RedisCache


@pytest.fixture
async def cache():
    """Создаём экземпляр кэша (in‑memory, Redis не нужен)."""
    c = RedisCache(use_redis=False)  # fallback‑режим для тестов
    await c.clear()
    return c


@pytest.mark.asyncio
async def test_set_and_get(cache):
    await cache.set("foo", "bar")
    assert await cache.get("foo") == "bar"


@pytest.mark.asyncio
async def test_get_missing_key(cache):
    assert await cache.get("missing") is None


@pytest.mark.asyncio
async def test_delete(cache):
    await cache.set("temp", 123)
    await cache.delete("temp")
    assert await cache.get("temp") is None


@pytest.mark.asyncio
async def test_ttl_expiry(cache):
    await cache.set("short", "value", ttl=1)  # 1 секунда
    await asyncio.sleep(1.1)
    assert await cache.get("short") is None
