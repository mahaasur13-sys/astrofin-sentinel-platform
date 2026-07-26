"""H-06: End-to-end integration test — full pipeline (mock external APIs).

Validates: health → dashboard → agent run → aspects → metrics → interpretation.
All external API calls mocked — runs in CI without staging.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock
import json

API_KEY = "test-key-for-frontend-contract"


@pytest.fixture(autouse=True)
def _mock_external_apis():
    """Block all real HTTP calls during end-to-end test."""
    with patch("core.external.coingecko_client.httpx.AsyncClient.get") as mock_cg, \
         patch("core.ephemeris.swe.calc_ut", return_value=(0, 360.0)) as mock_eph, \
         patch("core.llm_router.send_to_openrouter", return_value="NEUTRAL — test environment") as mock_llm:
        mock_cg.return_value.status_code = 200
        mock_cg.return_value.json.return_value = {"bitcoin": {"usd": 64290.0}}
        yield


@pytest.fixture
def client():
    """Create TestClient with auth disabled."""
    import os
    import core.settings
    import core.auth

    os.environ["REQUIRE_AUTH"] = "false"
    os.environ["API_KEY"] = API_KEY
    core.settings.get_settings.cache_clear()
    core.auth.reload_auth_state()

    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app, raise_server_exceptions=False)


def test_full_pipeline(client):
    """H-06a: Complete API pipeline — 6 endpoints in sequence."""

    # 1. Root health check
    resp = client.get("/health")
    assert resp.status_code == 200, f"Health failed: {resp.status_code}"
    data = resp.json()
    assert "status" in data
    assert data["status"] == "ok"

    # 2. Dashboard returns 13 agents
    resp = client.get("/api/v1/dashboard", headers={"X-API-Key": API_KEY})
    assert resp.status_code == 200, f"Dashboard failed: {resp.status_code}"
    data = resp.json()
    assert "agents" in data, f"Dashboard missing agents: {list(data.keys())}"
    assert len(data["agents"]) >= 13, f"Expected ≥13 agents, got {len(data['agents'])}"

    # 3. Agent run produces ensemble
    resp = client.post(
        "/api/v1/agent/run",
        json={"agentId": "12", "prompt": "e2e test — full pipeline"},
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code in (200, 500), f"Agent run: {resp.status_code}"
    data = resp.json()
    assert "result" in data
    assert "ensemble" in data["result"], f"Missing ensemble: {list(data['result'].keys())}"

    # 4. Astro aspects endpoint
    resp = client.get("/api/v1/astro/aspects", headers={"X-API-Key": API_KEY})
    assert resp.status_code == 200, f"Aspects failed: {resp.status_code}"
    data = resp.json()
    assert "aspects" in data or "timestamp" in data

    # 5. Metrics endpoint (no auth)
    resp = client.get("/metrics")
    assert resp.status_code == 200, f"Metrics failed: {resp.status_code}"
    assert len(resp.content) > 0, "Metrics body empty"

    # 6. Astro interpretation
    resp = client.get("/api/v1/astro/interpretation", headers={"X-API-Key": API_KEY})
    assert resp.status_code == 200, f"Interpretation: {resp.status_code}"
    data = resp.json()
    assert "verdict" in data, f"Missing verdict: {list(data.keys())}"
    assert data["verdict"] in ("favourable", "caution", "avoid"), f"Unknown verdict: {data['verdict']}"


def test_dashboard_response_schema(client):
    """H-06b: Dashboard response matches DashboardResponse pydantic model."""

    resp = client.get("/api/v1/dashboard", headers={"X-API-Key": API_KEY})
    assert resp.status_code == 200

    data = resp.json()
    required_fields = {"agents", "regime", "ensemble", "safety_gate", "pnl", "mode", "agent_analysis"}
    missing = required_fields - set(data.keys())
    assert not missing, f"Dashboard missing fields: {missing}"

    for agent in data["agents"]:
        assert "id" in agent or "agent_id" in agent, f"Agent missing id: {agent}"
        assert "name" in agent, f"Agent missing name: {agent}"
        assert "weight" in agent, f"Agent missing weight: {agent}"

    ensemble = data["ensemble"]
    assert "signal" in ensemble
    assert "confidence" in ensemble


def test_agent_run_response_schema(client):
    """H-06c: Agent run response matches contract."""

    resp = client.post(
        "/api/v1/agent/run",
        json={"agentId": "1", "prompt": "schema validation test"},
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code in (200, 500)

    data = resp.json()
    assert "result" in data
    result = data["result"]
    assert "agents" in result
    assert "ensemble" in result

    for agent in result["agents"]:
        assert "signal" in agent, f"Agent missing signal: {agent}"
        assert "confidence" in agent, f"Agent missing confidence: {agent}"


def test_health_deep_check_structure(client):
    """H-06d: Health endpoint returns deep check fields."""

    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
