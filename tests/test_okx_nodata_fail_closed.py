"""Regression: when every OKX request fails, no agent and no council may emit
a directional signal derived from missing market data (fail-closed).

Network is fully mocked (httpx.AsyncClient.get/post); no real I/O.
"""
from __future__ import annotations

import asyncio
from unittest import mock

import httpx
import pytest

from core.base_agent import SignalDirection

STATE = {"symbol": "BTCUSDT", "current_price": 50000}

# ---- deterministic astro inputs -------------------------------------------
# Explicit choghadiya windows: favourable (LONG), unfavourable (SHORT), AVOID (Marana), neutral.
CHOGHADIYA = {
    "amrita_long": {"name": "Amrita", "quality": "best", "score": 9.0},
    "mrityu_short": {"name": "Mrityu", "quality": "bad", "score": 2.0},
    "marana_avoid": {"name": "Marana", "quality": "worst", "score": 1.0},
    "kala_neutral": {"name": "Kala", "quality": "neutral", "score": 5.0},
}
NAKSHATRA = {"name": "Mrigashira", "pada": 4, "quality": "good", "longitude": 65.9}

# Real ephemeris at frozen instants (UTC), incl. 2026-10-30 05:47 when the v1 test failed (Marana).
FROZEN_UTC = ["2026-10-30T05:47:00", "2026-10-30T02:00:00", "2026-10-30T12:00:00", "2026-01-01T00:00:00"]


@pytest.fixture(params=sorted(CHOGHADIYA), ids=lambda k: f"chog-{k}")
def astro_window(request):
    ch = CHOGHADIYA[request.param]
    with mock.patch("astrology.vedic.get_choghadiya", return_value=dict(ch)), \
         mock.patch("astrology.vedic.get_current_nakshatra", return_value=dict(NAKSHATRA)):
        yield request.param


@pytest.fixture(params=FROZEN_UTC, ids=lambda t: f"utc-{t}")
def frozen_astro(request):
    """Real vedic functions evaluated at a frozen instant (offsets relative to 'now' preserved)."""
    from datetime import datetime, timedelta

    import astrology.vedic as vedic

    frozen = datetime.fromisoformat(request.param)
    real_ch, real_nak = vedic.get_choghadiya, vedic.get_current_nakshatra

    def _shift(dt):
        hours = round((dt - datetime.utcnow()).total_seconds() / 3600)
        return frozen + timedelta(hours=hours)

    with mock.patch("astrology.vedic.get_choghadiya", side_effect=lambda dt, *a, **k: real_ch(_shift(dt), *a, **k)), \
         mock.patch("astrology.vedic.get_current_nakshatra", side_effect=lambda dt, *a, **k: real_nak(_shift(dt), *a, **k)):
        yield real_ch(frozen)["name"]


def _make_get(mode: str):
    async def fake(self, url, *a, **k):
        req = httpx.Request("GET", url)
        if mode == "dns":
            raise httpx.ConnectError("dns timeout", request=req)
        if mode == "empty":
            return httpx.Response(200, json={"code": "0", "data": []}, request=req)
        if mode == "code_err":
            return httpx.Response(200, json={"code": "50011", "msg": "x", "data": []}, request=req)
        if mode == "http500":
            return httpx.Response(500, text="<html>cf</html>", request=req)
        raise AssertionError(mode)
    return fake


MODES = ["dns", "empty", "code_err", "http500"]

AGENTS = [
    ("market_analyst", "MarketAnalystAgent"),
    ("technical_agent", "TechnicalAgent"),
    ("quant_agent", "QuantAgent"),
    ("bull_researcher", "BullResearcherAgent"),
    ("bear_researcher", "BearResearcherAgent"),
    ("risk_agent", "RiskAgent"),
    ("cycle_agent", "CycleAgent"),
    ("bradley_agent", "BradleyAgent"),
    ("gann_agent", "GannAgent"),
    ("elliot_agent", "ElliotAgent"),
    ("time_window_agent", "TimeWindowAgent"),
    ("sentiment_agent", "SentimentAgent"),
]

DIRECTIONAL = {"LONG", "SHORT", "BUY", "SELL", "STRONG_BUY", "STRONG_SELL"}


def _sig(r) -> str:
    s = r.signal
    return s.value if isinstance(s, SignalDirection) else str(s)


def _run(coro):
    return asyncio.run(coro)


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("mod,cls", AGENTS)
def test_agent_no_okx_data_is_not_directional(mod, cls, mode, astro_window):
    import importlib

    m = importlib.import_module(f"agents._impl.{mod}")
    klass = getattr(m, cls, None)
    if klass is None:  # tolerate naming drift, pick the module's agent class
        klass = next(v for k, v in vars(m).items()
                     if isinstance(v, type) and v.__module__ == m.__name__ and hasattr(v, "analyze"))
    fake = _make_get(mode)
    with mock.patch.object(httpx.AsyncClient, "get", fake), \
         mock.patch.object(httpx.AsyncClient, "post", fake):
        r = _run(klass().analyze(dict(STATE)))
    assert _sig(r) not in DIRECTIONAL, f"{cls}/{mode}: {_sig(r)} {r.confidence} {r.reasoning}"


@pytest.mark.parametrize("mode", MODES)
def test_hybrid_council_all_okx_down_is_neutral(mode, astro_window):
    from agents.astro_council_agent import AstroCouncilAgent

    fake = _make_get(mode)
    with mock.patch.object(httpx.AsyncClient, "get", fake), \
         mock.patch.object(httpx.AsyncClient, "post", fake):
        r = _run(AstroCouncilAgent().run(dict(STATE)))
    assert r.signal == SignalDirection.NEUTRAL, r.reasoning


