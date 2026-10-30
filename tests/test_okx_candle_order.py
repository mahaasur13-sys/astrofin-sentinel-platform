"""OKX returns candles newest first; every agent must see them oldest -> newest
so that ``closes[-1]`` / ``[-N:]`` mean "latest" (P2 candle order)."""

from __future__ import annotations

import importlib

import httpx
import pytest

from core import market_freshness as mf

NOW = 1_800_000_000.0
DAY = 86400
N = 60


def _okx_rows(n: int = N) -> list:
    """Newest first, steady uptrend in time (close = 100 + 2*j, j=0 oldest).

    Read in OKX order the series looks like a downtrend, so RSI on the
    wrong order is ~0 and on the right order ~100.
    """
    rows = []
    for i in range(n):  # i=0 newest
        j = n - 1 - i
        close = 100.0 + 2 * j
        ts = NOW - 3600 - i * DAY
        rows.append([str(int(ts * 1000)), str(close), str(close + 1), str(close - 1), str(close), "10", "0", "0", "1"])
    return rows


ROWS = _okx_rows()
CHRONO_CLOSES = [float(r[4]) for r in reversed(ROWS)]


class _Resp:
    status_code = 200

    def __init__(self, payload):
        self._p = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._p


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


def test_fresh_okx_rows_sorted_oldest_first():
    out = mf.fresh_okx_rows(ROWS, "1D")
    assert [float(r[4]) for r in out] == CHRONO_CLOSES
    # idempotent on already sorted input
    assert mf.fresh_okx_rows(out, "1D") == out


def test_fresh_okx_rows_stale_still_empty():
    old = [[str(int((NOW - 30 * DAY) * 1000)), "1", "1", "1", "1", "1"]]
    assert mf.fresh_okx_rows(old, "1D") == []


# (module, class, column index of close in the agent's row)
AGENTS = [
    ("technical_agent", "TechnicalAgent", 0),
    ("market_analyst", "MarketAnalystAgent", 0),
    ("risk_agent", "RiskAgent", 0),
    ("cycle_agent", "CycleAgent", 0),
    ("time_window_agent", "TimeWindowAgent", 0),
    ("bear_researcher", "BearResearcherAgent", 3),
    ("bull_researcher", "BullResearcherAgent", 3),
    ("bradley_agent", "BradleyAgent", 4),
    ("gann_agent", "GannAgent", 4),
    ("elliot_agent", "ElliotAgent", 4),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("mod,cls,col", AGENTS, ids=[a[0] for a in AGENTS])
async def test_agent_fetch_oldest_first(mod, cls, col):
    m = importlib.import_module(f"agents._impl.{mod}")
    agent = getattr(m, cls)()
    data = await agent._fetch_ohlcv("BTCUSDT", "1D", N)
    assert [row[col] for row in data] == CHRONO_CLOSES
    assert data[-1][col] == CHRONO_CLOSES[-1]  # current = newest bar


@pytest.mark.asyncio
async def test_technical_rsi_uses_latest_bars():
    from agents._impl.technical_agent import TechnicalAgent

    agent = TechnicalAgent()
    data = await agent._fetch_ohlcv("BTCUSDT", "1D", N)
    ind = agent._calculate_indicators(data, CHRONO_CLOSES[-1])
    assert ind["rsi"] > 70  # last 14 deltas are all gains


@pytest.mark.asyncio
async def test_market_analyst_rsi_uses_latest_bars():
    from agents._impl.market_analyst import MarketAnalystAgent

    agent = MarketAnalystAgent()
    data = await agent._fetch_ohlcv("BTCUSDT", "1D", N)
    assert agent._calculate_rsi(data) > 70
