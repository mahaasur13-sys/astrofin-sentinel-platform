from __future__ import annotations

import os

from fastapi.testclient import TestClient

import pytest

os.environ["REQUIRE_AUTH"] = "true"
os.environ["API_KEY"] = "test-key-123"

from deploy.monitoring.health_endpoints import app

client = TestClient(app, raise_server_exceptions=False)


@pytest.mark.unit
def test_rate_limit_too_many_requests():
    """Проверяем, что после 10 запросов с правильным ключом возвращается 429."""
    headers = {"X-API-Key": "test-key-123"}
    responses = [client.get("/api/ab/compare", headers=headers) for _ in range(11)]
    # Хотя бы последний должен быть 429
    assert any(r.status_code == 429 for r in responses[-3:]), "No 429 response after exceeding limit"


@pytest.mark.unit
def test_health_endpoint_not_limited():
    """Публичные эндпоинты не должны лимитироваться."""
    for _ in range(5):
        r = client.get("/health")
        assert r.status_code == 200
