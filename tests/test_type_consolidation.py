from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent


@pytest.mark.unit
def test_no_duplicate_agent_response_imports():
    """Везде должен использоваться AgentResponse из core.base_agent, а не agents._impl.types."""
    violations = []
    for py_file in ROOT.rglob("*.py"):
        if "venv" in py_file.parts or "__pycache__" in py_file.parts:
            continue
        content = py_file.read_text(errors="ignore")
        if "from agents._impl.types import" in content or "import agents._impl.types" in content:
            # Проверяем, импортируется ли AgentResponse из дубликата
            if "AgentResponse" in content.split("import")[1]:
                violations.append(str(py_file))
    assert len(violations) == 0, f"Found duplicate imports in: {violations}"
