"""Tests for metrics bind + bearer-token authz (T5)."""

from __future__ import annotations

import pytest

from orchestration.sentinel_v5 import (
    _build_metrics_app,
    _metrics_bind_host,
    _metrics_fail_closed,
    _read_metrics_token,
    _start_metrics_server,
)


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


def test_read_metrics_token_from_env(monkeypatch):
    monkeypatch.setenv("METRICS_TOKEN", "from-env")
    monkeypatch.delenv("METRICS_TOKEN_FILE", raising=False)
    assert _read_metrics_token() == "from-env"


def test_read_metrics_token_from_file(monkeypatch, tmp_path):
    monkeypatch.delenv("METRICS_TOKEN", raising=False)
    f = tmp_path / "token"
    f.write_text("from-file\n")
    monkeypatch.setenv("METRICS_TOKEN_FILE", str(f))
    assert _read_metrics_token() == "from-file"


def test_read_metrics_token_env_wins_over_file(monkeypatch, tmp_path):
    monkeypatch.setenv("METRICS_TOKEN", "env-wins")
    f = tmp_path / "token"
    f.write_text("file\n")
    monkeypatch.setenv("METRICS_TOKEN_FILE", str(f))
    assert _read_metrics_token() == "env-wins"


def test_metrics_fail_closed_bind_all_no_token():
    with pytest.raises(RuntimeError):
        _metrics_fail_closed("0.0.0.0", "")


def test_metrics_fail_closed_loopback_no_token_ok():
    _metrics_fail_closed("127.0.0.1", "")  # must not raise


def test_metrics_fail_closed_bind_all_with_token_ok():
    _metrics_fail_closed("0.0.0.0", "sekrit")  # must not raise


def test_start_metrics_bind_all_no_token_raises(monkeypatch):
    monkeypatch.setenv("METRICS_BIND_ALL", "true")
    monkeypatch.delenv("METRICS_TOKEN", raising=False)
    monkeypatch.delenv("METRICS_TOKEN_FILE", raising=False)
    with pytest.raises(RuntimeError):
        _start_metrics_server()


def test_start_metrics_bind_all_empty_file_raises(monkeypatch, tmp_path):
    monkeypatch.setenv("METRICS_BIND_ALL", "true")
    monkeypatch.delenv("METRICS_TOKEN", raising=False)
    f = tmp_path / "token"
    f.write_text("")
    monkeypatch.setenv("METRICS_TOKEN_FILE", str(f))
    with pytest.raises(RuntimeError):
        _start_metrics_server()
