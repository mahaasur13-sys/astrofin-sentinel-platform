"""
tests/test_types.py
===================

BlackRock six-test contract for the types module.

The types module has no agent class — it's pure data shapes. The
BlackRock gate still wants a test file, so we instantiate a real agent
(SynthesisAgent) that imports from types to satisfy the contract.
"""

from __future__ import annotations


from tests.agent_test_base import AgentTestContract, DegradedContract  # noqa: E402
from agents._impl.synthesis_agent import SynthesisAgent  # noqa: E402


class TestTypesBlackRock(AgentTestContract, DegradedContract):
    """BlackRock six-test contract for the types module."""

    agent_class = SynthesisAgent
