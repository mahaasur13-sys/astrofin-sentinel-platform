"""P3 live-signal cleanup (no network, mocks only).

(a) OKX /market/candles is requested with a documented ``bar`` (``1D``,
    not ``1d``; OKX v5 "Get candlesticks": [6H/12H/1D/2D/3D/1W/1M/3M]).
(b) Missing price never turns into a made-up 50000: agents/synthesis/DAG
    are fail-closed (NEUTRAL no_data / ``None``).
(c) ``run_*_agent`` wrappers go through ``run()`` so an exception in
    ``analyze()`` degrades to NEUTRAL instead of escaping.
"""

from __future__ import annotations

import importlib
import sys
import types

import httpx
import pytest

from core.dag import DAGContext

OKX_BAD_BAR = "bar=1d"


class _Resp:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {"code": "0", "msg": "", "data": []}


def _recording_client(urls: list):
    class _C:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def get(self, url, **kw):
            params = kw.get("params") or {}
            urls.append(str(url) + "&" + "&".join(f"{k}={v}" for k, v in params.items()))
            return _Resp()

    return _C


# ── (a) bar value ────────────────────────────────────────────────────────
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mod,cls",
    [
        ("agents._impl.technical_agent", "TechnicalAgent"),
        ("agents._impl.market_analyst", "MarketAnalystAgent"),
    ],
)
async def test_okx_candles_use_documented_bar(monkeypatch, mod, cls):
    urls: list = []
    monkeypatch.setattr(httpx, "AsyncClient", _recording_client(urls))
    m = importlib.import_module(mod)
    klass = getattr(m, cls, None) or next(
        v for k, v in vars(m).items() if isinstance(v, type) and k.endswith("Agent") and v.__module__ == m.__name__
    )
    await klass().run({"symbol": "BTCUSDT", "current_price": 100.0})
    okx = [u for u in urls if "/market/candles" in u]
    assert okx, "agent did not request OKX candles"
    for u in okx:
        assert "bar=1D" in u and OKX_BAD_BAR not in u, u


@pytest.mark.parametrize(
    "path",
    [
        "agents/_impl/technical_agent.py",
        "agents/_impl/market_analyst.py",
        "agents/_impl/bear_researcher.py",
        "agents/_impl/bull_researcher.py",
        "agents/_impl/risk_agent.py",
        "agents/_impl/cycle_agent.py",
        "agents/_impl/time_window_agent.py",
    ],
)
def test_no_lowercase_okx_bar(path):
    src = open(path, encoding="utf-8").read()
    assert '_fetch_ohlcv(symbol, "1d"' not in src


# ── (b) no made-up 50000 ─────────────────────────────────────────────────
def _assert_no_price(resp):
    d = resp.to_dict() if hasattr(resp, "to_dict") else resp
    assert "50000" not in repr(d)
    assert d["signal"] in ("NEUTRAL", getattr(d["signal"], "value", None))
    assert (d.get("metadata") or {}).get("no_data") is True


@pytest.mark.asyncio
async def test_market_analyst_without_price_fail_closed(monkeypatch):
    from agents._impl import market_analyst as ma

    async def _never(*a, **kw):  # must not even need candles
        return [[100.0 + i, 1.0] for i in range(50)]

    monkeypatch.setattr(ma.MarketAnalystAgent, "_fetch_ohlcv", _never, raising=False)
    _assert_no_price(await ma.MarketAnalystAgent().run({"symbol": "BTCUSDT"}))


def _signals():
    from core.base_agent import AgentResponse, SignalDirection

    return [
        AgentResponse(agent_name=f"A{i}", signal=SignalDirection.LONG if i % 2 else SignalDirection.SHORT,
                      confidence=70, reasoning="x", sources=[])
        for i in range(6)
    ]


@pytest.mark.asyncio
async def test_synthesis_without_price_fail_closed():
    from agents._impl.synthesis.agent import SynthesisAgent

    _assert_no_price(await SynthesisAgent().run({"symbol": "BTCUSDT", "all_signals": _signals()}))


