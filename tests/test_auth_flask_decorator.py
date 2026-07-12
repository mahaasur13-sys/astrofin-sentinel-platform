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
    monkeypatch.setenv("REQUIRE_AUTH", "true")
    monkeypatch.setenv("API_KEY", "correct-key")
    import importlib
    import core.auth

    importlib.reload(core.auth)

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
    import importlib
    import core.auth

    importlib.reload(core.auth)

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
    import importlib
    import core.auth

    importlib.reload(core.auth)

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
    import importlib
    import core.auth

    importlib.reload(core.auth)

    app = create_test_app()
    client = app.test_client()

    # Request with no key
    resp1 = client.get("/protected")
    assert resp1.status_code == 500
    json_data1 = resp1.get_json()
    assert json_data1["code"] == "INTERNAL_ERROR"
    assert "message" in json_data1
    assert "correlation_id" in json_data1

    # Request with any key
    resp2 = client.get("/protected", headers={"X-API-Key": "anything"})
    assert resp2.status_code == 500
    json_data2 = resp2.get_json()
    assert json_data2["code"] == "INTERNAL_ERROR"
    assert "message" in json_data2
    assert "correlation_id" in json_data2


@pytest.mark.unit
def test_require_api_key_auth_disabled(monkeypatch):
    """When REQUIRE_AUTH=false, all requests should succeed."""
    monkeypatch.setenv("REQUIRE_AUTH", "false")
    monkeypatch.setenv("API_KEY", "some-key")  # even if set, ignored
    import importlib
    import core.auth

    importlib.reload(core.auth)

    app = create_test_app()
    client = app.test_client()

    # No key
    resp1 = client.get("/protected")
    assert resp1.status_code == 200
    assert resp1.json == {"data": "secret"}

    # Any key
    resp2 = client.get("/protected", headers={"X-API-Key": "anything"})
    assert resp2.status_code == 200
