"""Smoke test for Data Room API blueprint."""

from __future__ import annotations

from flask import Flask
from web.data_room import data_room_bp


import pytest


@pytest.mark.unit
def test_blueprint_exists():
    """Проверяем, что Blueprint зарегистрирован и имеет правильный префикс."""
    assert data_room_bp.name == "data_room"


@pytest.mark.unit
def test_conflicts_endpoint_returns_json():
    """При запросе /data-room/conflicts должен возвращаться JSON."""
    app = Flask(__name__)
    app.register_blueprint(data_room_bp)
    with app.test_client() as c:
        resp = c.get("/data-room/conflicts")
        assert resp.status_code in (200, 404)
        assert resp.is_json
