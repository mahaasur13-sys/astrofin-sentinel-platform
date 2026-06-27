"""
BlackRock Six Tests for MacroAgent.

Inherits from AgentTestContract + DegradedContract for full coverage.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents._impl.macro_agent import MacroAgent
from tests.agent_test_base import AgentTestContract, DegradedContract


class TestMacroAgent(AgentTestContract, DegradedContract):
    agent_class = MacroAgent
