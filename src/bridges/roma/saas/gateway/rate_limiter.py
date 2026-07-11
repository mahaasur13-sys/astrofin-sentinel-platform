"""Rate limiting — Token Bucket + SlowAPI + Redis backend."""
import time
import asyncio
from typing import Optional
from fastapi import Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
import os

_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import redis
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.from_url(url, decode_responses=True)
        _redis_client.ping()
    except Exception:  # noqa: BLE001
        _redis_client = None
    return _redis_client


class TokenBucket:
    """In-memory token bucket for single-instance rate limiting."""

    def __init__(self, rate: float, burst: int):
        self.rate = rate  # tokens per second
        self.burst = burst
        self.tokens = float(burst)
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_update = now
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False


class RedisTokenBucket:
    """Redis-backed token bucket for distributed rate limiting."""

    def __init__(self, key: str, rate: float, burst: int, redis_client):
        self.key = f"ratelimit:{key}"
        self.rate = rate
        self.burst = burst
        self.redis = redis_client

    async def consume(self, tokens: int = 1) -> bool:
        try:
            pipe = self.redis.pipeline()
            now = time.time()
            pipe.incr(self.key)
            pipe.expire(self.key, 60)
            results = pipe.execute()
            current = results[0]
            window = current * 60.0 / self.burst
            retry_after = max(0, window - (now - self.redis.get(f"{self.key}:reset") or now))
            allowed = current <= self.burst
            if allowed:
                self.redis.setex(f"{self.key}:reset", 60, str(now))
            return allowed
        except Exception:  # noqa: BLE001
            return True


def _tenant_key(request: Request) -> str:
    tenant = getattr(request.state, "tenant_id", None)
    if tenant:
        return f"tenant:{tenant}"
    return get_remote_address(request)


def create_limiter(redis_url: Optional[str] = None) -> Limiter:
    limiter = Limiter(key_func=_tenant_key, default_limits=["60/minute"])
    return limiter


_default_limiter: Optional[Limiter] = None
_buckets: dict[str, TokenBucket] = {}
_bucket_lock = asyncio.Lock()


async def check_rate_limit(
    request: Request,
    requests_per_minute: int = 60,
    burst_size: int = 10,
    use_redis: bool = False,
) -> None:
    tenant_id = getattr(request.state, "tenant_id", None)
    key = f"bucket:{tenant_id or get_remote_address(request)}"
    redis = _get_redis() if use_redis else None

    if redis:
        bucket = RedisTokenBucket(key, requests_per_minute / 60.0, burst_size, redis)
        allowed = await bucket.consume()
    else:
        async with _bucket_lock:
            if key not in _buckets:
                _buckets[key] = TokenBucket(requests_per_minute / 60.0, burst_size)
            bucket = _buckets[key]
        allowed = await bucket.consume()

    if not allowed:
        raise HTTPException(
            429,
            detail="Rate limit exceeded",
            headers={"Retry-After": "60"},
        )


def rate_limit_dependency(
    requests_per_minute: int = 60,
    burst_size: int = 10,
    use_redis: bool = False,
):
    async def dep(request: Request):
        await check_rate_limit(request, requests_per_minute, burst_size, use_redis)
    return dep
