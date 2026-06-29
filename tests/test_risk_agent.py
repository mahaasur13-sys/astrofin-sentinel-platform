"""
tests/test_risk_agent.py
============================

BlackRock six-test contract for RiskAgent.

Inherits six required tests from :class:`AgentTestContract`:
  test_happy_path, test_empty_state, test_malformed_state,
  test_data_source_unavailable, test_missing_ephemeris, test_large_input.

Class attribute `agent_class` tells the mixin which agent to instantiate.
"""

from __future__ import annotations


from tests.agent_test_base import AgentTestContract, DegradedContract  # noqa: E402
from agents._impl.risk_agent import RiskAgent  # noqa: E402


class TestRiskAgentBlackRock(AgentTestContract, DegradedContract):
    """BlackRock six-test contract for RiskAgent."""

    agent_class = RiskAgent
