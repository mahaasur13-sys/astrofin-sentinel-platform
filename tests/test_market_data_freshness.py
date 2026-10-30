"""Regression: stale OKX candles and a missing current price must be no_data.

* Candles whose newest bar is older than ~2 intervals are dropped (=> the
  #479 no_data path) instead of being used as current market data.
* ``_fetch_price`` returns ``None`` on failure (no made-up 50000) and agents
  that need the price answer NEUTRAL/no_data.

Time is frozen (FIXED_NOW); network is fully mocked; no yfinance needed.
"""

from __future__ import annotations

import asyncio
import importlib
from datetime import datetime, timezone
from unittest import mock

import httpx
import pytest

FIXED_NOW = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc).timestamp()
HOUR = 3600
DAY = 86400

CANDLE_AGENTS = [
    ("technical_agent", "TechnicalAgent"),
    ("time_window_agent", "TimeWindowAgent"),
    ("market_analyst", "MarketAnalystAgent"),
    ("cycle_agent", "CycleAgent"),
    ("bradley_agent", "BradleyAgent"),
    ("elliot_agent", "ElliotAgent"),
    ("gann_agent", "GannAgent"),
    ("bull_researcher", "BullResearcherAgent"),
    ("bear_researcher", "BearResearcherAgent"),
    ("risk_agent", "RiskAgent"),
]

PRICE_AGENTS = [
    ("technical_agent", "TechnicalAgent"),
    ("risk_agent", "RiskAgent"),
    ("ml_predictor_agent", "MLPredictorAgent"),
    ("options_flow_agent", "OptionsFlowAgent"),
    ("fundamental_agent", "FundamentalAgent"),
]


def _agent(mod: str, cls: str):
    return getattr(importlib.import_module(f"agents._impl.{mod}"), cls)()


def _okx_rows(newest_age_s: float, step_s: int, n: int = 60) -> list:
    """OKX v5 candles (newest first): [ts_ms, o, h, l, c, vol, ...]."""
    newest = FIXED_NOW - newest_age_s
    rows = []
    for i in range(n):
        c = 60000 + 500 * ((i * 7) % 11) - 30 * i
        rows.append([str(int((newest - i * step_s) * 1000)), str(c - 50), str(c + 200), str(c - 200),
                     str(c), str(100 + i), "0", "0", "1"])
    return rows


def _fake_get(rows: list):
    async def fake(self, url, *a, **k):
        return httpx.Response(200, json={"code": "0", "msg": "", "data": rows},
                              request=httpx.Request("GET", url))
    return fake


def _fetch(agent, rows: list, bar: str):
    with mock.patch.object(httpx.AsyncClient, "get", _fake_get(rows)), \
         mock.patch("time.time", return_value=FIXED_NOW):
        return asyncio.run(agent._fetch_ohlcv("BTCUSDT", bar, 60))


# ── candles ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("mod,cls", CANDLE_AGENTS, ids=[m for m, _ in CANDLE_AGENTS])
@pytest.mark.parametrize("bar,step,age", [("1d", DAY, 10 * DAY), ("1D", DAY, 4 * DAY),
                                          ("4H", 4 * HOUR, 13 * HOUR), ("1W", 7 * DAY, 30 * DAY)])
def test_stale_candles_are_dropped(mod, cls, bar, step, age):
    assert _fetch(_agent(mod, cls), _okx_rows(age, step), bar) == []


@pytest.mark.parametrize("mod,cls", CANDLE_AGENTS, ids=[m for m, _ in CANDLE_AGENTS])
@pytest.mark.parametrize("bar,step,age", [("1d", DAY, 3 * HOUR), ("1D", DAY, 71 * HOUR),
                                          ("4H", 4 * HOUR, 1 * HOUR), ("1W", 7 * DAY, 8 * DAY)])
def test_fresh_candles_are_kept(mod, cls, bar, step, age):
    assert len(_fetch(_agent(mod, cls), _okx_rows(age, step), bar)) == 60


def test_technical_agent_stale_candles_is_no_data():
    agent = _agent("technical_agent", "TechnicalAgent")
    rows = _okx_rows(10 * DAY, DAY)
    with mock.patch.object(httpx.AsyncClient, "get", _fake_get(rows)), \
         mock.patch("time.time", return_value=FIXED_NOW):
        r = asyncio.run(agent.run({"symbol": "BTCUSDT", "current_price": 61000.0}))
    assert str(getattr(r.signal, "value", r.signal)) == "NEUTRAL"
    assert r.metadata.get("no_data") is True


def test_freshness_helper_threshold_env(monkeypatch):
    from core.market_freshness import bar_seconds, candles_are_fresh

    assert bar_seconds("4H") == 4 * HOUR and bar_seconds("1d") == DAY
    assert bar_seconds("1Dutc") == DAY and bar_seconds("15m") == 900
    assert bar_seconds("bogus") is None
    rows = _okx_rows(30 * HOUR, DAY)
    assert candles_are_fresh(rows, "1D", now=FIXED_NOW)
    monkeypatch.setenv("ASTROFIN_CANDLE_MAX_AGE_BARS", "1")
    assert not candles_are_fresh(rows, "1D", now=FIXED_NOW)
    # undated / unknown bar -> fail-closed
    assert not candles_are_fresh([["x", "1"]], "1D", now=FIXED_NOW)
    assert not candles_are_fresh(rows, "??", now=FIXED_NOW)


# ── current price ──────────────────────────────────────────────────────────

def test_fetch_price_failure_returns_none():
    from orchestration import result_aggregator as ra

    class Boom:
        async def resolve(self, symbol):
            raise httpx.ConnectError("dns timeout")

        async def close(self):
            pass

    with mock.patch("data_room.resolvers.coingecko.CoinGeckoResolver", Boom):
        assert asyncio.run(ra._fetch_price("BTCUSDT")) is None


@pytest.mark.parametrize("mod,cls", PRICE_AGENTS, ids=[m for m, _ in PRICE_AGENTS])
@pytest.mark.parametrize("price", [None, 0, "missing"])
def test_agent_without_price_is_no_data(mod, cls, price):
    state = {"symbol": "BTCUSDT"}
    if price != "missing":
        state["current_price"] = price

    async def no_net(self, url, *a, **k):
        raise httpx.ConnectError("network disabled in test")

    with mock.patch.object(httpx.AsyncClient, "get", no_net):
        r = asyncio.run(_agent(mod, cls).run(state))
    assert str(getattr(r.signal, "value", r.signal)) == "NEUTRAL"
    assert r.metadata.get("no_data") is True
    assert "50000" not in (r.reasoning or "")


def test_history_db_accepts_missing_price(tmp_path):
    from core.history_db import HistoryDB

    db = HistoryDB(db_path=tmp_path / "h.db")
    db.save({"session_id": "s1", "symbol": "BTCUSDT", "current_price": None})

