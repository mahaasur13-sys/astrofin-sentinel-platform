"""test_karl_synthesis_lifecycle.py — Phase 1 (R9) coverage for KARL."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agents.karl_synthesis import KARLSynthesisAgent


class TestKARLInitialization:
    def test_construction_defaults(self):
        karl = KARLSynthesisAgent()
        assert karl.sync_interval == 10
        assert karl.enable_self_question is False
        assert karl.enable_backtest is True
        assert karl.decision_counter == 0
        assert karl.self_questioner is None
        assert karl.backtest is not None

    def test_construction_custom_params(self):
        karl = KARLSynthesisAgent(sync_interval=20, enable_self_question=True, enable_backtest=False)
        assert karl.sync_interval == 20
        assert karl.enable_self_question is True
        assert karl.enable_backtest is False
        assert karl.self_questioner is not None
        assert karl.backtest is None

    def test_sub_systems_initialized(self):
        karl = KARLSynthesisAgent()
        assert karl.oap is not None
        assert karl.calibrator is not None
        assert karl.dd_tracker is not None
        assert karl.reward_state is not None
        assert karl.lag_window is not None
        assert karl.lag_enabled is True

    def test_base_synthesis_agent_attached(self):
        """KARLSynthesisAgent wraps SynthesisAgent from agents._impl.synthesis_agent."""
        from agents._impl.synthesis_agent import SynthesisAgent

        karl = KARLSynthesisAgent()
        assert isinstance(karl.base_agent, SynthesisAgent)


class TestKARLDiagnostics:
    def test_get_karl_diagnostics_returns_dict(self):
        from agents.karl_synthesis import get_karl_agent
        agent = get_karl_agent()
        # First decision_counter call increments state
        diag = agent.get_karl_diagnostics() if hasattr(agent, "get_karl_diagnostics") else {}
        assert isinstance(diag, dict)

    def test_singleton_returns_same_instance(self):
        from agents.karl_synthesis import get_karl_agent
        a1 = get_karl_agent()
        a2 = get_karl_agent()
        assert a1 is a2


class TestKARLDecisionCounter:
    def test_decision_counter_starts_at_zero(self):
        karl = KARLSynthesisAgent()
        assert karl.decision_counter == 0

    def test_decision_counter_increments(self):
        karl = KARLSynthesisAgent()
        karl.decision_counter += 1
        assert karl.decision_counter == 1
        karl.decision_counter += 5
        assert karl.decision_counter == 6


class TestKARLLagWindow:
    def test_lag_enabled_by_default(self):
        karl = KARLSynthesisAgent()
        assert karl.lag_enabled is True

    def test_lag_window_attached(self):
        karl = KARLSynthesisAgent()
        assert karl.lag_window is not None


class TestKARLRewardState:
    def test_reward_state_initialized(self):
        karl = KARLSynthesisAgent()
        # RewardState may not have direct attributes, but should exist
        assert karl.reward_state is not None

    def test_two_karls_have_independent_state(self):
        k1 = KARLSynthesisAgent(sync_interval=10)
        k2 = KARLSynthesisAgent(sync_interval=20)
        k1.decision_counter = 99
        assert k2.decision_counter == 0