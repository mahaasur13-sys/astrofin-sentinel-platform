import pytest


@pytest.mark.unit
def test_quant_agent_no_sync_requests():
    """Проверяем, что quant_agent.py больше не использует синхронный requests."""
    import ast
    import pathlib

    code = pathlib.Path("agents/_impl/quant_agent.py").read_text()
    tree = ast.parse(code)
    imports = [node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)]
    imports_from = [
        f"{node.module}.{alias.name}"
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    ]
    assert "requests" not in imports
    assert not any(i.startswith("requests.") for i in imports_from)
    # Также не должно быть прямого вызова requests.get
    assert "requests.get" not in code
