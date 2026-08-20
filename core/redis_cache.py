from __future__ import annotations

import logging
log = logging.getLogger(__name__)

import time

import redis.asyncio as aioredis

from tools.metrics_server import CACHE_HITS, CACHE_MISSES


class RedisCache:
    """Async cache with Redis backend and in‑memory fallback."""

    def __init__(self, redis_url="redis://redis:6379", use_redis=True):
        self.redis = aioredis.Redis.from_url(redis_url) if use_redis else None
        self.fallback = {}  # in‑memory dict на случай недоступности Redis
        self._fallback_ttl = {}  # временные метки для fallback

    async def get(self, key: str):
        """Получить значение по ключу."""
        if self.redis:
            try:
                val = await self.redis.get(key)
                if val:
                    CACHE_HITS.inc()
                    return val.decode() if isinstance(val, bytes) else val
                else:
                    CACHE_MISSES.inc()
                    return None
            except Exception:
                log.warning("Cache fallback — operation failed", exc_info=True)
        # In‑memory fallback
        if key in self.fallback:
            if self._fallback_ttl.get(key, 0) > time.time():
                CACHE_HITS.inc()
                return self.fallback[key]
            else:
                await self.delete(key)  # удаляем просроченный
        CACHE_MISSES.inc()
        return None

    async def set(self, key: str, value, ttl=300):
        """Сохранить значение с TTL (секунд)."""
        if self.redis:
            try:
                await self.redis.setex(key, ttl, str(value))
                return
            except Exception:
                log.warning("Cache access failed", exc_info=True)
        # fallback
        self.fallback[key] = value
        self._fallback_ttl[key] = time.time() + ttl

    async def delete(self, key: str):
        """Удалить ключ."""
        if self.redis:
            try:
                await self.redis.delete(key)
            except Exception:
                log.warning("Cache access failed", exc_info=True)
        self.fallback.pop(key, None)
        self._fallback_ttl.pop(key, None)

    async def clear(self):
        """Очистить весь кэш (только fallback)."""
        if self.redis:
            try:
                await self.redis.flushdb()
            except Exception:
                log.warning("Cache access failed", exc_info=True)
        self.fallback.clear()
        self._fallback_ttl.clear()
