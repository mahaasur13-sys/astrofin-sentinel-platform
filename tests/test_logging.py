from __future__ import annotations

import asyncio
import json

import pytest

from core.logging import get_logger, setup_logging


@pytest.fixture(autouse=True)
def configure_structlog():
    setup_logging()
    yield


@pytest.mark.unit
def test_logger_includes_correlation_id(capsys):
    logger = get_logger("test")
    logger.info("Test event")
    captured = capsys.readouterr()
    assert captured.out, "No log output"
    log_entry = json.loads(captured.out.strip().split("\n")[0])
    assert "correlation_id" in log_entry
    assert log_entry["correlation_id"] == "unknown"


@pytest.mark.unit
def test_orchestrator_sets_correlation_id(capsys):
    from orchestration.sentinel_v5 import run_sentinel_v5

    try:
        asyncio.run(run_sentinel_v5("Analyze BTC", "BTCUSDT", "SWING"))
    except Exception:
        pass
    captured = capsys.readouterr()
    assert captured.out, "No log output from orchestrator"
    log_lines = [json.loads(line) for line in captured.out.strip().split("\n") if line]
    correlation_ids = {entry["correlation_id"] for entry in log_lines if "correlation_id" in entry}
    assert len(correlation_ids) > 0, "No correlation_id found in logs"
    assert "unknown" not in correlation_ids, "correlation_id should not be 'unknown'"
    assert len(correlation_ids) == 1, f"Multiple correlation ids found: {correlation_ids}"
