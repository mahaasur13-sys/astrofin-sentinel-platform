import sys
from pathlib import Path

import pytest
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


@pytest.mark.unit
def test_metrics_server_exists():
    assert (ROOT / "tools" / "metrics_server.py").exists(), "tools/metrics_server.py not found"


@pytest.mark.unit
def test_metrics_are_registered():
    """Проверяем, что метрики с префиксом astrofin_ регистрируются."""
    from prometheus_client import REGISTRY, generate_latest

    import tools.metrics_server as ms

    # Увеличим тестовый счётчик
    ms.REQUEST_COUNT.inc()
    output = generate_latest(REGISTRY).decode()
    assert "astrofin_requests_total" in output
    assert "astrofin_broker_errors_total" in output
    assert "astrofin_ollama_available" in output
