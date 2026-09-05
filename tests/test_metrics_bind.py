"""Tests for metrics bind + bearer-token authz (T5)."""

from __future__ import annotations

import pytest

from orchestration.sentinel_v5 import _build_metrics_app, _metrics_bind_host


def _call(app, headers=None):
    status = {}

    def start_response(s, h, exc_info=None):
        status["s"] = s

    environ = {"REQUEST_METHOD": "GET", "PATH_INFO": "/metrics"}
    environ.update(headers or {})
    body = app(environ, start_response)
    return status["s"], body


def test_metrics_bind_defaults_to_loopback(monkeypatch):
    monkeypatch.delenv("METRICS_BIND_ALL", raising=False)
    assert _metrics_bind_host() == "127.0.0.1"


def test_metrics_bind_all_requires_flag(monkeypatch):
    monkeypatch.setenv("METRICS_BIND_ALL", "true")
    assert _metrics_bind_host() == "0.0.0.0"
    monkeypatch.setenv("METRICS_BIND_ALL", "1")
    assert _metrics_bind_host() == "0.0.0.0"


def test_metrics_no_token_is_open():
    status, _ = _call(_build_metrics_app(""))
    assert status.startswith("200")


def test_metrics_token_required():
    app = _build_metrics_app("sekrit")

    status, _ = _call(app)
    assert status == "401 Unauthorized"

    status, _ = _call(app, {"HTTP_AUTHORIZATION": "Bearer sekrit"})
    assert status.startswith("200")

    status, _ = _call(app, {"HTTP_AUTHORIZATION": "Bearer wrong"})
    assert status == "401 Unauthorized"
