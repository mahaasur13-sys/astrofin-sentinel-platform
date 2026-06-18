from __future__ import annotations

import os
import subprocess
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "tools" / "update_progress.sh"


def run_script():
    result = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@test.com",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@test.com",
        },
    )
    return result.stdout, result.stderr, result.returncode


@pytest.mark.unit
def test_update_progress_script_exists():
    assert SCRIPT.exists(), "tools/update_progress.sh not found"


@pytest.mark.unit
def test_generates_progress_file():
    if not SCRIPT.exists():
        pytest.skip("Script not found")
    # Создадим временный репозиторий
    os.chdir(ROOT)
    subprocess.run(["git", "init"], check=False)
    subprocess.run(["git", "config", "user.email", "test@test.com"], check=False)
    subprocess.run(["git", "config", "user.name", "Test"], check=False)
    # Создадим тестовый файл, чтобы был коммит
    test_file = ROOT / "test_temp.txt"
    test_file.write_text("test")
    subprocess.run(["git", "add", "test_temp.txt"], check=False)
    subprocess.run(["git", "commit", "-m", "Test commit for progress"], check=False)
    # Запустим скрипт
    stdout, stderr, code = run_script()
    # Проверим, что progress.md создался и содержит запись
    progress_file = ROOT / "progress.md"
    assert progress_file.exists(), "progress.md was not created"
    content = progress_file.read_text()
    today = date.today().isoformat()
    assert today in content, "progress.md does not contain today's date"
    assert "Test commit for progress" in content, "progress.md does not contain commit message"
    # Уберем тестовый мусор
    test_file.unlink(missing_ok=True)
    subprocess.run(["git", "rm", "--cached", "test_temp.txt"], capture_output=True)
    subprocess.run(["rm", "-rf", ".git"], check=False)  # Удалим временный git
