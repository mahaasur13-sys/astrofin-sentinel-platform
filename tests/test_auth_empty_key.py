"""Edge case: API_KEY unset on the server with REQUIRE_AUTH=true.

The contract is "INTERNAL_ERROR + envelope", not 401/403, because
the server is misconfigured (auth required but no key available).
"""

from __future__ import annotations

import sys

import pytest
from flask import Flask, jsonify


def _reload_core_auth():
    """Drop cached ``core.auth`` so a fresh module is created from current env."""
    sys.modules.pop("core.auth", None)
    import core.auth as auth_mod  # noqa: F401 — populate sys.modules

    return auth_mod


@pytest.mark.unit
def test_empty_api_key_returns_500(monkeypatch):
    """Empty API_KEY with REQUIRE_AUTH=true should 500 with INTERNAL_ERROR envelope.

    Sets env via ``monkeypatch`` **before** reloading so ``core.auth`` reads the
    empty key on first import. This exercises the ``_ensure_key_configured``
    path with a falsy ``API_KEY``.
    """
    monkeypatch.setenv("API_KEY", "")
    monkeypatch.setenv("REQUIRE_AUTH", "true")
    auth_mod = _reload_core_auth()
    # Sanity check: the freshly-imported module has the expected (empty) key.
    assert auth_mod.API_KEY == ""
    assert auth_mod.REQUIRE_AUTH is True

    # Re-import the decorator from the fresh module so the closure sees
    # the new ``API_KEY`` constant.
    from core.auth import require_api_key

    app = Flask(__name__)

    @app.route("/test")
    @require_api_key
    def test_route():
        return jsonify({"status": "ok"})

    with app.test_client() as client:
        resp = client.get("/test", headers={"X-API-Key": "anything"})
        # Contract: 500 + INTERNAL_ERROR envelope (server misconfiguration)
        assert resp.status_code == 500
        json_data = resp.get_json()
        assert json_data["code"] == "INTERNAL_ERROR"
        assert "message" in json_data
        assert "correlation_id" in json_data
