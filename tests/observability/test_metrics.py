"""Smoke tests for observability/metrics.py."""

from __future__ import annotations

import asyncio
import time
import pytest
from observability.metrics import (
    record_agent_run,
    record_data_room_resolve,
    time_block,
    with_agent_timing,
)


def test_record_agent_run_does_not_raise():
    record_agent_run("TestAgent", "LONG", 0.123, 80)


def test_record_data_room_resolve_does_not_raise():
    record_data_room_resolve("price_resolver", "ok", 0.05)
    record_data_room_resolve("price_resolver", "fallback", 0.05)


def test_time_block_measures_elapsed():
    with time_block("test") as elapsed:
        time.sleep(0.01)
    assert elapsed["elapsed"] >= 0.01
    assert elapsed["elapsed"] < 0.5


def test_time_block_records_even_on_exception():
    with pytest.raises(RuntimeError):
        with time_block("test") as elapsed:
            raise RuntimeError("boom")
    assert elapsed["elapsed"] >= 0


def test_with_agent_timing_decorator_passes_through():
    @with_agent_timing("DecoratedAgent", signal_getter=lambda r: "LONG", confidence_getter=lambda r: 75)
    async def fake_run(state):
        return {"signal": "LONG", "confidence": 75}

    result = asyncio.run(fake_run({"x": 1}))
    assert result == {"signal": "LONG", "confidence": 75}