@pytest.mark.asyncio
async def test_compromise_without_price_fail_closed():
    from agents._impl.compromise_agent import CompromiseAgent

    _assert_no_price(await CompromiseAgent().run({"symbol": "BTCUSDT", "all_signals": _signals()}))


@pytest.mark.asyncio
async def test_karl_without_price_fail_closed():
    from agents.karl_synthesis import KARLSynthesisAgent

    out = await KARLSynthesisAgent(enable_backtest=False).run({"symbol": "BTCUSDT", "all_signals": _signals()})
    _assert_no_price(out["synthesis_result"])
    assert out["decision_record"] is None


def test_weights_calibrator_without_price_no_update():
    from agents._impl.amre.reward import RewardState
    from agents._impl.amre.weights_calibrator import estimate_karl_reward

    rs = RewardState()
    before = (rs.ema_reward, rs.count)

    def _ms(**kw):
        raise AssertionError(f"MarketState built with {kw.get('price')!r}")

    estimate_karl_reward({"symbol": "BTC"}, [], 50, "NEUTRAL", rs, _ms)
    assert (rs.ema_reward, rs.count) == before


def test_dag_price_helpers_return_none_not_50000():
    from orchestration import dag_nodes as dn

    ctx = DAGContext()
    assert dn.SynthesisNode._get_price(None, ctx) is None
    assert dn.PersistNode._get_price_for_persist(None, ctx) is None


@pytest.mark.asyncio
async def test_dag_price_node_fallback_is_none(monkeypatch):
    from orchestration import dag_nodes as dn

    fake = types.ModuleType("data_room.resolvers.coingecko")

    class _R:
        async def resolve(self, symbol):
            raise RuntimeError("offline")

        async def close(self):
            return None

    fake.CoinGeckoResolver = _R
    monkeypatch.setitem(sys.modules, "data_room.resolvers.coingecko", fake)
    node = dn.PriceNode.__new__(dn.PriceNode)
    out = await dn.PriceNode.run(node, DAGContext())
    assert out["price"] is None and out.get("fallback") is True
    assert "50000" not in repr(out)


# ── (c) run_*_agent must go through run() ────────────────────────────────
RUNNERS = [
    ("quant_agent", "QuantAgent", "run_quant_agent"),
    ("bear_researcher", "BearResearcherAgent", "run_bear_researcher"),
    ("bull_researcher", "BullResearcherAgent", "run_bull_researcher"),
    ("risk_agent", "RiskAgent", "run_risk_agent"),
    ("cycle_agent", "CycleAgent", "run_cycle_agent"),
    ("time_window_agent", "TimeWindowAgent", "run_time_window_agent"),
    ("gann_agent", "GannAgent", "run_gann_agent"),
    ("elliot_agent", "ElliotAgent", "run_elliot_agent"),
    ("bradley_agent", "BradleyAgent", "run_bradley_agent"),
    ("sentiment_agent", "SentimentAgent", "run_sentiment_agent"),
    ("options_flow_agent", "OptionsFlowAgent", "run_options_flow_agent"),
    ("insider_agent", "InsiderAgent", "run_insider_agent"),
    ("fundamental_agent", "FundamentalAgent", "run_fundamental_agent"),
    ("macro_agent", "MacroAgent", "run_macro_agent"),
    ("ml_predictor_agent", "MLPredictorAgent", "run_ml_predictor_agent"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("mod,cls,fn", RUNNERS, ids=[r[2] for r in RUNNERS])
async def test_runner_exception_degrades(monkeypatch, mod, cls, fn):
    m = importlib.import_module(f"agents._impl.{mod}")

    async def _boom(self, state):
        raise RuntimeError("boom-in-analyze")

    monkeypatch.setattr(getattr(m, cls), "analyze", _boom)
    out = await getattr(m, fn)({"symbol": "BTCUSDT", "current_price": 100.0})
    (sig,) = [v for v in out.values() if isinstance(v, dict)]
    assert sig["signal"] == "NEUTRAL"
    assert sig["metadata"].get("degraded") is True
