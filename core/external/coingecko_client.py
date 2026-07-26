"""CoinGecko client with circuit breaker + Redis cache fallback."""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx

from core.external.circuit_breaker import CircuitBreaker

_coingecko_cb = CircuitBreaker("coingecko", fail_max=5, timeout_seconds=60.0)

# Redis cache fallback path (file-based when Redis unavailable)
_CACHE_DIR = Path(os.getenv("ASTROFIN_CACHE_DIR", os.path.expanduser("~/.cache/astrofin")))  # nosec B108 — XDG cache, not /tmp
_CACHE_DIR.mkdir(parents=True, exist_ok=True)  # nosec B108


def _file_cache_key(prefix: str, key: str) -> Path:
    return _CACHE_DIR / f"{prefix}_{key.replace('/', '_')}.json"


def _read_cache(prefix: str, key: str, max_age_s: int = 300) -> dict | None:
    cache_path = _file_cache_key(prefix, key)
    if not cache_path.exists():
        return None
    import time
    if time.time() - cache_path.stat().st_mtime > max_age_s:
        return None
    try:
        return json.loads(cache_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _write_cache(prefix: str, key: str, data: dict) -> None:
    cache_path = _file_cache_key(prefix, key)
    try:
        cache_path.write_text(json.dumps(data))
    except OSError:
        pass


async def get_price(symbol: str = "bitcoin", vs_currency: str = "usd", days: int = 90) -> dict | None:
    """Fetch CoinGecko market chart with circuit breaker + file cache fallback."""
    cache_key = f"{symbol.lower()}/{vs_currency}/{days}"
    cached = _read_cache("cg_price", cache_key, max_age_s=120)
    if cached:
        return cached

    if _coingecko_cb.is_open:
        cached = _read_cache("cg_price", cache_key, max_age_s=3600)
        if cached:
            return cached
        return None

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart"
            r = await client.get(url, params={"vs_currency": vs_currency, "days": days})
            if r.status_code == 200:
                data = r.json()
                _write_cache("cg_price", cache_key, data)
                _coingecko_cb.success()
                return data
            elif r.status_code == 429:
                _coingecko_cb.failure()
                cached = _read_cache("cg_price", cache_key, max_age_s=3600)
                return cached
            else:
                _coingecko_cb.failure()
                cached = _read_cache("cg_price", cache_key, max_age_s=3600)
                return cached
    except Exception:
        _coingecko_cb.failure()
        return _read_cache("cg_price", cache_key, max_age_s=3600)


def get_circuit_breaker() -> CircuitBreaker:
    """Expose the CoinGecko circuit breaker for metrics."""
    return _coingecko_cb
