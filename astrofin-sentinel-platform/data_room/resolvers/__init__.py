"""
data_room/resolvers/__init__.py
================================
Concrete resolvers. Each one wraps a single external data source.

  coingecko.py     - CoinGecko API → PriceTick
  price_resolver.py - CoinGecko + Binance → unified PriceTick
  feargreed.py     - Fear & Greed Index → FearGreedTick
  yahoo.py         - Yahoo Finance (VIX, DXY) → PriceTick

All resolvers expose a coroutine `async def resolve(symbol, asof) -> T`.
"""

from __future__ import annotations

from data_room.resolvers.base import Resolver, ResolverError  # noqa: F401
from data_room.resolvers.coingecko import CoinGeckoResolver as CoinGecko
from data_room.resolvers.feargreed import FearGreedResolver as FearGreed
from data_room.resolvers.yahoo import YahooResolver as Yahoo

__all__ = ["Resolver", "ResolverError", "CoinGecko", "FearGreed", "Yahoo", "RESOLVER_REGISTRY"]
RESOLVER_REGISTRY = [CoinGecko(), FearGreed(), Yahoo()]
