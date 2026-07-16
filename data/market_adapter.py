"""data/market_adapter.py — ATOM-STEP-6: Market Data Adapter with live sources, cache, and metrics."""

import logging
import os
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import requests
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

# ── Prometheus metrics ──────────────────────────────────────────────────────────
MARKET_DATA_CACHE_HITS = Counter("astrofin_market_data_cache_hits", "Number of market data cache hits")
MARKET_DATA_CACHE_MISSES = Counter("astrofin_market_data_cache_misses", "Number of market data cache misses")
MARKET_DATA_API_LATENCY = Histogram(
    "astrofin_market_data_api_latency_seconds",
    "Market data API request duration in seconds",
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# ── Configuration ───────────────────────────────────────────────────────────────
MARKET_DATA_SOURCE = os.getenv("MARKET_DATA_SOURCE", "synthetic").lower()
BINANCE_API_BASE = os.getenv("BINANCE_API_BASE", "https://api.binance.com")
COINGECKO_API_BASE = os.getenv("COINGECKO_API_BASE", "https://api.coingecko.com/api/v3")
CACHE_TTL_MAP = {"1m": 60, "5m": 120, "15m": 300, "1h": 900, "4h": 3600, "1d": 86400}


@dataclass
class OHLCV:
    """Open, High, Low, Close, Volume candle."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketAdapter:
    """Multi-source market data adapter with fallback chain and caching."""

    def __init__(self, source: str = None):
        self.source = source or MARKET_DATA_SOURCE
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})
        # Synchronous Redis cache (separate from async core.cache)
        self._redis = None
        try:
            import redis

            _redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
            self._redis = redis.Redis.from_url(_redis_url, decode_responses=True)
            self._redis.ping()
            logger.info("Redis connected for market data cache")
        except Exception as e:
            logger.warning("Redis unavailable, caching disabled: %s", e)
            self._redis = None

    # ── Public API ──────────────────────────────────────────────────────────────

    def fetch_ohlcv(self, symbol: str, interval: str = "1h", limit: int = 100) -> list[OHLCV]:
        """
        Fetch OHLCV candles for a symbol.

        Args:
            symbol: Trading pair (e.g. 'BTCUSDT')
            interval: Candle interval ('1m', '5m', '15m', '1h', '4h', '1d')
            limit: Number of candles to return

        Returns:
            List of OHLCV objects.
        """
        cache_key = f"ohlcv:{symbol}:{interval}:{limit}"

        # Check cache first
        if self._cache:
            cached = self._cache.get(cache_key)
            if cached:
                MARKET_DATA_CACHE_HITS.inc()
                logger.debug("Cache hit for %s", cache_key)
                return [OHLCV(**c) for c in cached]

        MARKET_DATA_CACHE_MISSES.inc()

        # Fetch from source chain
        chain = self._build_source_chain()
        for src in chain:
            try:
                data = self._fetch_from_source(src, symbol, interval, limit)
                if data:
                    # Cache the result
                    if self._cache:
                        ttl = CACHE_TTL_MAP.get(interval, 3600)
                        self._cache.setex(
                            cache_key,
                            ttl,
                            [
                                {
                                    "timestamp": d.timestamp.isoformat(),
                                    "open": d.open,
                                    "high": d.high,
                                    "low": d.low,
                                    "close": d.close,
                                    "volume": d.volume,
                                }
                                for d in data
                            ],
                        )
                    return data
            except Exception as e:
                logger.warning("Source %s failed for %s: %s", src, symbol, e)
                continue

        # Ultimate fallback: synthetic data
        logger.error("All sources failed, returning synthetic data for %s", symbol)
        return self._generate_synthetic(symbol, interval, limit)

    def get_latest_price(self, symbol: str) -> float:
        """Get the latest closing price for a symbol."""
        data = self.fetch_ohlcv(symbol, limit=1)
        return data[0].close if data else 0.0

    # ── Private methods ──────────────────────────────────────────────────────────

    def _build_source_chain(self) -> list[str]:
        """Build ordered list of sources based on configured source."""
        if self.source == "synthetic":
            return ["synthetic"]
        elif self.source == "binance":
            return ["binance", "coingecko", "synthetic"]
        elif self.source == "coingecko":
            return ["coingecko", "synthetic"]
        return [self.source, "synthetic"]

    def _fetch_from_source(self, source: str, symbol: str, interval: str, limit: int) -> list[OHLCV]:
        """Dispatch to correct fetcher."""
        if source == "synthetic":
            return self._generate_synthetic(symbol, interval, limit)
        elif source == "binance":
            return self._fetch_binance(symbol, interval, limit)
        elif source == "coingecko":
            return self._fetch_coingecko(symbol, interval, limit)
        return []

    def _fetch_binance(self, symbol: str, interval: str, limit: int) -> list[OHLCV]:
        """Fetch candles from Binance public API."""
        url = f"{BINANCE_API_BASE}/api/v3/klines"
        params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}

        start = time.monotonic()
        try:
            resp = self._session.get(url, params=params, timeout=10)
            MARKET_DATA_API_LATENCY.observe(time.monotonic() - start)
            resp.raise_for_status()
            klines = resp.json()
            return [
                OHLCV(
                    timestamp=datetime.fromtimestamp(k[0] / 1000),
                    open=float(k[1]),
                    high=float(k[2]),
                    low=float(k[3]),
                    close=float(k[4]),
                    volume=float(k[5]),
                )
                for k in klines
            ]
        except Exception as e:
            MARKET_DATA_API_LATENCY.observe(time.monotonic() - start)
            logger.error("Binance API error: %s", e)
            raise

    def _fetch_coingecko(self, symbol: str, interval: str, limit: int) -> list[OHLCV]:
        """Fetch candles from CoinGecko public API."""
        # CoinGecko uses coingecko-specific IDs; for simplicity we hardcode BTC/USDT mapping
        coin_map = {"BTCUSDT": "bitcoin", "ETHUSDT": "ethereum"}
        coin_id = coin_map.get(symbol.upper(), "bitcoin")
        vs_currency = "usd"
        days_map = {"1h": "1", "4h": "7", "1d": "30"}
        days = days_map.get(interval, "1")

        url = f"{COINGECKO_API_BASE}/coins/{coin_id}/ohlc"
        params = {"vs_currency": vs_currency, "days": days}

        start = time.monotonic()
        try:
            resp = self._session.get(url, params=params, timeout=15)
            MARKET_DATA_API_LATENCY.observe(time.monotonic() - start)
            resp.raise_for_status()
            klines = resp.json()
            # CoinGecko returns [timestamp, open, high, low, close]
            return [
                OHLCV(
                    timestamp=datetime.fromtimestamp(k[0] / 1000),
                    open=float(k[1]),
                    high=float(k[2]),
                    low=float(k[3]),
                    close=float(k[4]),
                    volume=0.0,  # CoinGecko free tier doesn't provide volume
                )
                for k in klines[-limit:]
            ]
        except Exception as e:
            MARKET_DATA_API_LATENCY.observe(time.monotonic() - start)
            logger.error("CoinGecko API error: %s", e)
            raise

    def _generate_synthetic(self, symbol: str, interval: str, limit: int) -> list[OHLCV]:
        """Generate synthetic OHLCV data (original mock implementation)."""
        data = []
        now = datetime.now(timezone.utc)
        price = 100.0
        for i in range(limit):
            ts = now - timedelta(hours=limit - i - 1) if interval == "1h" else now - timedelta(days=limit - i - 1)
            change = random.gauss(0, 0.02)
            o, c = price, price * (1 + change)
            h, l = (
                max(o, c) * (1 + abs(change) * 0.5),
                min(o, c) * (1 - abs(change) * 0.5),
            )
            data.append(
                OHLCV(
                    timestamp=ts,
                    open=round(o, 4),
                    high=round(h, 4),
                    low=round(l, 4),
                    close=round(c, 4),
                    volume=random.uniform(1000, 10000),
                )
            )
            price = c
        return data
