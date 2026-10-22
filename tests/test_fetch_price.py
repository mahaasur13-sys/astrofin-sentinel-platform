from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from data_room.blueprint import PriceTick
from orchestration.sentinel_v5 import _fetch_price


@pytest.mark.asyncio
async def test_fetch_price_uses_async_http():
    """_fetch_price goes through the async Data Room resolver (R-01), not bare httpx."""
    tick = PriceTick(symbol="BTCUSDT", price=100.0, source_id="test")
    with (
        patch(
            "data_room.resolvers.coingecko.CoinGeckoResolver.resolve",
            new=AsyncMock(return_value=tick),
        ) as mock_resolve,
        patch(
            "data_room.resolvers.coingecko.CoinGeckoResolver.close",
            new=AsyncMock(),
        ) as mock_close,
    ):
        price = await _fetch_price("BTCUSDT")
        mock_resolve.assert_awaited_once()
        mock_close.assert_awaited_once()
        assert price == 100.0
