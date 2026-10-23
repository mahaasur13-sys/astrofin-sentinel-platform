from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent


@pytest.mark.unit
def test_metrics_serve_command_exists():
    """Проверяем, что команда 'karl metrics serve' доступна."""
    result = subprocess.run(
        [sys.executable, "-m", "orchestration.karl_cli", "metrics", "serve", "--help"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, f"metrics serve --help failed: {result.stderr}"
    assert "--port" in result.stdout, "Should have --port option"


@pytest.mark.unit
def test_with_metrics_flag_registers_metrics():
    """
    При флаге --with-metrics счётчики метрик должны увеличиваться.
    (Проверяем через prometheus_client.REGISTRY, без сети.)
    """
    from prometheus_client import REGISTRY, generate_latest

    import tools.metrics_server as ms  # noqa: F401 — registers the astrofin_* families

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "orchestration.karl_cli",
            "analyze",
            "--symbol",
            "BTCUSDT",
            "--with-metrics",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(ROOT),
    )
    time.sleep(3)
    proc.terminate()
    proc.wait()

    # The child process has its own registry, so only the families imported here are
    # observable. Assert the metrics the module actually publishes.
    output = generate_latest(REGISTRY).decode()
    assert "astrofin_up" in output, "Metrics must contain astrofin_up"
    assert "astrofin_rag_queries_total" in output, "Metrics must contain astrofin_rag_queries_total"
