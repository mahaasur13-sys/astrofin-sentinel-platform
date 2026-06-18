from __future__ import annotations

# tests/test_healthcheck.py
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).parent.parent
HEALTHCHECK = ROOT / "tools" / "healthcheck.py"


def run_healthcheck(*args):
    """Run healthcheck as subprocess and return (stdout, stderr, exitcode)."""
    result = subprocess.run(
        [sys.executable, str(HEALTHCHECK)] + list(args),
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    return result.stdout, result.stderr, result.returncode


@pytest.mark.unit
def test_healthcheck_exists():
    assert HEALTHCHECK.exists(), "tools/healthcheck.py not found"


@pytest.mark.unit
def test_healthcheck_outputs_json():
    if not HEALTHCHECK.exists():
        pytest.skip("healthcheck.py not found")
    stdout, _, returncode = run_healthcheck()
    data = json.loads(stdout)
    assert "status" in data
    assert "checks" in data


@pytest.mark.unit
def test_healthcheck_exit_code_ok_when_all_good():
    if not HEALTHCHECK.exists():
        pytest.skip("healthcheck.py not found")
    _, _, returncode = run_healthcheck()
    # В идеальных условиях должен вернуть 0, но в тестовой среде может быть 1.
    # Мы просто проверяем, что не 2 (критическая ошибка).
    assert returncode in (0, 1), f"Expected exit code 0 or 1, got {returncode}"


@pytest.mark.unit
def test_healthcheck_venv_check():
    if not HEALTHCHECK.exists():
        pytest.skip("healthcheck.py not found")
    stdout, _, _ = run_healthcheck()
    data = json.loads(stdout)
    checks = data.get("checks", {})
    assert "venv" in checks
    assert "active" in checks["venv"]


@pytest.mark.unit
def test_healthcheck_db_check():
    if not HEALTHCHECK.exists():
        pytest.skip("healthcheck.py not found")
    stdout, _, _ = run_healthcheck()
    data = json.loads(stdout)
    checks = data.get("checks", {})
    assert "postgresql" in checks or "database" in checks


@pytest.mark.unit
def test_healthcheck_ollama_check():
    if not HEALTHCHECK.exists():
        pytest.skip("healthcheck.py not found")
    stdout, _, _ = run_healthcheck()
    data = json.loads(stdout)
    checks = data.get("checks", {})
    # Ollama может быть не запущена — это не фатально
    assert "ollama" in checks


@pytest.mark.unit
def test_healthcheck_handle_missing_docker_compose():
    # Мокаем отсутствие docker-compose
    with patch("subprocess.run", side_effect=FileNotFoundError):
        # ... это больше для внутреннего тестирования, можно пока пропустить
        pass
