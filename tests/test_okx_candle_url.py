"""Verify OKX v5 candle URLs use instId/bar (not symbol/interval)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from agents._impl.bear_researcher import BearResearcherAgent
from core.http_client import normalize_okx_inst_id


@pytest.mark.asyncio
async def test_bear_researcher_builds_instid_bar_url():
    captured: dict[str, str] = {}

    async def _capture(client, url: str, **kw) -> dict:
        captured["url"] = url
        return {"data": []}

    agent = BearResearcherAgent()
    with (
        patch("agents._impl.bear_researcher.okx_get_json", new=_capture),
        patch("httpx.AsyncClient") as _client_cls,
    ):
        _client_cls.return_value = AsyncMock()
        await agent._fetch_ohlcv("BTC", "1d", 60)

    assert captured["url"] == ("https://www.okx.com/api/v5/market/candles?instId=BTC-USDT&bar=1D&limit=60")


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("BTC", "BTC-USDT"),
        ("btc", "BTC-USDT"),
        ("BTCUSDT", "BTC-USDT"),
        ("BTC-USDT", "BTC-USDT"),
        ("ethusdt", "ETH-USDT"),
        ("ETHUSDT", "ETH-USDT"),
    ],
)
def test_normalize_okx_inst_id(raw: str, expected: str) -> None:
    assert normalize_okx_inst_id(raw) == expected
