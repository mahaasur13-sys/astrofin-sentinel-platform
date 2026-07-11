from __future__ import annotations

import pytest
from flask import Flask, jsonify
from core.auth import require_api_key


@pytest.mark.unit
def test_empty_api_key_returns_500(monkeypatch):
    app = Flask(__name__)

    @app.route("/test")
    @require_api_key
    def test_route():
        return jsonify({"status": "ok"})

    # Симулируем пустой ключ при включённой аутентификации
    monkeypatch.setenv("API_KEY", "")
    monkeypatch.setenv("API_KEY_AUTH_DISABLED", "false")

    with app.test_client() as client:
        resp = client.get("/test", headers={"X-API-Key": "anything"})
        assert resp.status_code == 500
        assert b"misconfiguration" in resp.data.lower()
