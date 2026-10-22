#!/usr/bin/env python3
"""OffsiteStateCollector: pgdump_offsite_* только когда offsite_state.json валиден."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_EXPORTER = Path(__file__).resolve().parent.parent / "scripts" / "metrics_exporter.py"


@pytest.fixture(scope="module")
def exporter():
    spec = importlib.util.spec_from_file_location("metrics_exporter_offsite", _EXPORTER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _families(exporter, tmp_path, payload=None, raw=None):
    state = tmp_path / "offsite_state.json"
    if raw is not None:
        state.write_text(raw)
    elif payload is not None:
        state.write_text(json.dumps(payload))
    exporter.OFFSITE_STATE_FILE = state
    return {f.name: f.samples[0].value for f in exporter.OffsiteStateCollector().collect()}


def test_ok_state_exports_both_gauges(exporter, tmp_path):
    got = _families(
        exporter,
        tmp_path,
        {"last_success_ts": 1792560001, "last_result": "ok", "bytes": 307865},
    )
    assert got["pgdump_offsite_last_success_timestamp"] == pytest.approx(1792560001.0)
    assert got["pgdump_offsite_last_result"] == 1.0


def test_failed_result_exports_zero(exporter, tmp_path):
    got = _families(
        exporter,
        tmp_path,
        {"last_success_ts": 1792560001, "last_result": "fail", "bytes": 0},
    )
    assert got["pgdump_offsite_last_result"] == 0.0
    assert got["pgdump_offsite_last_success_timestamp"] == pytest.approx(1792560001.0)


def test_missing_file_exports_no_series(exporter, tmp_path):
    assert _families(exporter, tmp_path) == {}


def test_bad_json_exports_no_series(exporter, tmp_path):
    assert _families(exporter, tmp_path, raw="{not json") == {}


def test_state_without_timestamp_exports_no_series(exporter, tmp_path):
    assert _families(exporter, tmp_path, {"last_result": "ok"}) == {}
