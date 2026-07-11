"""Unit tests for the Flask `require_api_key` decorator.

These tests verify authentication behavior including edge cases.
"""
from __future__ import annotations

import pytest

from flask import Flask, jsonify
from core.auth import require_api_key


def create_test_app():
    """Create a Flask test app with a protected endpoint."""
    app = Flask(__name__)

    @app.route("/protected")
    @require_api_key
    def protected():
        return jsonify({"data": "secret"})

    return app


@pytest.mark.unit
def test_require_api_key_correct_key(monkeypatch):
    """Valid API key should allow access."""
    monkeypatch.setenv("API_KEY_AUTH_DISABLED", "false")
    monkeypatch.setenv("API_KEY", "correct-key")
    # core.auth reads env per-request — no reload required.

    app = create_test_app()
    client = app.test_client()
    resp = client.get("/protected", headers={"X-API-Key": "correct-key"})
    assert resp.status_code == 200
    assert resp.json == {"data": "secret"}


@pytest.mark.unit
def test_require_api_key_missing_key(monkeypatch):
    """Missing API key should return 401 with JSON error envelope."""
    monkeypatch.setenv("API_KEY_AUTH_DISABLED", "false")
    monkeypatch.setenv("API_KEY", "correct-key")

    app = create_test_app()
    client = app.test_client()
    resp = client.get("/protected")  # No header
    assert resp.status_code == 401
    assert resp.json.get("code") == "UNAUTHORIZED"


@pytest.mark.unit
def test_require_api_key_wrong_key(monkeypatch):
    """Wrong API key should return 403 with JSON error envelope."""
    monkeypatch.setenv("API_KEY_AUTH_DISABLED", "false")
    monkeypatch.setenv("API_KEY", "correct-key")

    app = create_test_app()
    client = app.test_client()
    resp = client.get("/protected", headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 403
    assert resp.json.get("code") == "FORBIDDEN"


@pytest.mark.unit
def test_require_api_key_empty_env_key_should_reject_all(monkeypatch):
    """
    If API_KEY env var is empty (or missing), all requests should be rejected
    with 500, even if a key is provided.
    """
    monkeypatch.setenv("API_KEY_AUTH_DISABLED", "false")
    monkeypatch.setenv("API_KEY", "")  # empty

    app = create_test_app()
    client = app.test_client()

    # Request with no key
    resp1 = client.get("/protected")
    assert resp1.status_code == 500
    assert resp1.json.get("code") == "INTERNAL_ERROR"
    assert "misconfiguration" in resp1.json.get("message", "").lower()

    # Request with any key
    resp2 = client.get("/protected", headers={"X-API-Key": "anything"})
    assert resp2.status_code == 500
    assert resp2.json.get("code") == "INTERNAL_ERROR"
    assert "misconfiguration" in resp2.json.get("message", "").lower()


@pytest.mark.unit
def test_require_api_key_auth_disabled(monkeypatch):
    """When API_KEY_AUTH_DISABLED=true, all requests should succeed."""
    monkeypatch.setenv("API_KEY_AUTH_DISABLED", "true")
    monkeypatch.setenv("API_KEY", "some-key")  # even if set, ignored

    app = create_test_app()
    client = app.test_client()

    # No key
    resp1 = client.get("/protected")
    assert resp1.status_code == 200
    assert resp1.json == {"data": "secret"}

    # Any key
    resp2 = client.get("/protected", headers={"X-API-Key": "anything"})
    assert resp2.status_code == 200
