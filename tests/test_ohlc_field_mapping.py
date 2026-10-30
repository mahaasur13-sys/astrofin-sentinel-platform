"""OHLC field mapping (P2): bull/bear researchers must read high/low from the
right columns, RiskAgent ATR must use real high/low/prev-close and fail closed
when ATR cannot be computed. No network: httpx.AsyncClient is mocked."""

from __future__ import annotations

import httpx
import pytest

from core import market_freshness as mf

NOW = 1_800_000_000.0
DAY = 86400


def _okx(bars: list) -> list:
    """bars oldest-first as (o, h, l, c, v) -> OKX rows newest-first, fresh ts."""
    n = len(bars)
    rows = []
    for j, (o, h, low, c, v) in enumerate(bars):
        ts = NOW - 3600 - (n - 1 - j) * DAY
        rows.append([str(int(ts * 1000)), str(o), str(h), str(low), str(c), str(v), "0", "0", "1"])
    return list(reversed(rows))


class _Resp:
    status_code = 200

    def __init__(self, payload):
        self._p = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._p


ROWS: list = []


class _FakeClient:
    def __init__(self, *a, **kw):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, **kw):
        return _Resp({"code": "0", "msg": "", "data": [list(r) for r in ROWS]})


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setattr(mf, "_now", lambda: NOW)
    monkeypatch.delenv(mf.ENV_MAX_AGE_BARS, raising=False)
    monkeypatch.setattr(httpx, "AsyncClient", _FakeClient)


def _set(bars):
    ROWS[:] = _okx(bars)


# 25 bars, flat close 150; lows flat at 100, highs flat at 200,
# last 5 bars: high jumps to 210 (breakout) and low drops to 90 (breakdown)
BREAK_BARS = [(150, 200, 100, 150, 10)] * 20 + [(150, 210, 90, 150, 10)] * 5


@pytest.mark.asyncio
async def test_fetch_keeps_high_above_low():
    from agents._impl.bull_researcher import BullResearcherAgent

    _set(BREAK_BARS)
    data = await BullResearcherAgent()._fetch_ohlcv("BTCUSDT", "1D", 25)
    assert all(r[1] >= r[2] for r in data)  # [o, h, l, c, v]


@pytest.mark.asyncio
async def test_bull_breakout_reads_highs():
    from agents._impl.bull_researcher import BullResearcherAgent

    agent = BullResearcherAgent()
    _set(BREAK_BARS)
    res = agent._detect_bullish_patterns(await agent._fetch_ohlcv("BTCUSDT", "1D", 25))
    assert "breakout: yes" in res["summary"]


@pytest.mark.asyncio
async def test_bull_higher_lows_reads_lows():
    from agents._impl.bull_researcher import BullResearcherAgent

    # lows rise every bar, highs flat
    bars = [(150, 200, 100 + j, 150, 10) for j in range(25)]
    agent = BullResearcherAgent()
    _set(bars)
    res = agent._detect_bullish_patterns(await agent._fetch_ohlcv("BTCUSDT", "1D", 25))
    assert res["summary"].startswith("Higher lows: 22")
    assert "breakout: no" in res["summary"]


@pytest.mark.asyncio
async def test_bear_breakdown_reads_lows():
    from agents._impl.bear_researcher import BearResearcherAgent

    agent = BearResearcherAgent()
    _set(BREAK_BARS)
    res = agent._detect_bearish_patterns(await agent._fetch_ohlcv("BTCUSDT", "1D", 25))
    assert "breakdown: yes" in res["summary"]


@pytest.mark.asyncio
async def test_bear_lower_highs_reads_highs():
    from agents._impl.bear_researcher import BearResearcherAgent

    # highs fall every bar, lows flat
    bars = [(150, 300 - j, 100, 150, 10) for j in range(25)]
    agent = BearResearcherAgent()
    _set(bars)
    res = agent._detect_bearish_patterns(await agent._fetch_ohlcv("BTCUSDT", "1D", 25))
    assert res["summary"].startswith("Lower highs: 22")
    assert "breakdown: no" in res["summary"]


# ATR: close alternates 100/104, high = c + 5, low = c - 3.
# TR_i = max(8, |c+5 - c_prev|, |c-3 - c_prev|):
#   c=104, prev 100 -> max(8, 9, 1) = 9 ; c=100, prev 104 -> max(8, 1, 7) = 8
ATR_BARS = [(c, c + 5, c - 3, c, 10) for c in ([100, 104] * 15)]  # 30 bars
# last 14 TRs: 7 x 9 (c=104) + 7 x 8 (c=100) -> 8.5
EXPECTED_ATR = 8.5


@pytest.mark.asyncio
async def test_risk_atr_from_ohlc():
    from agents._impl.risk_agent import RiskAgent

    agent = RiskAgent()
    _set(ATR_BARS)
    data = await agent._fetch_ohlcv("BTCUSDT", "1D", 30)
    assert agent._calculate_atr(data, 14) == pytest.approx(EXPECTED_ATR)


@pytest.mark.asyncio
async def test_risk_run_reports_atr_not_degraded():
    from agents._impl.risk_agent import RiskAgent

    _set(ATR_BARS)
    resp = await RiskAgent().run({"symbol": "BTCUSDT", "current_price": 104.0})
    assert not resp.metadata.get("degraded")
    assert "ATR(14): $8.50" in resp.reasoning


@pytest.mark.asyncio
async def test_risk_insufficient_data_fails_closed():
    from agents._impl.risk_agent import RiskAgent

    agent = RiskAgent()
    _set(ATR_BARS[:10])
    data = await agent._fetch_ohlcv("BTCUSDT", "1D", 30)
    assert agent._calculate_atr(data, 14) is None
    resp = await agent.run({"symbol": "BTCUSDT", "current_price": 104.0})
    assert resp.signal.value.upper() == "NEUTRAL"
    assert resp.metadata.get("no_data") is True
    assert "Not enough OHLC data" in resp.reasoning


# close 150, highs 200 / lows 100, one swing at bar 10: low 95, high 205
SWING_BARS = [(150, 205 if j == 10 else 200, 95 if j == 10 else 100, 150, 10) for j in range(25)]


@pytest.mark.asyncio
async def test_bull_support_from_lows_vs_close():
    from agents._impl.bull_researcher import BullResearcherAgent

    agent = BullResearcherAgent()
    _set(SWING_BARS)
    res = agent._find_support_zones(await agent._fetch_ohlcv("BTCUSDT", "1D", 25))
    # (150 - 95) / 150 = 36.7 %
    assert res["summary"] == "support at $95 (36.7% below)"


@pytest.mark.asyncio
async def test_bear_resistance_from_highs_vs_close():
    from agents._impl.bear_researcher import BearResearcherAgent

    agent = BearResearcherAgent()
    _set(SWING_BARS)
    res = agent._find_resistance_zones(await agent._fetch_ohlcv("BTCUSDT", "1D", 25))
    # (205 - 150) / 150 = 36.7 %
    assert "$205" in res["summary"] and "36.7%" in res["summary"]
