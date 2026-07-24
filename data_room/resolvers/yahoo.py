"""
data_room/resolvers/yahoo.py
=============================
Yahoo Finance resolver — VIX, DXY, macro indicators.
Uses yfinance (synchronous, wrapped in async via executor).
"""
from __future__ import annotations

from dataclasses import dataclass

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from data_room.resolvers.base import Resolver, ResolverError

logger = logging.getLogger("data_room.yahoo")

MACRO_SYMBOLS: dict[str, str] = {
    "VIX": "^VIX",
    "DXY": "DX-Y.NYB",
    "SPX": "^GSPC",
    "NASDAQ": "^IXIC",
    "GOLD": "GC=F",
    "OIL": "CL=F",
    "US10Y": "^TNX",
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
}

EXECUTOR = ThreadPoolExecutor(max_workers=3, thread_name_prefix="yfinance")


@dataclass
class YahooTick:
    symbol: str
    price: float
    change_pct: float
    volume: float
    asof: str
    source_id: str = "yahoo"


class YahooResolver(Resolver[YahooTick]):
    name = "yahoo"
    freshness_sla_seconds = 300  # 5 min

    def __init__(self):
        pass

    async def resolve(
        self, symbol: str, asof: str | None = None, **_: Any
    ) -> YahooTick:
        yahoo_symbol = MACRO_SYMBOLS.get(symbol.upper(), symbol)
        loop = asyncio.get_running_loop()

        try:
            ticker = await loop.run_in_executor(EXECUTOR, self._fetch, yahoo_symbol)
        except Exception as e:
            raise ResolverError(f"Yahoo: {e}") from e

        return YahooTick(
            symbol=symbol,
            price=ticker["price"],
            change_pct=ticker["change_pct"],
            volume=ticker["volume"],
            asof=asof or "",
        )

    @staticmethod
    def _fetch(yahoo_symbol: str) -> dict[str, float]:
        import yfinance as yf

        t = yf.Ticker(yahoo_symbol)
        info = t.info or {}
        fast_info = t.fast_info if hasattr(t, "fast_info") else {}

        price = info.get("regularMarketPrice") or fast_info.get("lastPrice") or 0.0
        prev_close = info.get("regularMarketPreviousClose") or fast_info.get("previousClose") or price
        change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0.0
        volume = info.get("regularMarketVolume") or fast_info.get("lastVolume") or 0.0

        return {"price": float(price), "change_pct": float(change_pct), "volume": float(volume)}


__all__ = ["YahooResolver", "YahooTick", "MACRO_SYMBOLS"]
