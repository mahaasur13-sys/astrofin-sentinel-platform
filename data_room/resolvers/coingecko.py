"""
data_room/resolvers/coingecko.py
=================================
CoinGecko resolver — crypto prices, metadata, market data.

Free tier: 30 req/min. Rate-limit aware with exponential backoff.
"""
from __future__ import annotations

from dataclasses import dataclass

import asyncio
import logging
import time
from typing import Any

import aiohttp

from data_room.resolvers.base import Resolver, ResolverError
from data_room.blueprint import PriceTick

logger = logging.getLogger("data_room.coingecko")

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# Map internal symbols to CoinGecko IDs
SYMBOL_TO_ID: dict[str, str] = {
    "BTCUSDT": "bitcoin",
    "BTC": "bitcoin",
    "ETHUSDT": "ethereum",
    "ETH": "ethereum",
    "SOLUSDT": "solana",
    "SOL": "solana",
    "BNBUSDT": "binancecoin",
    "BNB": "binancecoin",
    "ADAUSDT": "cardano",
    "XRPUSDT": "ripple",
    "DOGEUSDT": "dogecoin",
    "DOTUSDT": "polkadot",
    "AVAXUSDT": "avalanche-2",
    "MATICUSDT": "matic-network",
}


class CoinGeckoResolver(Resolver[PriceTick]):
    name = "coingecko"
    freshness_sla_seconds = 30

    def __init__(self, base_url: str = COINGECKO_BASE):
        self._base = base_url
        self._session: aiohttp.ClientSession | None = None
        self._last_request = 0.0
        self._min_interval = 2.0  # 30 req/min ≈ 2s between requests

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
                headers={"Accept": "application/json"},
            )
        return self._session

    async def _rate_limit(self):
        elapsed = time.monotonic() - self._last_request
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)
        self._last_request = time.monotonic()

    async def resolve(self, symbol: str, asof: str | None = None, **_: Any) -> PriceTick:
        coingecko_id = SYMBOL_TO_ID.get(symbol.upper(), symbol.lower())
        url = f"{self._base}/simple/price?ids={coingecko_id}&vs_currencies=usd&include_24hr_change=true"

        for attempt in range(3):
            try:
                await self._rate_limit()
                session = await self._get_session()
                async with session.get(url) as resp:
                    if resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", 5))
                        logger.warning("CoinGecko rate limited, waiting %ds", retry_after)
                        await asyncio.sleep(retry_after)
                        continue
                    if resp.status != 200:
                        raise ResolverError(f"CoinGecko HTTP {resp.status}")
                    data = await resp.json()

                coin_data = data.get(coingecko_id, {})
                price = coin_data.get("usd")
                if price is None:
                    raise ResolverError(f"CoinGecko: no USD price for {coingecko_id}")

                return PriceTick(
                    symbol=symbol,
                    price=float(price),
                    asof=asof or "",
                    source_id="coingecko",
                    quality_score=0.95,
                    freshness_sla_seconds=self.freshness_sla_seconds,
                )

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning("CoinGecko attempt %d failed: %s", attempt + 1, e)
                if attempt == 2:
                    raise ResolverError(f"CoinGecko: {e}") from e
                await asyncio.sleep(2 ** attempt)

        raise ResolverError("CoinGecko: all retries exhausted")

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()


__all__ = ["CoinGeckoResolver", "SYMBOL_TO_ID"]
