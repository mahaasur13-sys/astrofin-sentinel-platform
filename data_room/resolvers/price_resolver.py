"""
data_room/resolvers/price_resolver.py
=====================================
Reference implementation: a price resolver that chains CoinGecko → Binance.

    CoinGecko  ── fail ──►  Binance  ── fail ──►  ResolverError

The Resolver will be picked up by the Data Room via the resolver
registry (data_room/blueprint.py:RESOLVERS).
"""

from __future__ import annotations

import logging
from typing import Any

from data_room.blueprint import PriceTick
from data_room.resolvers.base import Resolver, ResolverError

logger = logging.getLogger("data_room.price")


class CoinGeckoPriceResolver(Resolver[PriceTick]):
    name = "coingecko"

    async def resolve(self, symbol: str, asof: str | None = None, **_: Any) -> PriceTick:
        # In production: aiohttp + rate-limit aware client.
        # Here: stub. The shape of the call is what matters.
        raise ResolverError("coingecko not implemented in this stub")


class BinancePriceResolver(Resolver[PriceTick]):
    name = "binance"

    async def resolve(self, symbol: str, asof: str | None = None, **_: Any) -> PriceTick:
        # Same comment as above. The point is: this is the *contract*.
        raise ResolverError("binance not implemented in this stub")


# Module-level registry of price resolvers in priority order.
PRICE_RESOLVERS: list[Resolver[PriceTick]] = [
    CoinGeckoPriceResolver(),
    BinancePriceResolver(),
]


__all__ = ["PRICE_RESOLVERS", "CoinGeckoPriceResolver", "BinancePriceResolver"]
