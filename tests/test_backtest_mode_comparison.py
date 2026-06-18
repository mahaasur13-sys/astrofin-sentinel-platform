from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "scripts" / "compare_backtest_modes.py"


@pytest.mark.unit
def test_comparison_script_exists():
    assert SCRIPT.exists(), "scripts/compare_backtest_modes.py not found"


@pytest.mark.unit
def test_comparison_script_ci_mode_succeeds():
    """Скрипт с --ci должен отрабатывать и возвращать exit code 0."""
    if not SCRIPT.exists():
        return
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--ci"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        timeout=30,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}\n{result.stdout}"
    assert "comparable" in result.stdout.lower()
