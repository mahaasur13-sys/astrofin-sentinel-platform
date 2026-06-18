from __future__ import annotations

from pathlib import Path

import pytest
ROOT = Path(__file__).parent.parent


@pytest.mark.unit
def test_cursorrules_exists():
    assert (ROOT / ".cursorrules").exists(), ".cursorrules not found"


@pytest.mark.unit
def test_claude_md_exists():
    assert (ROOT / "CLAUDE.md").exists(), "CLAUDE.md not found"


@pytest.mark.unit
def test_cursorrules_references_agents_md():
    content = (ROOT / ".cursorrules").read_text()
    assert "AGENTS.md" in content, ".cursorrules should reference AGENTS.md"


@pytest.mark.unit
def test_claude_md_references_agents_md():
    content = (ROOT / "CLAUDE.md").read_text()
    assert "AGENTS.md" in content, "CLAUDE.md should reference AGENTS.md"
