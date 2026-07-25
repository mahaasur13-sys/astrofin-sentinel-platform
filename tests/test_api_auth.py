"""Tests for API authentication (Phase 6.1)."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


class TestAPIAuth:
    @pytest.fixture(autouse=True, scope="class")
    def _patch_auth(self):
        """Patch core.auth globals directly — avoids Settings/os.environ race on CI."""
        import core.auth

        orig_require = core.auth.REQUIRE_AUTH
        orig_key = core.auth.API_KEY

        with patch.object(core.auth, "REQUIRE_AUTH", True), patch.object(
            core.auth, "API_KEY", "test-api-secret-key-123"
        ):
            yield

        core.auth.REQUIRE_AUTH = orig_require
        core.auth.API_KEY = orig_key

    @pytest.fixture(autouse=True, scope="class")
    def _client(self, _patch_auth):
        """Provide isolated TestClient after auth setup."""
        from api.main import app

        self.__class__.client = TestClient(app, raise_server_exceptions=False)
        yield
        self.__class__.client.close()

    def test_health_returns_200(self):
        response = self.client.get("/health")
        assert response.status_code == 200

    def test_unauthenticated_returns_401_on_protected(self):
        response = self.client.get("/api/v1/dashboard")
        assert response.status_code in (401, 403)

    def test_valid_key_returns_200_on_protected(self):
        response = self.client.get(
            "/api/v1/dashboard",
            headers={"Authorization": "Bearer test-api-secret-key-123"},
        )
        assert response.status_code == 200
