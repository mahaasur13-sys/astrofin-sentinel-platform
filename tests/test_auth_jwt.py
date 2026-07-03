"""Tests for JWT auth (P1-03)."""

from __future__ import annotations

import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import web.api.auth as auth
from web.api.auth import router as auth_router

# Build a minimal app that hosts only the auth router.  This keeps tests
# decoupled from health_endpoints (which has unrelated import-time
# issues with slowapi/redis/asyncpg).
app = FastAPI(title="auth-test")
app.include_router(auth_router)
client = TestClient(app)


def test_login_success():
    resp = client.post("/auth/login", json={"username": "admin", "password": "devpass123"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password():
    resp = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_user():
    resp = client.post("/auth/login", json={"username": "ghost", "password": "x"})
    assert resp.status_code == 401


def test_access_token_valid():
    token = auth.create_access_token("testuser")
    resp = client.get("/auth/whoami", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["sub"] == "testuser"


def test_access_token_expired(monkeypatch):
    # Issue a token that has already expired by setting TTL to a negative value.
    monkeypatch.setattr(auth, "ACCESS_TTL_MIN", -1)
    token = auth.create_access_token("testuser")
    resp = client.get("/auth/whoami", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert "expired" in resp.text.lower()


def test_refresh_token_ok():
    token = auth.create_refresh_token("testuser")
    resp = client.post("/auth/refresh", json={"refresh_token": token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_refresh_token_used_as_access_rejected():
    token = auth.create_refresh_token("testuser")
    resp = client.get("/auth/whoami", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert "invalid token type" in resp.text.lower()


def test_missing_authorization_header():
    resp = client.get("/auth/whoami")
    assert resp.status_code == 401


def test_malformed_authorization_header():
    resp = client.get("/auth/whoami", headers={"Authorization": "NotBearer abc"})
    assert resp.status_code == 401
