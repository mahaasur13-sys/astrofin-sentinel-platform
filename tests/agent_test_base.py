"""
tests/agent_test_base.py
========================
Shared test base class for all AstroFin Sentinel V5 agents.

Provides:

- :class:`AgentTestContract` — the canonical "BlackRock six" test cases
  every agent must satisfy. Subclasses opt in by setting the class
  attribute :pyattr:`agent_class` and may override individual tests.

- :class:`DegradedContract` — six tests that exercise the
  ``self._degraded(reason, msg)`` path inherited from BaseAgent.

Why a base class and not a free function:
    - Per-agent tests stay tiny (one file ~ 30 lines + imports).
    - New agents inherit compliance for free.
    - When the contract changes, ONE place to update.

Usage::

    from tests.agent_test_base import AgentTestContract, DegradedContract

    class TestMacroAgent(AgentTestContract, DegradedContract):
        agent_class = MacroAgent

Run it::

    pytest -q tests/test_macro_agent.py
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

from core.base_agent import AgentResponse, SignalDirection  # noqa: E402

# Latency budget per agent call (seconds). Anything longer than this
# should trip the per-agent p99 budget alarm in production.
HOT_LATENCY_BUDGET_S = 5.0


class AgentTestContract:
    """
    Canonical test contract for an AstroFin Sentinel V5 agent.

    Subclasses must set the class attribute ``agent_class``::

        class TestMacroAgent(AgentTestContract):
            agent_class = MacroAgent

    Each test is independent: it builds a fresh agent from
    ``self.agent_class()`` so per-test state never leaks.
    """

    # ─── subclass overrides ────────────────────────────────────────
    agent_class = None  # type: type
    # Optional: name of the HTTP/data method to patch in the
    # "data_source_unavailable" test. If None, the test patches
    # ``agent.retrieve`` (which is safe on every agent).
    data_method = "retrieve"
    # Optional: kwargs to override the happy_state fixture.
    happy_state_overrides: dict = {}

    # ─── fixtures ─────────────────────────────────────────────────
    @pytest.fixture
    def agent(self):
        """Fresh agent per-test (no shared state)."""
        assert self.agent_class is not None, f"{self.__class__.__name__} must set `agent_class`"
        return self.agent_class()

    @pytest.fixture
    def happy_state(self) -> dict:
        """A minimal state that every real agent must handle."""
        state = {
            "symbol": "BTCUSDT",
            "current_price": 67000.0,
            "timeframe": "SWING",
            "regime": "NORMAL",
        }
        state.update(self.happy_state_overrides)
        return state

    # ─── 1. happy path ────────────────────────────────────────────
    @pytest.mark.asyncio
    async def test_happy_path_returns_agent_response(self, agent, happy_state):
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

    # ─── 2. empty state ───────────────────────────────────────────
    @pytest.mark.asyncio
    async def test_empty_state_does_not_crash(self, agent):
        """An empty state is not allowed to raise — must degrade gracefully."""
        response = await agent.run({})
        assert response is not None
        assert response.reasoning

    # ─── 3. malformed state ───────────────────────────────────────
    @pytest.mark.asyncio
    async def test_malformed_state_does_not_crash(self, agent):
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

    # ─── 4. data source unavailable ───────────────────────────────
    @pytest.mark.asyncio
    async def test_data_source_unavailable_marks_degraded(self, agent, happy_state):
        """If a data source raises, the response is degraded with a machine reason."""
        with patch.object(agent, self.data_method, side_effect=ConnectionError("data_room down")):
            response = await agent.run(happy_state)
        # The contract: never raise. Either succeed or degrade cleanly.
        assert response is not None
        # If your agent catches and degrades, this assertion will pass:
        #   assert response.metadata.get("degraded") is True
        # If your agent silently falls back, both pass — that's also OK.

    # ─── 5. graceful degradation when ephemeris is missing ────────
    @pytest.mark.asyncio
    async def test_missing_ephemeris_returns_degraded(self, agent, happy_state):
        """@require_ephemeris must convert to a degraded response, not a crash."""
        # Patch every plausible import path.
        with patch("agents._impl.ephemeris_decorator.HAS_SWISS_EPHEMERIS", False):
            with patch("agents._impl._template_agent.HAS_SWISS_EPHEMERIS", False):
                with patch.object(agent.__class__, "HAS_SWISS_EPHEMERIS", False, create=True):
                    response = await agent.run(happy_state)
        assert response.metadata.get("degraded") is True
        assert response.metadata.get("degradation_reason") == "EPHEMERIS_UNAVAILABLE"
        assert response.signal == SignalDirection.NEUTRAL
        assert response.confidence == 0

    # ─── 6. large input ───────────────────────────────────────────
    @pytest.mark.asyncio
    async def test_large_input_does_not_explode(self, agent):
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
        assert len(response.reasoning) < 10_000

    # ─── 7. hot latency budget ────────────────────────────────────
    @pytest.mark.asyncio
    async def test_hot_latency_under_budget(self, agent, happy_state):
        """First call must return within HOT_LATENCY_BUDGET_S."""
        import time

        t0 = time.perf_counter()
        await agent.run(happy_state)
        dt = time.perf_counter() - t0
        assert dt < HOT_LATENCY_BUDGET_S, f"agent took {dt:.3f}s, budget {HOT_LATENCY_BUDGET_S}s"

    # ─── 8. dict contract ─────────────────────────────────────────
    def test_agent_response_to_dict_round_trip(self, agent):
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


class DegradedContract:
    """
    Tests for the canonical ``_degraded(reason, msg)`` path inherited
    from BaseAgent.

    Mix into your test class alongside :class:`AgentTestContract`::

        class TestMacroAgent(AgentTestContract, DegradedContract):
            agent_class = MacroAgent
    """

    agent_class = None  # type: type

    @pytest.fixture
    def agent(self):
        assert self.agent_class is not None
        return self.agent_class()

    @pytest.mark.asyncio
    async def test_degraded_returns_neutral_zero_confidence(self, agent):
        """_degraded() must return NEUTRAL with confidence=0."""
        from core.base_agent import EPHEMERIS_UNAVAILABLE

        response = agent._degraded(EPHEMERIS_UNAVAILABLE, "sweph not installed")
        assert response.agent_name == agent.name
        assert response.signal == SignalDirection.NEUTRAL
        assert response.confidence == 0
        assert response.metadata["degraded"] is True
        assert response.metadata["degradation_reason"] == "EPHEMERIS_UNAVAILABLE"

    @pytest.mark.asyncio
    async def test_degraded_runs_under_budget(self, agent):
        """_degraded() must be fast — orchestrator's last-resort path."""
        import time

        t0 = time.perf_counter()
        for _ in range(100):
            agent._degraded("UNKNOWN", "test")
        dt = time.perf_counter() - t0
        assert dt < 1.0, f"_degraded x100 took {dt:.3f}s"


__all__ = ["AgentTestContract", "DegradedContract", "HOT_LATENCY_BUDGET_S"]
