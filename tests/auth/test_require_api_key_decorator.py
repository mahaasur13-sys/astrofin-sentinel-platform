"""Smoke tests for the @require_api_key decorator against the Flask app.

These tests exercise the decorator end-to-end through Flask's test_client
(``web.wsgi.server``) and assert that 401/403/200 responses go through the
shared :func:`core.error_schema.format_error` envelope.

We **do not** re-import :mod:`core.auth` here — its module-level constants
(``API_KEY_AUTH_DISABLED``, ``API_KEY``) are read from the environment at import
time, and ``web.wsgi`` imports it eagerly. So we control auth by setting
the env vars *before* importing ``web.wsgi``.
"""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def wsgi_app(monkeypatch: pytest.MonkeyPatch):
    """Reload ``web.wsgi`` with a fresh API_KEY for each test."""
    monkeypatch.setenv("API_KEY", "test-key-123")
    # ``API_KEY_AUTH_DISABLED`` is the new env var. When unset, the legacy
    # ``REQUIRE_AUTH`` shim is consulted; here we just don't set either so
    # auth stays ON by default.
    monkeypatch.delenv("API_KEY_AUTH_DISABLED", raising=False)
    monkeypatch.delenv("REQUIRE_AUTH", raising=False)

    # Drop cached modules so env vars are read at import time.
    for mod in list(importlib.sys.modules):
        if mod == "web.wsgi" or mod == "core.auth":
            importlib.sys.modules.pop(mod, None)

    import web.wsgi as wsgi

    return wsgi.server


def test_missing_api_key_returns_401(wsgi_app):
    r = wsgi_app.test_client().get("/api/ab/compare", query_string={"sid_a": "a", "sid_b": "b"})
    assert r.status_code == 401
    body = r.get_json()
    assert body["code"] == "UNAUTHORIZED"
    assert "timestamp" in body
    assert "correlation_id" in body


def test_wrong_api_key_returns_403(wsgi_app):
    r = wsgi_app.test_client().get(
        "/api/ab/compare",
        query_string={"sid_a": "a", "sid_b": "b"},
        headers={"X-API-Key": "nope"},
    )
    assert r.status_code == 403
    body = r.get_json()
    assert body["code"] == "FORBIDDEN"


def test_correct_api_key_returns_200(wsgi_app):
    r = wsgi_app.test_client().get(
        "/api/ab/compare",
        query_string={"sid_a": "a", "sid_b": "b"},
        headers={"X-API-Key": "test-key-123"},
    )
    # We don't care about the A/B payload shape here — only that auth passed
    # and the route executed (not a 401/403).
    assert r.status_code == 200, r.get_data(as_text=True)


def test_health_endpoint_is_unprotected(wsgi_app):
    """``/health`` has no ``@require_api_key`` and should always be reachable."""
    r = wsgi_app.test_client().get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_auth_disabled_allows_request(monkeypatch: pytest.MonkeyPatch):
    """When ``API_KEY_AUTH_DISABLED=true`` the decorator must not block the request."""
    monkeypatch.setenv("API_KEY", "ignored-when-disabled")
    monkeypatch.setenv("API_KEY_AUTH_DISABLED", "true")

    for mod in list(importlib.sys.modules):
        if mod == "web.wsgi" or mod == "core.auth":
            importlib.sys.modules.pop(mod, None)

    from web.wsgi import server

    r = server.test_client().get("/api/ab/compare", query_string={"sid_a": "a", "sid_b": "b"})
    assert r.status_code == 200


def test_constant_time_compare_used(monkeypatch: pytest.MonkeyPatch):
    """Sanity check: ``secrets.compare_digest`` is invoked on a wrong key."""
    import secrets as _secrets

    called = {"n": 0}
    orig = _secrets.compare_digest

    def spy(a, b):
        called["n"] += 1
        return orig(a, b)

    monkeypatch.setattr(_secrets, "compare_digest", spy)
    monkeypatch.setenv("API_KEY", "real-key")
    monkeypatch.setenv("API_KEY_AUTH_DISABLED", "false")

    for mod in list(importlib.sys.modules):
        if mod == "web.wsgi" or mod == "core.auth":
            importlib.sys.modules.pop(mod, None)

    from web.wsgi import server

    r = server.test_client().get(
        "/api/ab/compare",
        query_string={"sid_a": "a", "sid_b": "b"},
        headers={"X-API-Key": "wrong-key"},
    )
    assert r.status_code == 403
    assert called["n"] >= 1
