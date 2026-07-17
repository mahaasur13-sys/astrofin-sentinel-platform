"""
data_room/resolvers/feargreed.py
=================================
Alternative.me Fear & Greed Index resolver.
"""
from __future__ import annotations

from dataclasses import dataclass

import asyncio
import logging
from typing import Any

import aiohttp

from data_room.resolvers.base import Resolver, ResolverError

logger = logging.getLogger("data_room.feargreed")

API_URL = "https://api.alternative.me/fng/?limit=2"


@dataclass
class FearGreedTick:
    value: int
    classification: str
    timestamp: str

    @property
    def is_extreme_fear(self) -> bool:
        return self.value <= 25

    @property
    def is_extreme_greed(self) -> bool:
        return self.value >= 75


class FearGreedResolver(Resolver[FearGreedTick]):
    name = "feargreed"
    freshness_sla_seconds = 3600  # hourly is fine

    def __init__(self, api_url: str = API_URL):
        self._url = api_url
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
                headers={"Accept": "application/json"},
            )
        return self._session

    async def resolve(self, *args: Any, **kwargs: Any) -> FearGreedTick:
        session = await self._get_session()
        try:
            async with session.get(self._url) as resp:
                if resp.status != 200:
                    raise ResolverError(f"FearGreed HTTP {resp.status}")
                data = await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise ResolverError(f"FearGreed: {e}") from e

        try:
            entry = data["data"][0]
        except (KeyError, IndexError) as e:
            raise ResolverError(f"FearGreed: unexpected response format: {e}") from e

        return FearGreedTick(
            value=int(entry["value"]),
            classification=entry.get("value_classification", ""),
            timestamp=entry.get("timestamp", ""),
        )

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()


__all__ = ["FearGreedResolver", "FearGreedTick"]
