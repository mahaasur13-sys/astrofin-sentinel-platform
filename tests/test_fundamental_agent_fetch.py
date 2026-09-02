"""FundamentalAgent CoinGecko fetch: no_data abstain + TTL cache (no network)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents._impl.fundamental_agent import _CACHE, FundamentalAgent
from core.base_agent import SignalDirection


@pytest.fixture(autouse=True)
def _clear_cache():
    _CACHE.clear()
    yield
    _CACHE.clear()


@pytest.mark.asyncio
async def test_empty_fetch_returns_no_data():
    agent = FundamentalAgent()
    with patch.object(agent, "_fetch_fundamental_data", new=AsyncMock(return_value={"no_data": True})):
        result = await agent.analyze({"symbol": "BTCUSDT", "current_price": 50000})
    assert result.signal == SignalDirection.NEUTRAL
    assert result.metadata.get("no_data") is True


@pytest.mark.asyncio
async def test_repeat_fetch_within_ttl_hits_client_once():
    agent = FundamentalAgent()

    resp = MagicMock()
    resp.status = 200
    resp.json = AsyncMock(return_value={"prices": [[1, 100.0], [2, 110.0], [3, 105.0]]})
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)

    session = MagicMock()
    session.get = MagicMock(return_value=resp)
    agent._session = session

    data1 = await agent._fetch_fundamental_data("BTCUSDT")
    data2 = await agent._fetch_fundamental_data("BTCUSDT")

    assert data1 == data2
    assert data1.get("mvrv_ratio") is not None
    assert session.get.call_count == 1  # second call served from TTL cache
