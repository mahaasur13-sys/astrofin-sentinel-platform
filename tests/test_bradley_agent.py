"""
tests/test_bradley_agent.py
============================

BlackRock six-test contract for BradleyAgent.

Inherits six required tests from :class:`AgentTestContract`:
  test_happy_path, test_empty_state, test_malformed_state,
  test_data_source_unavailable, test_missing_ephemeris, test_large_input.

Class attribute `agent_class` tells the mixin which agent to instantiate.
"""

from __future__ import annotations

import pytest

from tests.agent_test_base import AgentTestContract, DegradedContract  # noqa: E402
from agents._impl.bradley_agent import BradleyAgent  # noqa: E402


class TestBradleyAgentBlackRock(AgentTestContract, DegradedContract):
    """BlackRock six-test contract for BradleyAgent."""

    agent_class = BradleyAgent
