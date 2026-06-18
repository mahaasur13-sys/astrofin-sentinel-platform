"""
tests/architecture/test_validate_agent.py
=========================================
Tests for the per-agent validator.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "scripts" / "validate_agent.py"

sys.path.insert(0, str(REPO_ROOT / "scripts"))


def test_validator_passes_on_template():
    """The template is hand-written to pass all 9 checks."""
    rc = subprocess.run(
        [sys.executable, str(VALIDATOR), "agents/_impl/_template_agent.py"],
        capture_output=True, text=True, check=False,
    )
    assert rc.returncode == 0
    assert "9 / 9 checks passed" in rc.stdout


def test_validator_rejects_class_without_base(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text('''
class NotAnAgent:
    pass
''')
    rc = subprocess.run(
        [sys.executable, str(VALIDATOR), str(bad)],
        capture_output=True, text=True, check=False,
    )
    assert rc.returncode != 0
    assert "A1" in rc.stdout or "A1" in rc.stderr


def test_validator_rejects_missing_runner_function(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text('''
from core.base_agent import BaseAgent, AgentResponse

class MyAgent(BaseAgent[AgentResponse]):
    def __init__(self):
        super().__init__(name="MyAgent", domain="fundamental")
    async def run(self, state):
        return AgentResponse(agent_name="MyAgent", signal="NEUTRAL", confidence=50, reasoning="")
''')
    rc = subprocess.run(
        [sys.executable, str(VALIDATOR), str(bad)],
        capture_output=True, text=True, check=False,
    )
    assert rc.returncode != 0
    assert "A5" in rc.stdout


def test_validator_reports_ephemeris_without_decorator(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text('''
from core.base_agent import BaseAgent, AgentResponse

class AstroAgent(BaseAgent[AgentResponse]):
    def __init__(self):
        super().__init__(name="AstroAgent", domain="astro")
    async def run(self, state):
        return AgentResponse(agent_name="AstroAgent", signal="NEUTRAL", confidence=50, reasoning="")
    def _internal(self):
        return core.ephemeris.get_planetary_positions(...)
''')
    rc = subprocess.run(
        [sys.executable, str(VALIDATOR), str(bad)],
        capture_output=True, text=True, check=False,
    )
    # Missing @require_ephemeris
    assert "A4" in rc.stdout
