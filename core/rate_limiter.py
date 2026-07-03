"""In-memory IP-based rate limiter (P1-05).

Sliding-window counter using :class:`cachetools.TTLCache`. For multi-process
deployments swap in Redis; for now we keep it simple and process-local.

Usage::

    from fastapi import APIRouter, Depends
    from core.rate_limiter import rate_limit_dependency

    router = APIRouter()

    @router.post("/login", dependencies=[Depends(rate_limit_dependency(5, 60))])
    def login(...): ...
"""
from __future__ import annotations

import time
from typing import Dict, List, Tuple

from cachetools import TTLCache
from fastapi import HTTPException, Request, status


class RateLimiter:
    """Sliding-window rate limiter keyed by ``(client_ip, path)``."""

    def __init__(self, max_requests: int, window_seconds: int, max_keys: int = 10_000) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # TTL slightly longer than the window so the whole entry ages out cleanly.
        self._cache: TTLCache = TTLCache(maxsize=max_keys, ttl=window_seconds + 1)
        self._lock = None  # placeholder for future asyncio.Lock

    def _key(self, request: Request) -> str:
        client = request.client
        ip = client.host if client else "unknown"
        return f"{ip}:{request.url.path}"

    async def __call__(self, request: Request) -> None:
        key = self._key(request)
        now = time.monotonic()
        cutoff = now - self.window_seconds
        timestamps: List[float] = self._cache.get(key, [])
        fresh = [t for t in timestamps if t > cutoff]
        if len(fresh) >= self.max_requests:
            self._cache[key] = fresh  # refresh TTL; do not consume a slot
            retry_after = max(1, int(self.window_seconds - (now - fresh[0])))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests",
                headers={"Retry-After": str(retry_after)},
            )
        fresh.append(now)
        self._cache[key] = fresh

    def reset(self) -> None:
        self._cache.clear()

    def snapshot(self) -> Dict[str, Tuple[int, float]]:
        """Diagnostic: return {key: (count, oldest_timestamp)}."""
        out: Dict[str, Tuple[int, float]] = {}
        now = time.monotonic()
        cutoff = now - self.window_seconds
        for k, ts_list in self._cache.items():
            fresh = [t for t in ts_list if t > cutoff]
            if fresh:
                out[k] = (len(fresh), fresh[0])
        return out


def rate_limit_dependency(max_requests: int, window_seconds: int):
    """FastAPI dependency factory — usage::

        from core.rate_limiter import rate_limit_dependency

        @router.post("/login")
        def login(body: LoginIn, _lim=Depends(rate_limit_dependency(5, 60))):
            ...

    The returned callable is a plain function (not a class), which is
    critical for FastAPI 0.115+ to inject :class:`fastapi.Request` correctly.
    Earlier the factory returned a :class:`RateLimiter` instance; FastAPI did
    not resolve the ``request: Request`` annotation on the instance's
    ``__call__``, which surfaced as ``422 Unprocessable Entity`` with
    ``loc=['query', 'request']``.
    """
    limiter = RateLimiter(max_requests=max_requests, window_seconds=window_seconds)

    async def _dep(request: Request) -> None:
        # Delegate to the underlying RateLimiter.
        await limiter(request)

    return _dep
