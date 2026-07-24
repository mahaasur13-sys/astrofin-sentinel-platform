"""
tests/data_room/test_resolvers.py
===================================
Smoke / integration tests for Data Room resolvers.

Marked `integration` because they hit live APIs.
Run with: pytest -m integration tests/data_room/
"""
from __future__ import annotations

import pytest

from data_room.resolvers.coingecko import CoinGeckoResolver, SYMBOL_TO_ID
from data_room.resolvers.feargreed import FearGreedResolver, FearGreedTick
from data_room.resolvers.yahoo import YahooResolver, YahooTick, MACRO_SYMBOLS
from data_room.resolvers.base import Resolver, ResolverError
from data_room.blueprint import PriceTick


pytestmark = pytest.mark.integration


class TestCoinGeckoResolver:
    @pytest.mark.asyncio
    async def test_resolve_btc_returns_price(self):
        r = CoinGeckoResolver()
        tick = await r.resolve("BTCUSDT")
        assert isinstance(tick, PriceTick)
        assert tick.price > 0
        assert tick.source_id == "coingecko"
        assert tick.quality_score == 0.95

    @pytest.mark.asyncio
    async def test_resolve_eth(self):
        r = CoinGeckoResolver()
        tick = await r.resolve("ETHUSDT")
        assert tick.price > 0

    @pytest.mark.asyncio
    async def test_resolve_unknown_symbol_raises(self):
        r = CoinGeckoResolver()
        with pytest.raises(ResolverError):
            await r.resolve("NONEXISTENTCOIN123456")

    def test_symbol_mapping_coverage(self):
        assert SYMBOL_TO_ID["BTCUSDT"] == "bitcoin"
        assert SYMBOL_TO_ID["ETH"] == "ethereum"
        assert len(SYMBOL_TO_ID) >= 10


class TestFearGreedResolver:
    @pytest.mark.asyncio
    async def test_resolve_returns_valid_range(self):
        r = FearGreedResolver()
        tick = await r.resolve()
        assert isinstance(tick, FearGreedTick)
        assert 0 <= tick.value <= 100
        assert tick.classification
        assert tick.timestamp

    @pytest.mark.asyncio
    async def test_extreme_fear_property(self):
        r = FearGreedResolver()
        tick = await r.resolve()
        is_extreme = tick.value <= 25
        assert tick.is_extreme_fear == is_extreme

    @pytest.mark.asyncio
    async def test_extreme_greed_property(self):
        r = FearGreedResolver()
        tick = await r.resolve()
        is_extreme = tick.value >= 75
        assert tick.is_extreme_greed == is_extreme


class TestYahooResolver:
    @pytest.mark.asyncio
    async def test_resolve_vix(self):
        r = YahooResolver()
        tick = await r.resolve("VIX")
        assert isinstance(tick, YahooTick)
        assert tick.price > 0
        assert tick.symbol == "VIX"

    @pytest.mark.asyncio
    async def test_resolve_dxy(self):
        r = YahooResolver()
        tick = await r.resolve("DXY")
        assert tick.price > 0

    @pytest.mark.asyncio
    async def test_resolve_spx(self):
        r = YahooResolver()
        tick = await r.resolve("SPX")
        assert tick.price > 0

    @pytest.mark.asyncio
    async def test_resolve_gold(self):
        r = YahooResolver()
        tick = await r.resolve("GOLD")
        assert tick.price > 0

    def test_macro_symbols_coverage(self):
        assert MACRO_SYMBOLS["VIX"] == "^VIX"
        assert MACRO_SYMBOLS["DXY"] == "DX-Y.NYB"
        assert len(MACRO_SYMBOLS) >= 6


class TestResolverContracts:
    """Verify base contracts are importable and usable."""

    def test_resolver_base_class(self):
        assert issubclass(CoinGeckoResolver, Resolver)
        assert issubclass(FearGreedResolver, Resolver)
        assert issubclass(YahooResolver, Resolver)

    def test_resolver_error_is_exception(self):
        err = ResolverError("test")
        assert isinstance(err, Exception)
        assert str(err) == "test"


__all__ = [
    "TestCoinGeckoResolver",
    "TestFearGreedResolver",
    "TestYahooResolver",
    "TestResolverContracts",
]
