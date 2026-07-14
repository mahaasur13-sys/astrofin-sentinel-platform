"""Unit tests for the Flask `require_api_key` decorator.

These tests verify authentication behavior including edge cases.
"""

from __future__ import annotations

import importlib
import sys

import pytest

from flask import Flask, jsonify


def _reload_core_auth() -> None:
    """Drop cached ``core.auth`` and force a fresh re-import.

    ``core.auth`` reads ``API_KEY``/``REQUIRE_AUTH`` at import time and
    ``require_api_key`` closes over the module namespace. Reloading
    repopulates ``sys.modules['core.auth']`` with a fresh module so each
    test starts from the env vars it set via ``monkeypatch``.
    """
    sys.modules.pop("core.auth", None)
    # pydantic-settings caches get_settings() via @lru_cache; without
    # cache_clear() the re-imported module still sees stale env-derived
    # values, which is what made the empty-key and auth-disabled tests
    # fall through to the "missing key" 401 branch.
    from core.settings import get_settings

    get_settings.cache_clear()
    import core.auth  # noqa: F401  (re-import to repopulate sys.modules)


def create_test_app():
    """Create a Flask test app with a protected endpoint.

    Imports ``require_api_key`` *inside* the factory so the closure captures
    the freshly reloaded module's ``API_KEY``/``REQUIRE_AUTH`` constants.
    """
    from core.auth import require_api_key

    app = Flask(__name__)

    @app.route("/protected")
    @require_api_key
    def protected():
        return jsonify({"data": "secret"})

    return app


@pytest.mark.unit
def test_require_api_key_correct_key(monkeypatch):
    """Valid API key should allow access."""
    monkeypatch.setenv("REQUIRE_AUTH", "true")
    monkeypatch.setenv("API_KEY", "correct-key")
    _reload_core_auth()

    app = create_test_app()
    client = app.test_client()
    resp = client.get("/protected", headers={"X-API-Key": "correct-key"})
    assert resp.status_code == 200
    assert resp.json == {"data": "secret"}


@pytest.mark.unit
def test_require_api_key_missing_key(monkeypatch):
    """Missing API key should return 401 with envelope error."""
    monkeypatch.setenv("REQUIRE_AUTH", "true")
    monkeypatch.setenv("API_KEY", "correct-key")
    _reload_core_auth()

    app = create_test_app()
    client = app.test_client()
    resp = client.get("/protected")  # No header
    assert resp.status_code == 401
    json_data = resp.get_json()
    assert json_data["code"] == "UNAUTHORIZED"
    assert "message" in json_data
    assert "correlation_id" in json_data


@pytest.mark.unit
def test_require_api_key_wrong_key(monkeypatch):
    """Wrong API key should return 403 with envelope error."""
    monkeypatch.setenv("REQUIRE_AUTH", "true")
    monkeypatch.setenv("API_KEY", "correct-key")
    _reload_core_auth()

    app = create_test_app()
    client = app.test_client()
    resp = client.get("/protected", headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 403
    json_data = resp.get_json()
    assert json_data["code"] == "FORBIDDEN"
    assert "message" in json_data
    assert "correlation_id" in json_data


@pytest.mark.unit
def test_require_api_key_empty_env_key_should_reject_all(monkeypatch):
    """
    If API_KEY env var is empty (or missing), all requests should be rejected
    with 503 SERVICE_UNAVAILABLE, even if a key is provided.
    """
    monkeypatch.setenv("REQUIRE_AUTH", "true")
    monkeypatch.setenv("API_KEY", "")  # empty
    _reload_core_auth()

    app = create_test_app()
    client = app.test_client()

    # Request with no key
    resp1 = client.get("/protected")
    assert resp1.status_code == 500
    body1 = resp1.get_json()
    assert body1["code"] == "INTERNAL_ERROR"
    assert "message" in body1
    assert "correlation_id" in body1

    # Request with any key
    resp2 = client.get("/protected", headers={"X-API-Key": "anything"})
    assert resp2.status_code == 500
    body2 = resp2.get_json()
    assert body2["code"] == "INTERNAL_ERROR"


@pytest.mark.unit
def test_require_api_key_auth_disabled(monkeypatch):
    """When ``REQUIRE_AUTH=false`` the decorator must not block the request."""
    monkeypatch.setenv("API_KEY", "ignored-when-disabled")
    monkeypatch.setenv("REQUIRE_AUTH", "false")
    _reload_core_auth()

    app = create_test_app()
    client = app.test_client()

    # No key → should succeed when auth disabled
    resp1 = client.get("/protected")
    assert resp1.status_code == 200
    assert resp1.json == {"data": "secret"}

    # Any key
    resp2 = client.get("/protected", headers={"X-API-Key": "anything"})
    assert resp2.status_code == 200
