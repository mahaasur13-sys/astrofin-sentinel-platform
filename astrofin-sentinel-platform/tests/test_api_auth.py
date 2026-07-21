"""Tests for API authentication (Phase 6.1)."""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

os.environ["API_KEY"] = "test-api-secret-key-123"
os.environ["REQUIRE_AUTH"] = "true"

from api.main import app

client = TestClient(app, raise_server_exceptions=False)


class TestAPIAuth:
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_unauthenticated_returns_401_on_protected(self):
        response = client.get("/api/v1/dashboard")
        assert response.status_code in (401, 403)

    def test_valid_key_returns_200_on_protected(self):
        response = client.get(
            "/api/v1/dashboard",
            headers={"Authorization": "Bearer test-api-secret-key-123"}
        )
        assert response.status_code == 200
