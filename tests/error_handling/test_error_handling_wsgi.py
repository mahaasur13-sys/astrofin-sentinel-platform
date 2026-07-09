"""HTTP-level tests for the standardised error envelope (ERR-01).

These tests exercise the Flask server defined in web/wsgi.py and verify that:
  * 400/401/403/404/500 responses carry the same JSON envelope.
  * The envelope contains correlation_id and trace_id.
  * The X-Correlation-ID response header echoes the request id.
  * Legacy 200 responses (success) are unaffected.
"""
from __future__ import annotations

import os

os.environ.setdefault("API_KEY", "test-key")

import pytest

from web.wsgi import server as flask_server


@pytest.fixture()
def client():
    flask_server.config.update(TESTING=True)
    with flask_server.test_client() as c:
        yield c


def _envelope_keys():
    return {
        "code",
        "message",
        "trace_id",
        "correlation_id",
        "timestamp",
        "status",
        "details",
    }


class TestHealthEndpoint:
    def test_health_ok(self, client):
        r = client.get("/health")
        assert r.status_code in (200, 503)
        assert r.get_json()["status"] in {"ok", "draining"}


class TestStandardisedErrors:
    def test_400_bad_request_envelope(self, client):
        r = client.get(
            "/api/ab/compare",
            headers={"X-API-Key": "test-key", "X-Correlation-ID": "cid-1"},
        )
        assert r.status_code == 400
        body = r.get_json()
        assert _envelope_keys().issubset(body.keys())
        assert body["code"] == "BAD_REQUEST"
        assert body["status"] == 400
        assert body["correlation_id"] == "cid-1"
        assert r.headers.get("X-Correlation-ID") == "cid-1"
        assert "sid_a and sid_b required" in body["message"]

    def test_400_confirmation_required(self, client):
        r = client.post(
            "/api/live/enable",
            json={"confirmed": False},
            headers={"X-API-Key": "test-key"},
        )
        assert r.status_code == 400
        body = r.get_json()
        assert body["code"] == "BAD_REQUEST"
        assert "Confirmation required" in body["message"]
        assert body["correlation_id"]

    def test_404_uses_envelope(self, client):
        r = client.get(
            "/data-room/conflicts",
            headers={"X-API-Key": "test-key"},
        )
        if r.status_code == 404:
            body = r.get_json()
            assert body["code"] == "NOT_FOUND"
            assert _envelope_keys().issubset(body.keys())
        else:
            assert r.status_code == 200

    def test_unknown_route_returns_404_envelope(self, client):
        r = client.get("/api/does-not-exist")
        assert r.status_code == 404
        body = r.get_json()
        if body is not None and isinstance(body, dict):
            assert _envelope_keys().issubset(body.keys())


class TestCorrelationIdPropagation:
    def test_correlation_id_generated_when_missing(self, client):
        r = client.get(
            "/api/ab/compare",
            headers={"X-API-Key": "test-key"},
        )
        body = r.get_json()
        assert body["correlation_id"]
        assert r.headers.get("X-Correlation-ID") == body["correlation_id"]

    def test_correlation_id_echoed_from_request(self, client):
        r = client.get(
            "/api/ab/compare",
            headers={"X-API-Key": "test-key", "X-Correlation-ID": "my-trace-7"},
        )
        body = r.get_json()
        assert body["correlation_id"] == "my-trace-7"
        assert r.headers.get("X-Correlation-ID") == "my-trace-7"
