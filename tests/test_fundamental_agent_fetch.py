"""FundamentalAgent contract tests — offline, network-free.

Rewritten for the canonical post-``233ad1c5`` contract. The ratified
resolver-map commit removed the module-level cache from
``agents._impl.fundamental_agent`` (``_CACHE``, ``_CACHE_TTL``,
``_cache_get``, ``_cache_set``, ``_fetch_fundamental_data``), so this file
no longer imports or exercises them.

Covered instead — the real public and protected surface of the agent:

* BaseAgent inheritance, identity and registry metadata
* ``run(state)`` -> ``AgentResponse`` on a valid state
* valuation-driven signal direction plus deterministic confidence/reasoning
* degradation through ``BaseAgent._degraded`` when Swiss Ephemeris is absent
* degradation through ``BaseAgent._degraded`` when the agent raises
* offline fallbacks for both CoinGecko fetch helpers
* session lifecycle for the on-chain helper
* determinism and absence of module-level shared state between calls

No test performs real HTTP and no external service is contacted.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents._impl import fundamental_agent as _mod
from agents._impl.fundamental_agent import FundamentalAgent
from core.base_agent import (
    EPHEMERIS_UNAVAILABLE,
    UNKNOWN,
    AgentResponse,
    BaseAgent,
    SignalDirection,
)

_EPHEMERIS_FLAG = "agents._impl.ephemeris_decorator.HAS_SWISS_EPHEMERIS"
_CLIENT_SESSION = "agents._impl.fundamental_agent.aiohttp.ClientSession"

_ONCHAIN_FALLBACK = {
    "mvrv_ratio": 1.0,
    "ath_distance_pct": 50.0,
    "volatility_30d": 10.0,
}


def _state(**overrides) -> dict:
    state = {
        "symbol": "BTCUSDT",
        "current_price": 67000.0,
        "timeframe": "SWING",
        "regime": "NORMAL",
    }
    state.update(overrides)
    return state


def _mocked_agent(metadata: dict, onchain: dict) -> FundamentalAgent:
    """Agent whose two CoinGecko helpers are replaced by offline mocks."""
    agent = FundamentalAgent()
    agent._fetch_crypto_metadata = AsyncMock(return_value=metadata)
    agent._fetch_onchain_data = AsyncMock(return_value=onchain)
    return agent


def _response_mock(payload: dict, status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status = status
    resp.json = AsyncMock(return_value=payload)
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    return resp


def _session_mock(resp: MagicMock) -> MagicMock:
    session = MagicMock()
    session.get = MagicMock(return_value=resp)
    session.close = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    return session


# ── 1. BaseAgent inheritance and identity ───────────────────────────────


def test_agent_is_a_base_agent_subclass():
    assert issubclass(FundamentalAgent, BaseAgent)
    agent = FundamentalAgent()
    assert isinstance(agent, BaseAgent)
    assert agent.name == "FundamentalAgent"
    assert agent.domain == "fundamental"
    assert agent.weight == 0.12


def test_create_factory_returns_fundamental_agent():
    assert isinstance(_mod.create(), FundamentalAgent)


# ── 2. run(state) -> AgentResponse ──────────────────────────────────────


async def test_run_returns_agent_response_on_valid_state():
    agent = _mocked_agent(
        metadata={"market_cap_rank": 1, "price_change_24h": 1.5},
        onchain={"mvrv_ratio": 0.5, "ath_distance_pct": 80.0, "volatility_30d": 12.0},
    )
    with patch(_EPHEMERIS_FLAG, True):
        result = await agent.run(_state())

    assert isinstance(result, AgentResponse)
    assert result.agent_name == "FundamentalAgent"
    assert result.signal is SignalDirection.LONG
    assert result.confidence == 82
    assert set(result.metadata) == {"valuation", "earnings", "growth", "onchain"}
    assert result.metadata["onchain"]["mvrv_ratio"] == 0.5


@pytest.mark.parametrize(
    ("mvrv", "ath_distance", "expected"),
    [
        (0.5, 50.0, SignalDirection.LONG),
        (2.5, 50.0, SignalDirection.SHORT),
        (1.5, 50.0, SignalDirection.NEUTRAL),
    ],
)
async def test_signal_direction_follows_valuation_score(mvrv, ath_distance, expected):
    agent = _mocked_agent(
        metadata={"market_cap_rank": 20, "price_change_24h": 0.0},
        onchain={
            "mvrv_ratio": mvrv,
            "ath_distance_pct": ath_distance,
            "volatility_30d": 10.0,
        },
    )
    with patch(_EPHEMERIS_FLAG, True):
        result = await agent.run(_state())

    assert result.signal is expected
    assert 0 <= result.confidence <= 100


async def test_confidence_and_reasoning_are_deterministic():
    metadata = {"market_cap_rank": 5, "price_change_24h": 2.0}
    onchain = {"mvrv_ratio": 0.5, "ath_distance_pct": 50.0, "volatility_30d": 3.0}

    agent = _mocked_agent(dict(metadata), dict(onchain))
    with patch(_EPHEMERIS_FLAG, True):
        first = await agent.run(_state())
        second = await agent.run(_state())

    assert first.signal is second.signal is SignalDirection.LONG
    assert first.confidence == second.confidence == 75
    assert first.reasoning == second.reasoning
    assert "MVRV 0.50" in first.reasoning
    assert first.metadata["earnings"]["score"] == 0.65
    assert first.metadata["growth"]["score"] == 0.60


# ── 3. degradation paths ────────────────────────────────────────────────


async def test_run_degrades_when_ephemeris_is_unavailable():
    agent = FundamentalAgent()
    with patch(_EPHEMERIS_FLAG, False):
        result = await agent.run(_state())

    assert isinstance(result, AgentResponse)
    assert result.signal is SignalDirection.NEUTRAL
    assert result.confidence == 0
    assert result.metadata["degraded"] is True
    assert result.metadata["degradation_reason"] == EPHEMERIS_UNAVAILABLE
    assert result.sources == []


async def test_run_degrades_on_unexpected_agent_error():
    agent = FundamentalAgent()
    with (
        patch(_EPHEMERIS_FLAG, True),
        patch.object(agent, "analyze", new=AsyncMock(side_effect=RuntimeError("boom"))),
    ):
        result = await agent.run(_state())

    assert result.signal is SignalDirection.NEUTRAL
    assert result.confidence == 0
    assert result.metadata["degraded"] is True
    assert result.metadata["degradation_reason"] == UNKNOWN
    assert "boom" in result.reasoning


# ── 4. offline fetch fallbacks ──────────────────────────────────────────


async def test_fetch_crypto_metadata_falls_back_without_network():
    agent = FundamentalAgent()
    session = MagicMock()
    session.get = MagicMock(side_effect=OSError("network down"))
    session.close = AsyncMock()

    with patch(_CLIENT_SESSION, return_value=session):
        data = await agent._fetch_crypto_metadata("BTCUSDT")

    assert data == {"market_cap_rank": 999}


async def test_fetch_onchain_data_falls_back_and_closes_session():
    agent = FundamentalAgent()
    session = MagicMock()
    session.get = MagicMock(side_effect=OSError("network down"))
    session.close = AsyncMock()

    with patch(_CLIENT_SESSION, return_value=session):
        data = await agent._fetch_onchain_data("BTCUSDT")

    assert data == _ONCHAIN_FALLBACK
    session.close.assert_awaited_once()
    assert agent._session is None


async def test_fetch_onchain_data_computes_metrics_from_prices():
    agent = FundamentalAgent()
    resp = _response_mock({"prices": [[1, 100.0], [2, 200.0], [3, 150.0]]})
    session = _session_mock(resp)

    with patch(_CLIENT_SESSION, return_value=session):
        data = await agent._fetch_onchain_data("BTCUSDT")

    assert data["mvrv_ratio"] == round(150.0 / ((100.0 + 200.0 + 150.0) / 3), 2)
    assert data["ath_distance_pct"] == round((200.0 - 150.0) / 200.0 * 100, 1)
    assert data["volatility_30d"] == round((200.0 - 100.0) / 150.0 * 100, 1)
    assert session.get.call_count == 1
    session.close.assert_awaited_once()


# ── 5. no module-level state, no leakage between calls ──────────────────


def test_removed_module_level_cache_stays_removed():
    for symbol in (
        "_CACHE",
        "_CACHE_TTL",
        "_cache_get",
        "_cache_set",
        "_fetch_fundamental_data",
    ):
        assert not hasattr(_mod, symbol), f"{symbol} must not exist on the module"


async def test_no_state_leakage_between_instances():
    metadata = {"market_cap_rank": 3, "price_change_24h": 0.5}
    onchain = {"mvrv_ratio": 0.5, "ath_distance_pct": 50.0, "volatility_30d": 8.0}

    async def _run_once():
        agent = _mocked_agent(dict(metadata), dict(onchain))
        with patch(_EPHEMERIS_FLAG, True):
            return await agent.run(_state())

    first = await _run_once()
    second = await _run_once()

    assert first.to_dict()["metadata"] == second.to_dict()["metadata"]
    assert first.signal is second.signal
    assert first.confidence == second.confidence
    assert first.reasoning == second.reasoning


async def test_module_runner_returns_serialised_response():
    stub = AgentResponse(
        agent_name="FundamentalAgent",
        signal=SignalDirection.NEUTRAL,
        confidence=50,
        reasoning="stub",
    )
    with patch.object(FundamentalAgent, "analyze", new=AsyncMock(return_value=stub)):
        payload = await _mod.run_fundamental_agent(_state())

    assert set(payload) == {"fundamental_signal"}
    assert payload["fundamental_signal"]["signal"] == "NEUTRAL"
    assert payload["fundamental_signal"]["agent_name"] == "FundamentalAgent"
