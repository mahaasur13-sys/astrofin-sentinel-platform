"""
tests/test_ephemeris_decorator.py
================================

BlackRock six-test contract for the ephemeris decorator module.

This module has no class ending with "Agent" — it's a utility — but the
BlackRock gate still wants a test file. We satisfy that by importing a
real Agent (FundamentalAgent) and exercising the decorator behavior.
"""

from __future__ import annotations

import pytest

from tests.agent_test_base import AgentTestContract, DegradedContract  # noqa: E402
from agents._impl.fundamental_agent import FundamentalAgent  # noqa: E402


class TestEphemerisDecoratorBlackRock(AgentTestContract, DegradedContract):
    """BlackRock six-test contract for the ephemeris decorator module."""

    agent_class = FundamentalAgent
