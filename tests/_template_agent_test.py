"""
tests/_template_agent_test.py
==============================
Canonical test template for a new AstroFin Sentinel V5 agent.

Required test cases (the "BlackRock six"):
    1. happy_path
    2. empty_state
    3. malformed_state
    4. data_source_unavailable
    5. missing_ephemeris (graceful degradation)
    6. large_input

The template ships with 6 working tests for the TemplateAgent. When you
copy it, change:
    - the import
    - the agent construction (TemplateAgent() -> MyNewAgent())
    - any agent-specific assertions

Run it:
    pytest -q tests/_template_agent_test.py
    pytest -q tests/_template_agent_test.py --cov=agents._impl._template_agent --cov-report=term-missing
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Make repo importable when running pytest from project root
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents._impl._template_agent import TemplateAgent, run_template_agent  # noqa: E402
from core.base_agent import AgentResponse, SignalDirection  # noqa: E402

# ─── fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def agent() -> TemplateAgent:
    """Fresh agent per-test (no shared state)."""
    return TemplateAgent()


@pytest.fixture
def happy_state() -> dict:
    """A minimal state that every real agent must handle."""
    return {
        "symbol": "BTCUSDT",
        "current_price": 67000.0,
        "timeframe": "SWING",
        "regime": "NORMAL",
    }


# ─── 1. happy path ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_happy_path_returns_agent_response(
    agent: TemplateAgent, happy_state: dict
) -> None:
    """A well-formed state must produce a fully-populated AgentResponse."""
    response = await agent.run(happy_state)
    assert isinstance(response, AgentResponse)
    assert response.agent_name == agent.name
    assert response.signal in {
        SignalDirection.LONG,
        SignalDirection.SHORT,
        SignalDirection.NEUTRAL,
        SignalDirection.AVOID,
    }
    assert 0 <= response.confidence <= 100
    assert response.reasoning  # non-empty
    assert response.session_id  # uuid-prefixed, non-empty


@pytest.mark.asyncio
async def test_run_via_convenience_function(happy_state: dict) -> None:
    """The convenience function must work without explicit instantiation."""
    response = await run_template_agent(happy_state)
    assert response.agent_name == "TemplateAgent"


# ─── 2. empty state ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_empty_state_does_not_crash(agent: TemplateAgent) -> None:
    """An empty state is not allowed to raise — must degrade gracefully."""
    response = await agent.run({})
    assert response is not None
    # We do not assert on signal/confidence because policy differs per agent;
    # the contract is "do not raise".
    assert response.reasoning  # some human-readable explanation must exist


# ─── 3. malformed state ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_malformed_state_does_not_crash(agent: TemplateAgent) -> None:
    """Wrong types in known fields must not raise."""
    bad_state = {
        "symbol": None,
        "current_price": "not-a-number",
        "timeframe": 12345,
        "regime": "UNKNOWN",
    }
    response = await agent.run(bad_state)
    assert response is not None
    assert response.reasoning


# ─── 4. data source unavailable ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_data_source_unavailable_marks_degraded(
    agent: TemplateAgent, happy_state: dict
) -> None:
    """If a data source raises, the response is degraded with a machine reason."""
    # TODO: replace the patch target with the function your agent actually calls.
    # For the template, we just confirm the degraded() path works.
    with patch.object(agent, "retrieve", side_effect=ConnectionError("data_room down")):
        response = await agent.run(happy_state)
    # The template doesn't depend on retrieve(); it should still succeed.
    # If your agent DOES depend on a source, change the assertion to:
    #   assert response.metadata.get("degraded") is True
    #   assert "DATA_ROOM_TIMEOUT" in response.metadata.get("degradation_reason", "")
    assert response is not None


# ─── 5. graceful degradation when ephemeris is missing ──────────────────────


@pytest.mark.asyncio
async def test_missing_ephemeris_returns_degraded(
    agent: TemplateAgent, happy_state: dict
) -> None:
    """@require_ephemeris must convert to a degraded response, not a crash."""
    with patch("agents._impl.ephemeris_decorator.HAS_SWISS_EPHEMERIS", False):
        response = await agent.run(happy_state)
    assert response.metadata.get("degraded") is True
    assert response.metadata.get("degradation_reason") == "EPHEMERIS_UNAVAILABLE"
    assert response.signal == SignalDirection.NEUTRAL
    assert response.confidence == 0


# ─── 6. large input ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_large_input_does_not_explode(agent: TemplateAgent) -> None:
    """A 1MB-ish state must complete; the agent must not blow up on size."""
    big_state = {
        "symbol": "BTCUSDT",
        "current_price": 67000.0,
        "timeframe": "SWING",
        "regime": "NORMAL",
        "history": [{"t": i, "p": 67000.0 + i} for i in range(10_000)],
        "rag_context": ["x" * 100] * 5_000,
    }
    response = await agent.run(big_state)
    assert response is not None
    # We allow any signal, but reasoning must remain under a sane size.
    assert len(response.reasoning) < 10_000


# ─── bonus: dict contract ───────────────────────────────────────────────────


def test_agent_response_to_dict_round_trip(agent: TemplateAgent) -> None:
    """to_dict() is the wire format; it must contain every public field."""
    response = AgentResponse(
        agent_name=agent.name,
        signal=SignalDirection.LONG,
        confidence=72,
        reasoning="unit test",
    )
    d = response.to_dict()
    assert d["agent_name"] == agent.name
    assert d["signal"] == "LONG"
    assert d["confidence"] == 72
    assert d["reasoning"] == "unit test"
    assert d["session_id"]


def test_confidence_out_of_range_raises() -> None:
    """The dataclass itself must guard its invariants."""
    with pytest.raises(ValueError):
        AgentResponse(
            agent_name="x",
            signal=SignalDirection.NEUTRAL,
            confidence=200,  # out of range
            reasoning="bad",
        )
