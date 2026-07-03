"""P1-13: RBAC + audit log.

Covers:
  - ``create_access_token`` / ``create_refresh_token`` embed the role
  - ``WhoAmIOut`` returns the role from the JWT payload
  - ``auth.login.success`` / ``auth.login.failure`` records are written
  - ``fastapi_require_role("admin")`` admits admin, denies reader (403),
    and writes an ``access.denied`` audit record on denial
  - Unknown / missing role in JWT is normalized to "reader"
  - Security headers middleware is attached to the health_endpoints app

Tests run in isolation: the audit log path is redirected to a tmpdir
via the ``AUDIT_LOG_FILE`` env var, and secrets are read from
``config/secrets.yaml`` (already decrypted by the developer).
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

import web.api.auth as auth
from core.audit import write_audit
from core.access_policy import fastapi_require_role, normalize_role
from web.api.auth import router as auth_router

# ---------------------------------------------------------------------------
# Per-test audit log file
# ---------------------------------------------------------------------------


@pytest.fixture
def audit_log(monkeypatch, tmp_path: Path) -> Path:
    log = tmp_path / "audit.jsonl"
    monkeypatch.setenv("AUDIT_LOG_FILE", str(log))
    # Also reset the import-time default inside core.audit by re-pointing
    # the helper at the test path.  write_audit() reads AUDIT_LOG_FILE on
    # every call, so this is enough.
    return log


@pytest.fixture(autouse=True)
def _reset_rate_limiters():
    """Clear in-process rate-limiter state between tests.

    The ``rate_limit_dependency(N, W)`` factory closes over a single
    ``RateLimiter`` instance, and the same instance backs every
    subsequent request to the protected endpoint.  Without a reset the
    P1-05 test (or earlier P1-13 tests) exhausts the 5-per-minute budget
    and later tests start seeing 429s instead of 401s.
    """
    import inspect

    import web.api.auth as _auth

    for fn_name in ("login", "refresh"):
        fn = getattr(_auth, fn_name)
        dep = inspect.signature(fn).parameters["_lim"].default
        for cell in dep.dependency.__closure__ or ():
            cell.cell_contents.reset()
    yield


def _read_records(path: Path) -> list:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# App fixture: JWT auth router + a single admin-only route that uses
# fastapi_require_role, so we exercise the dependency end-to-end.
# ---------------------------------------------------------------------------


@pytest.fixture
def api_app(audit_log: Path):
    app = FastAPI(title="p1-13-test")
    app.include_router(auth_router)

    @app.get("/admin/secret", dependencies=[Depends(fastapi_require_role("admin"))])
    def _admin_secret():
        return {"ok": True}

    return app


@pytest.fixture
def client(api_app) -> TestClient:
    return TestClient(api_app)


# ---------------------------------------------------------------------------
# Token + role plumbing
# ---------------------------------------------------------------------------


def test_create_access_token_includes_role():
    tok = auth.create_access_token("alice", role="admin")
    payload = auth.decode_token(tok)
    assert payload["sub"] == "alice"
    assert payload["role"] == "admin"
    assert payload["type"] == "access"


def test_create_access_token_defaults_to_reader():
    tok = auth.create_access_token("bob")
    payload = auth.decode_token(tok)
    assert payload["role"] == "reader"


def test_create_refresh_token_includes_role():
    tok = auth.create_refresh_token("alice", role="admin")
    payload = auth.decode_token(tok)
    assert payload["role"] == "admin"
    assert payload["type"] == "refresh"


def test_normalize_role_known():
    assert normalize_role("admin") == "admin"
    assert normalize_role("reader") == "reader"
    assert normalize_role("ADMIN") == "admin"


def test_normalize_role_unknown_defaults_to_reader():
    assert normalize_role(None) == "reader"
    assert normalize_role("") == "reader"
    assert normalize_role("superuser") == "reader"


# ---------------------------------------------------------------------------
# whoami returns role
# ---------------------------------------------------------------------------


def test_whoami_returns_role_for_admin_token(client):
    tok = auth.create_access_token("admin", role="admin")
    r = client.get("/auth/whoami", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    body = r.json()
    assert body["sub"] == "admin"
    assert body["role"] == "admin"


def test_whoami_returns_role_for_reader_token(client):
    tok = auth.create_access_token("reader", role="reader")
    r = client.get("/auth/whoami", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    assert r.json()["role"] == "reader"


# ---------------------------------------------------------------------------
# Audit log writes
# ---------------------------------------------------------------------------


def test_login_success_writes_audit(client, audit_log):
    # Use a real dev user (admin / devpass123) so login succeeds.
    r = client.post("/auth/login", json={"username": "admin", "password": "devpass123"})
    assert r.status_code == 200, r.text
    records = _read_records(audit_log)
    success = [rec for rec in records if rec["event"] == "auth.login.success"]
    assert success, f"no auth.login.success in {records!r}"
    assert success[0]["actor"] == "admin"
    assert success[0]["status"] == "ok"
    assert success[0]["detail"]["role"] == "admin"


def test_login_failure_writes_audit(client, audit_log):
    r = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401
    records = _read_records(audit_log)
    fail = [rec for rec in records if rec["event"] == "auth.login.failure"]
    assert fail, f"no auth.login.failure in {records!r}"
    assert fail[0]["status"] == "denied"
    assert fail[0]["actor"] == "admin"


# ---------------------------------------------------------------------------
# RBAC: fastapi_require_role
# ---------------------------------------------------------------------------


def test_rbac_admits_admin(client):
    tok = auth.create_access_token("admin", role="admin")
    r = client.get("/admin/secret", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200


def test_rbac_denies_reader_with_audit(client, audit_log):
    tok = auth.create_access_token("reader", role="reader")
    r = client.get("/admin/secret", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403
    records = _read_records(audit_log)
    denied = [rec for rec in records if rec["event"] == "access.denied"]
    assert denied, f"no access.denied in {records!r}"
    assert denied[0]["status"] == "denied"
    assert denied[0]["actor"] == "reader"
    assert denied[0]["detail"]["required"] == ["admin"]
    assert denied[0]["detail"]["actual"] == "reader"


def test_rbac_denies_token_without_role(client, audit_log):
    # Simulate a legacy token with no ``role`` claim by forging the payload.
    import jwt as pyjwt

    token = pyjwt.encode(
        {
            "sub": "legacy",
            "iat": 0,
            "exp": 9_999_999_999,
            "type": "access",
        },
        auth.JWT_SECRET,
        algorithm=auth.ALGORITHM,
    )
    r = client.get("/admin/secret", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    records = _read_records(audit_log)
    denied = [rec for rec in records if rec["event"] == "access.denied"]
    assert denied
    assert denied[0]["detail"]["actual"] == "reader"


# ---------------------------------------------------------------------------
# Security headers middleware
# ---------------------------------------------------------------------------

def test_security_headers_middleware_attaches_baseline_headers():
    from web.api.middleware import SecurityHeadersMiddleware

    app = FastAPI(title="headers-test")
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/ping")
    def _ping():
        return {"ok": True}

    with TestClient(app) as c:
        # 1) HTTP request — no HSTS, but everything else present.
        r = c.get("/ping")
        assert r.status_code == 200
        expected_http = {
            "X-Content-Type-Options",
            "X-Frame-Options",
            "Referrer-Policy",
            "Permissions-Policy",
        }
        for h in expected_http:
            assert h in r.headers, f"missing {h} on HTTP"
        assert r.headers["X-Content-Type-Options"] == "nosniff"
        assert r.headers["X-Frame-Options"] == "DENY"
        assert "Strict-Transport-Security" not in r.headers, "HSTS must NOT be emitted on plain HTTP"

        # 2) HTTPS request — HSTS should now be present.
        r_https = c.get("/ping", headers={"X-Forwarded-Proto": "https"})
        assert r_https.status_code == 200
        assert "Strict-Transport-Security" in r_https.headers, r_https.headers
        assert "max-age" in r_https.headers["Strict-Transport-Security"]


def test_security_headers_middleware_is_wired_into_health_app():
    """Smoke-check: ``health_endpoints.app`` registers SecurityHeadersMiddleware.

    Importing ``health_endpoints`` is heavy (asyncpg/redis/slowapi), so we
    wrap it in a try/except and only assert the middleware attachment when
    the import succeeds — which is the configuration we want to ship.
    """
    import importlib

    try:
        mod = importlib.import_module("health_endpoints")
    except Exception as e:  # pragma: no cover - import may fail in CI sandbox
        pytest.skip(f"health_endpoints not importable here: {e!r}")
    middleware_names = [m.cls.__name__ for m in mod.app.user_middleware]
    assert "SecurityHeadersMiddleware" in middleware_names, middleware_names
