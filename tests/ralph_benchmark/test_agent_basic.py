from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(reason="Requires external Ralph agent")
"""Бенчмарк для Ralph Loop – минимальная задача, которую агент должен решить."""

import os
import subprocess
import sys
import pytest

BENCHMARK_DIR = os.path.dirname(__file__)
TARGET_FILE = os.path.join(BENCHMARK_DIR, "_temp_add.py")
TEST_FILE = os.path.join(BENCHMARK_DIR, "_test_temp_add.py")


@pytest.fixture(autouse=True)
def cleanup():
    """Удаляем временные файлы до и после теста."""
    for f in (TARGET_FILE, TEST_FILE):
        if os.path.exists(f):
            os.remove(f)
    yield
    for f in (TARGET_FILE, TEST_FILE):
        if os.path.exists(f):
            os.remove(f)


def test_agent_can_create_add_function():
    """Проверяем, что после Ralph Loop агент создал нужный файл."""
    # 1. Подготовить тестовый файл, который упадет без функции add
    with open(TEST_FILE, "w") as f:
        f.write("""
from _temp_add import add

def test_add():
    assert add(2, 3) == 5
""")
    # 2. Запустить Ralph Loop с задачей (только одна итерация)
    task = f"Создай файл {TARGET_FILE} с функцией add(a, b), которая возвращает сумму a+b. Затем убедись, что pytest {TEST_FILE} проходит."  # noqa: E501
    env = os.environ.copy()
    env["VSELM_API_KEY"] = os.getenv("VSELM_API_KEY", "sk-TEST")  # подставь реальный ключ при необходимости
    subprocess.run(
        [sys.executable, "scripts/ralph_agent.py", task],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=os.path.join(os.path.dirname(__file__), "..", ".."),
        env=env,
    )
    # 3. Проверить, что файл создался и pytest проходит
    assert os.path.exists(TARGET_FILE), f"Агент не создал {TARGET_FILE}"
    pytest_result = subprocess.run(
        [sys.executable, "-m", "pytest", TEST_FILE, "-v"],
        capture_output=True,
        text=True,
        cwd=os.path.join(os.path.dirname(__file__), "..", ".."),
    )
    assert pytest_result.returncode == 0, f"pytest упал:\n{pytest_result.stdout}\n{pytest_result.stderr}"
