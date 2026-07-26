"""tests/test_frontend_contract.py — F3: Frontend API Contract Validation

CRITICAL: env vars MUST be set BEFORE importing core.auth / core.settings.
`pytest_configure` in conftest.py sets REQUIRE_AUTH=false but core.auth
module-level _refresh_auth_state() runs at import time — if CI has
REQUIRE_AUTH=true or API_KEY set via GitHub Secrets, the module globals
capture that state and `@require_auth` decorators enforce real auth.

Fix: force env vars, clear all caches, THEN import the app.
"""
import json, os, unittest.mock

# ═══ MUST come before ANY import that reads core.settings ═══
# Force-disable auth + clean any pre-existing API_KEY from CI Secrets.
for _k in ("API_KEY", "REQUIRE_AUTH"):
    os.environ.pop(_k, None)
os.environ["REQUIRE_AUTH"] = "false"
os.environ["API_KEY"] = "test-key-for-frontend-contract"

# Now safe to import — core.settings will see REQUIRE_AUTH=false
import core.settings
core.settings.get_settings.cache_clear()

import core.auth
core.auth.REQUIRE_AUTH = False
core.auth.API_KEY = "test-key-for-frontend-contract"

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

RESTRICTED_FIELDS = {'api_key', 'password', 'secret', 'private_key', 'token', 'credential'}


def test_dashboard_fields():
    """Validate /api/v1/dashboard returns all fields expected by React frontend."""
    resp = client.get("/api/v1/dashboard", headers={"X-API-Key": "test-key-for-frontend-contract"})
    assert resp.status_code == 200, f'Expected 200, got {resp.status_code}'
    data = resp.json()
    assert 'agents' in data, 'dashboard must have agents'
    assert 'ensemble' in data, 'dashboard must have ensemble'
    for k in RESTRICTED_FIELDS:
        assert k not in json.dumps(data), f'Sensitive field {k} leaked in dashboard'


def test_agent_run_fields():
    """Validate /api/v1/agent/run returns contract-compliant agent response."""
    resp = client.post(
        '/api/v1/agent/run',
        json={'agentId': 'fundamental', 'prompt': 'test'},
        headers={"X-API-Key": "test-key-for-frontend-contract"},
    )
    assert resp.status_code in (200, 500), f'Unexpected status: {resp.status_code}'
    data = resp.json()
    if resp.status_code == 200:
        assert 'result' in data, 'response must have result'
        result = data['result']
        assert 'agents' in result, 'result must have agents'
        assert 'ensemble' in result, 'result must have ensemble'
        for agent in result['agents']:
            assert 'id' in agent or 'agent_id' in agent, 'agent missing id/agent_id'
            assert 'confidence' in agent, f'agent {agent.get("id","?")} missing confidence'


def test_cors_preflight():
    resp = client.options('/api/v1/dashboard', headers={
        'Origin': 'http://localhost:5173',
        'Access-Control-Request-Method': 'GET',
    })
    assert resp.status_code in (200, 204), f'CORS preflight failed: {resp.status_code}'


def test_no_secrets_leak_in_errors():
    resp = client.get('/api/v1/nonexistent')
    assert resp.status_code == 404
    for k in RESTRICTED_FIELDS:
        assert k not in resp.text, f'Secret leak: {k} in error response'
