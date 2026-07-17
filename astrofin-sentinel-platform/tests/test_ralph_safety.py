from __future__ import annotations

import os
import tempfile

import pytest

from scripts.ralph_agent import (
    check_protected_files_in_diff,
    is_protected_file,
    log_audit,
)


@pytest.mark.unit
def test_is_protected_file():
    assert is_protected_file("docker-compose.yml")
    assert is_protected_file(".env")
    assert is_protected_file("core/tracing.py")
    assert not is_protected_file("orchestration/sentinel_v5.py")
    assert not is_protected_file("README.md")


@pytest.mark.unit
def test_log_audit():
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        log_audit(f.name, "test_task", "LLM ответ", "OK")
        f.close()
        with open(f.name) as fr:
            content = fr.read()
        assert "test_task" in content
        assert "LLM ответ" in content
        assert "OK" in content
    os.unlink(f.name)


@pytest.mark.unit
def test_check_protected_files_in_diff(monkeypatch):
    # Симулируем вывод git diff --name-only с защищённым файлом
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: type(
            "res", (), {"stdout": "docker-compose.yml\nother_file.py", "returncode": 0}
        ),
    )
    result = check_protected_files_in_diff()
    assert result is False  # Функция должна вернуть False, если есть защищённый файл