def _astro_council_all_down(mode):
    from agents._impl.astro_council.agent import AstroCouncilAgent

    fake = _make_get(mode)
    with mock.patch.object(httpx.AsyncClient, "get", fake):
        council = AstroCouncilAgent()
        tw = _run(council.agents["TimeWindowAgent"].run(dict(STATE)))
        final = _run(council.aggregate(dict(STATE)))
    return tw, final


@pytest.mark.parametrize("mode", MODES)
def test_astro_council_frozen_real_ephemeris_all_okx_down(mode, frozen_astro):
    tw, final = _astro_council_all_down(mode)
    assert _sig(tw) not in DIRECTIONAL, (frozen_astro, tw.reasoning)
    assert final.signal == SignalDirection.NEUTRAL, (frozen_astro, final.reasoning)


@pytest.mark.parametrize("mode", MODES)
def test_astro_council_all_okx_down_time_window_not_directional(mode, astro_window):
    """agents/_impl/astro_council/agent.py (used by backtest/engine.py)."""
    from agents._impl.astro_council.agent import AstroCouncilAgent

    fake = _make_get(mode)
    with mock.patch.object(httpx.AsyncClient, "get", fake):
        council = AstroCouncilAgent()
        tw = _run(council.agents["TimeWindowAgent"].run(dict(STATE)))
        final = _run(council.aggregate(dict(STATE)))
    assert _sig(tw) not in DIRECTIONAL, tw.reasoning
    # Electoral is astro-only by design; with market agents silent the council must not go directional
    assert final.signal == SignalDirection.NEUTRAL, final.reasoning


def test_orchestrator_neutral_consensus_places_no_order():
    from orchestration.council_orchestrator import CouncilOrchestrator
    from core.base_agent import AgentResponse

    risk = mock.MagicMock()
    orch = CouncilOrchestrator(risk)
    orch.adjust_through_risk = lambda size, resp: (size, "ok")
    with mock.patch("orchestration.council_orchestrator.get_broker") as gb:
        out = _run(orch.execute_trading_cycle(
            [], AgentResponse(agent_name="AstroCouncil", signal=SignalDirection.NEUTRAL, confidence=5, reasoning=""),
            is_backtest=True))
    assert out["action"] == "NEUTRAL" and out["size"] == 0.0
    gb.assert_not_called()


def test_orchestrator_directional_without_market_data_is_denied():
    """Even if a LONG slips through, SafetyGate must deny without cfg['market'] (no live data)."""
    from orchestration.council_orchestrator import CouncilOrchestrator
    from core.base_agent import AgentResponse

    orch = CouncilOrchestrator(mock.MagicMock())
    orch.adjust_through_risk = lambda size, resp: (0.1, "ok")
    broker = mock.MagicMock()
    with mock.patch("orchestration.council_orchestrator.get_broker", return_value=broker):
        out = _run(orch.execute_trading_cycle(
            [], AgentResponse(agent_name="AstroCouncil", signal=SignalDirection.LONG, confidence=28, reasoning=""),
            config={"current_price": 50000.0, "equity": 10000.0, "trading_mode": "PAPER"}))
    assert out["action"] == "DENIED", out
    assert not broker.place_order.called and not getattr(broker, "submit_order", mock.MagicMock()).called


# ---- second council voting rules (pure, no I/O) ----------------------------
def _r(name, sig, conf=80, **meta):
    from core.base_agent import AgentResponse
    return AgentResponse(agent_name=name, signal=sig, confidence=conf, reasoning="t", sources=[], metadata=meta)


def _council2():
    from agents._impl.astro_council.agent import AstroCouncilAgent
    return AstroCouncilAgent()


def test_council2_avoid_does_not_crash_and_vetoes_direction():
    L = SignalDirection.LONG
    out = _council2()._weighted_vote({
        "BradleyAgent": _r("BradleyAgent", L), "GannAgent": _r("GannAgent", L),
        "CycleAgent": _r("CycleAgent", L), "TimeWindowAgent": _r("TimeWindowAgent", L),
        "ElectoralAgent": _r("ElectoralAgent", SignalDirection.AVOID, 75),
    })
    assert out.signal == SignalDirection.NEUTRAL and "AVOID veto" in out.reasoning


@pytest.mark.parametrize("bad", ["HOLD", "garbage", None, 123])
def test_council2_unknown_signal_is_neutral(bad):
    out = _council2()._weighted_vote({"BradleyAgent": _r("BradleyAgent", bad),
                                      "GannAgent": _r("GannAgent", bad)})
    assert out.signal == SignalDirection.NEUTRAL


def test_council2_astrology_only_is_neutral():
    N = SignalDirection.NEUTRAL
    out = _council2()._weighted_vote({
        "BradleyAgent": _r("BradleyAgent", N, 20, no_data=True),
        "GannAgent": _r("GannAgent", N, 20, no_data=True),
        "CycleAgent": _r("CycleAgent", N, 25, no_data=True),
        "TimeWindowAgent": _r("TimeWindowAgent", N, 20, no_data=True),
        "ElectoralAgent": _r("ElectoralAgent", SignalDirection.LONG, 100),
    })
    assert out.signal == SignalDirection.NEUTRAL


@pytest.mark.parametrize("sig", [SignalDirection.LONG, SignalDirection.SHORT, "BUY", "SELL"])
def test_council2_market_backed_direction_still_passes(sig):
    out = _council2()._weighted_vote({n: _r(n, sig, 80) for n in
                                      ["BradleyAgent", "GannAgent", "CycleAgent", "TimeWindowAgent"]})
    exp = SignalDirection.LONG if str(getattr(sig, "value", sig)) in ("LONG", "BUY") else SignalDirection.SHORT
    assert out.signal == exp
