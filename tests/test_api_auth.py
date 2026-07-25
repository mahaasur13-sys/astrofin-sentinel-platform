"""Tests for API authentication (Phase 6.1)."""

from __future__ import annotations

import importlib
import os

import pytest
from fastapi.testclient import TestClient


class TestAPIAuth:
    @pytest.fixture(autouse=True, scope="class")
    def _setup_auth_env(self):
        """Isolate auth state: set env before importing app, restore after tests."""
        orig_api_key = os.environ.get("API_KEY")
        orig_require_auth = os.environ.get("REQUIRE_AUTH")

        os.environ["API_KEY"] = "test-api-secret-key-123"
        os.environ["REQUIRE_AUTH"] = "true"

        import core.auth
        reload_auth_state = core.auth.reload_auth_state
        reload_auth_state()

        # Ensure api.main sees fresh auth state (CI fix: Pydantic caches Settings)
        import api.main as api_main
        importlib.reload(api_main)

        try:
            yield
        finally:
            if orig_api_key is None:
                os.environ.pop("API_KEY", None)
            else:
                os.environ["API_KEY"] = orig_api_key
            if orig_require_auth is None:
                os.environ.pop("REQUIRE_AUTH", None)
            else:
                os.environ["REQUIRE_AUTH"] = orig_require_auth
            reload_auth_state()

    @pytest.fixture(autouse=True, scope="class")
    def _client(self, _setup_auth_env):
        """Provide isolated TestClient after auth setup."""
        import api.main as api_main
        self.__class__.client = TestClient(api_main.app, raise_server_exceptions=False)
        yield
        self.__class__.client.close()

    def test_health_returns_200(self):
        response = self.client.get("/health")
        assert response.status_code == 200

    def test_unauthenticated_returns_401_on_protected(self):
        response = self.client.get("/api/v1/dashboard")
        assert response.status_code in (401, 403)

    def test_valid_key_returns_200_on_protected(self):
        response = self.client.get("/api/v1/dashboard", headers={"Authorization": "Bearer test-api-secret-key-123"})
        assert response.status_code == 200
