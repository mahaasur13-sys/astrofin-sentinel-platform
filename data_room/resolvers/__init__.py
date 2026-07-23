"""
data_room/resolvers/__init__.py
================================
Concrete resolvers. Each one wraps a single external data source.

  price_resolver.py        - CoinGecko + Binance → unified PriceTick
  macro_resolver.py        - Yahoo + Fed
  ephemeris_resolver.py    - Swiss Ephemeris + JPL fallback
  fundamentals_resolver.py - SEC EDGAR + CoinGecko

All resolvers expose a coroutine `async def resolve(symbol, asof) -> T`.
"""

from __future__ import annotations

from data_room.resolvers.base import Resolver, ResolverError  # noqa: F401

__all__ = ["Resolver", "ResolverError"]
