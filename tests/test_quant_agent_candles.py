"""QuantAgent must parse the OKX envelope, order candles oldest-first and
fail closed (NEUTRAL/no_data) on stale/missing candles or price."""

from __future__ import annotations

from unittest.mock import patch

import pytest

import agents._impl.ephemeris_decorator as eph
from agents._impl import quant_agent as qa
from core import market_freshness as mf
from core.base_agent import SignalDirection

NOW = 1_800_000_000.0
DAY = 86400


def _rows(n: int, newest_age_s: float, trend: float = 1.0) -> list:
    """OKX rows newest first: [ts_ms, o, h, l, c, vol, ...]."""
    rows = []
    for i in range(n):  # i=0 newest
        ts = NOW - newest_age_s - i * DAY
        close = 100.0 + trend * (n - i)
        rows.append([str(int(ts * 1000)), str(close), str(close + 1), str(close - 1), str(close), "10", "0", "0", "1"])
    return rows


class _Resp:
    def __init__(self, payload):
        self._p = payload

    def json(self):
        return self._p


class _Client:
    def __init__(self, payload):
        self.payload = payload
        self.urls: list[str] = []

    async def get(self, url, **kw):
        self.urls.append(url)
        return _Resp(self.payload)


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setattr(eph, "HAS_SWISS_EPHEMERIS", True, raising=False)
    monkeypatch.setattr(mf, "_now", lambda: NOW)
    monkeypatch.delenv(mf.ENV_MAX_AGE_BARS, raising=False)


def _patch(payload):
    client = _Client({"code": "0", "msg": "", "data": payload})
    return client, patch.object(qa, "get_http_client", return_value=client)


@pytest.mark.asyncio
async def test_fetch_parses_okx_envelope_oldest_first():
    client, p = _patch(_rows(100, 3600))
    with p:
        data = await qa.QuantAgent()._fetch_price_history("BTCUSDT", "SWING")
    assert len(data) == 100
    assert client.urls[0].endswith("instId=BTC-USDT&bar=1D&limit=100")
    closes = [d[0] for d in data]
    assert closes == sorted(closes), "candles must be oldest first"
    assert closes[-1] == 200.0  # newest close last


@pytest.mark.asyncio
async def test_fresh_uptrend_produces_real_signal():
    _, p = _patch(_rows(100, 3600, trend=1.0))
    with p:
        r = await qa.QuantAgent().analyze({"symbol": "BTCUSDT", "current_price": 200.0})
    assert r.signal == SignalDirection.LONG
    assert "momentum" in (r.metadata or {})


@pytest.mark.asyncio
@pytest.mark.parametrize("age_s", [4 * DAY, 30 * DAY])
async def test_stale_candles_fail_closed(age_s):
    _, p = _patch(_rows(100, age_s))
    with p:
        r = await qa.QuantAgent().analyze({"symbol": "BTCUSDT", "current_price": 200.0})
    assert r.signal == SignalDirection.NEUTRAL
    assert r.metadata.get("no_data") is True


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [[], None])
async def test_missing_candles_fail_closed(payload):
    _, p = _patch(payload)
    with p:
        r = await qa.QuantAgent().analyze({"symbol": "BTCUSDT", "current_price": 200.0})
    assert r.signal == SignalDirection.NEUTRAL
    assert r.metadata.get("no_data") is True


@pytest.mark.asyncio
@pytest.mark.parametrize("state", [{"symbol": "BTCUSDT"}, {"symbol": "BTCUSDT", "current_price": 0}])
async def test_missing_price_fail_closed_no_50000(state):
    client, p = _patch(_rows(100, 3600))
    with p:
        r = await qa.QuantAgent().analyze(state)
    assert r.signal == SignalDirection.NEUTRAL
    assert r.metadata.get("no_data") is True
    assert r.metadata.get("reason") == "no_price"
