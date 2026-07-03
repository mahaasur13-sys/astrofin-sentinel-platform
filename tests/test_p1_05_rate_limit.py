"""P1-05: rate limiter on /auth/login and /auth/refresh."""
from __future__ import annotations
import os
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
os.environ.setdefault("SECRETS_FILE", "/dev/null")
from web.api.auth import router, rate_limit_dependency
app = FastAPI()
app.include_router(router)
client = TestClient(app)
def test_rate_limit_blocks_after_threshold():
    from web.api.auth import create_access_token
    for i in range(5):
        r = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
        assert r.status_code in (401, 429), f"#{i}: got {r.status_code}"
    r = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 429, f"expected 429, got {r.status_code}"
