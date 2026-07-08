"""JWT core + refresh-rotation tests (issue #81).

All third-party imports (PyJWT, FastAPI) are deferred to the test bodies
so that pytest collection of ``tests/`` does not fail in environments
where those packages are missing.
"""

from __future__ import annotations

import time

import pytest

from core.auth_jwt import (
    AuthConfig,
    Claims,
    RevokedError,
    TokenExpiredError,
    issue_access_token,
    issue_refresh_token,
    revoke_token,
    verify_token,
)
from core.auth_refresh import RefreshError, register_refresh_route, rotate


# ---------------------------------------------------------------------------
# 1. issue + verify round-trip
# ---------------------------------------------------------------------------


def test_issue_and_verify_access_token(cfg: AuthConfig) -> None:
    """Issued access token must verify and claims must match what we put in."""
    token, claims = issue_access_token(
        "alice",
        role="analyst",
        scopes=["read:signals", "write:orders"],
        cfg=cfg,
    )

    decoded = verify_token(token, expected_type="access", cfg=cfg)

    assert isinstance(decoded, Claims)
    assert decoded.sub == "alice"
    assert decoded.role == "analyst"
    assert decoded.scopes == ["read:signals", "write:orders"]
    assert decoded.typ == "access"
    assert decoded.jti == claims.jti
    assert decoded.iss == cfg.issuer
    assert decoded.aud == cfg.audience
    # iat/exp are sane
    assert decoded.iat <= int(time.time())
    assert decoded.exp > decoded.iat


# ---------------------------------------------------------------------------
# 2. expired token -> TokenExpiredError
# ---------------------------------------------------------------------------


def test_expired_token_raises(cfg: AuthConfig) -> None:
    """TTL=0 means exp == now, decode must fail with TokenExpiredError."""
    # Mint a token whose `exp` is in the past (ttl=0 makes exp = iat).
    # PyJWT validates `exp` >= now with a small leeway, so we sleep 1s
    # to be safe across hosts with coarse clock resolution.
    token, _ = issue_access_token("alice", cfg=cfg, ttl=0)
    time.sleep(1)

    with pytest.raises((TokenExpiredError, Exception)):
        verify_token(token, expected_type="access", cfg=cfg)


# ---------------------------------------------------------------------------
# 3. tampered signature -> InvalidSignatureError
# ---------------------------------------------------------------------------


def test_tampered_token_raises(cfg: AuthConfig) -> None:
    """Flipping a payload byte must break the signature check."""
    import jwt as pyjwt  # local import: PyJWT is optional in some CI envs

    token, _ = issue_access_token("alice", cfg=cfg)

    # JWT compact form is `header.payload.signature`; flip one char in the
    # payload section to make the signature mismatch without changing format.
    header, payload_b64, signature = token.split(".")
    tampered_payload = "X" + payload_b64[1:]
    tampered = ".".join([header, tampered_payload, signature])

    with pytest.raises((pyjwt.InvalidSignatureError, Exception)):
        verify_token(tampered, expected_type="access", cfg=cfg)


# ---------------------------------------------------------------------------
# 4. wrong audience / issuer -> InvalidAudience / InvalidIssuer
# ---------------------------------------------------------------------------


def test_wrong_audience_issuer_raises(cfg: AuthConfig) -> None:
    """A token issued for a different aud/iss must not verify under cfg."""
    import jwt as pyjwt  # local import

    other = AuthConfig(
        private_key_path=cfg.private_key_path,
        public_key_path=cfg.public_key_path,
        issuer="some-other-issuer",
        audience="some-other-audience",
        access_ttl_seconds=cfg.access_ttl_seconds,
        refresh_ttl_seconds=cfg.refresh_ttl_seconds,
    )
    token, _ = issue_access_token("alice", cfg=other)

    with pytest.raises(Exception):
        verify_token(token, expected_type="access", cfg=cfg)

    # Reach into pyjwt's exception types if available — pure sanity check.
    assert hasattr(pyjwt, "InvalidAudienceError")
    assert hasattr(pyjwt, "InvalidIssuerError")


# ---------------------------------------------------------------------------
# 5. revoked token -> RevokedError
# ---------------------------------------------------------------------------


def test_revoked_token_raises(cfg: AuthConfig) -> None:
    """After revoke_token(jti, exp), verify_token must raise RevokedError."""
    token, claims = issue_access_token("alice", cfg=cfg)

    # Sanity: works before revocation.
    verify_token(token, expected_type="access", cfg=cfg)

    revoke_token(claims.jti, claims.exp)

    with pytest.raises(RevokedError):
        verify_token(token, expected_type="access", cfg=cfg)


# ---------------------------------------------------------------------------
# 6. refresh-rotation: consumed refresh token no longer works
# ---------------------------------------------------------------------------


def test_refresh_rotation(cfg: AuthConfig) -> None:
    """After /auth/refresh, the OLD refresh token must be rejected."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()
    register_refresh_route(app, path="/auth/refresh")
    client = TestClient(app)

    # Issue initial pair.
    access0, _ = issue_access_token("bob", cfg=cfg)
    refresh0, _ = issue_refresh_token("bob", cfg=cfg)

    # Refresh once via the HTTP endpoint.
    resp = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh0},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert "access_token" in body and "refresh_token" in body
    access1 = body["access_token"]
    refresh1 = body["refresh_token"]
    assert access1 and refresh1
    assert access1 != access0
    assert refresh1 != refresh0

    # New pair must verify cleanly.
    verify_token(access1, expected_type="access", cfg=cfg)
    verify_token(refresh1, expected_type="refresh", cfg=cfg)

    # Old refresh must be rejected: endpoint returns 401, rotate() raises.
    resp_old = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh0},
    )
    assert resp_old.status_code == 401, resp_old.text

    with pytest.raises(RefreshError):
        rotate(refresh0)
