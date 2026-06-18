from __future__ import annotations

import re
from pathlib import Path


import pytest
@pytest.mark.unit
def test_agents_md_has_ai_rules_section():
    """AGENTS.md должен содержать секцию 'AI Agent Rules'."""
    root = Path(__file__).parent.parent
    agents_md = root / "AGENTS.md"
    assert agents_md.exists(), "AGENTS.md not found"
    content = agents_md.read_text(encoding="utf-8")
    assert "AI Agent Rules" in content, "Missing 'AI Agent Rules' header"
    # Проверяем, что после заголовка идут правила (ненулевое количество пунктов)
    rules_section = content.split("AI Agent Rules")[1]
    rules = re.findall(r"^\d+\.\s", rules_section, re.MULTILINE)
    assert len(rules) >= 3, f"Expected at least 3 rules, found {len(rules)}"


@pytest.mark.unit
def test_agents_md_references_healthcheck():
    content = (Path(__file__).parent.parent / "AGENTS.md").read_text()
    assert "healthcheck" in content.lower(), "AGENTS.md should mention healthcheck"


@pytest.mark.unit
def test_agents_md_warns_archived_modules():
    content = (Path(__file__).parent.parent / "AGENTS.md").read_text()
    assert "_archived" in content, "Should warn about archived modules"
