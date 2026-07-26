"""tests/test_frontend_contract.py — F3: Frontend API Contract Validation"""
import json, pytest
import os, core.auth
os.environ.pop("API_KEY", None)
core.auth.REQUIRE_AUTH = False

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

RESTRICTED_FIELDS = {'api_key', 'password', 'secret', 'private_key', 'token', 'credential'}
REQUIRED_AGENT_KEYS = {'agent_id', 'analyze_at', 'signal', 'confidence', 'reasoning'}

def test_dashboard_fields():
    resp = client.get('/api/v1/dashboard')
    assert resp.status_code == 200, f'Expected 200, got {resp.status_code}'
    data = resp.json()
    assert 'agents' in data, 'dashboard must have agents'
    assert 'summary' in data, 'dashboard must have summary'
    for k in RESTRICTED_FIELDS:
        assert k not in json.dumps(data), f'Sensitive field {k} leaked in dashboard'

def test_agent_run_fields():
    resp = client.post('/api/v1/agent/run', json={'agentId': 'fundamental', 'prompt': 'test'})
    assert resp.status_code in (200, 401, 403), f'Unexpected status: {resp.status_code}'
    if resp.status_code == 200:
        data = resp.json()
        for k in REQUIRED_AGENT_KEYS:
            assert k in data, f'Agent response missing required field: {k}'
        assert data['confidence'] >= 0 and data['confidence'] <= 100, 'confidence out of range'
        assert data['signal'] in ('LONG', 'SHORT', 'NEUTRAL'), f'invalid signal: {data["signal"]}'

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
