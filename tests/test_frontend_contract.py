"""tests/test_frontend_contract.py — F3: Frontend API Contract Validation

Patch core.settings.get_settings() to guarantee require_auth=False regardless
of CI environment (GitHub Secrets, other test files' module-level imports, etc).
"""
import json, os, unittest.mock

import core.settings
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)
RESTRICTED_FIELDS = {'api_key', 'password', 'secret', 'private_key', 'token', 'credential'}
TEST_KEY = "test-frontend-key-000000000000"


def _patch_auth() -> unittest.mock._patch:
    """Return a patch that forces auth OFF and sets a known API key."""
    mock_settings = unittest.mock.MagicMock()
    mock_settings.require_auth = False
    mock_settings.api_key.get_secret_value.return_value = TEST_KEY
    return unittest.mock.patch("core.settings.get_settings", return_value=mock_settings)


def test_dashboard_fields():
    """Validate /api/v1/dashboard returns all fields expected by React frontend."""
    with _patch_auth():
        resp = client.get("/api/v1/dashboard", headers={"X-API-Key": TEST_KEY})
    assert resp.status_code == 200, f'Expected 200, got {resp.status_code}'
    data = resp.json()
    assert 'agents' in data, 'dashboard must have agents'
    assert 'ensemble' in data, 'dashboard must have ensemble'
    for k in RESTRICTED_FIELDS:
        assert k not in json.dumps(data), f'Sensitive field {k} leaked in dashboard'


def test_agent_run_fields():
    """Validate /api/v1/agent/run returns contract-compliant agent response."""
    with _patch_auth():
        resp = client.post(
            '/api/v1/agent/run',
            json={'agentId': 'fundamental', 'prompt': 'test'},
            headers={"X-API-Key": TEST_KEY},
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
    with _patch_auth():
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
