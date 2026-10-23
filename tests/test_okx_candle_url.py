"""Verify OKX v5 candle URLs use instId/bar (not symbol/interval)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from agents._impl.bear_researcher import BearResearcherAgent
from core.http_client import normalize_okx_inst_id


class _Resp:
    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return {"data": []}


class _CapturingClient:
    """Stands in for httpx.AsyncClient and records the URL actually requested."""

    def __init__(self) -> None:
        self.urls: list[str] = []

    async def __aenter__(self) -> "_CapturingClient":
        return self

    async def __aexit__(self, *exc) -> None:
        return None

    async def get(self, url: str, **kw) -> _Resp:
        self.urls.append(url)
        return _Resp()


@pytest.mark.asyncio
async def test_bear_researcher_builds_instid_bar_url():
    client = _CapturingClient()
    with patch("httpx.AsyncClient", return_value=client):
        await BearResearcherAgent()._fetch_ohlcv("BTCUSDT", "1d", 60)

    assert len(client.urls) == 1, "expected exactly one OKX candles request"
    assert client.urls[0] == (
        "https://www.okx.com/api/v5/market/candles?instId=BTC-USDT&bar=1d&limit=60"
    )


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
