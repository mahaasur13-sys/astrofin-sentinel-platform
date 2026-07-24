"""RS256 JWT core (ADR-0009).

This module provides the canonical issue / verify / revoke primitives used
by the unified JWT authentication layer described in ADR-0009.

It is intentionally self-contained:

* No imports from :mod:`core.auth` (the legacy API-key module) so the
  rollout can proceed in *dual-mode* without circular dependencies.
* The revocation store is an in-process LRU dict with a per-entry TTL
  (ADR-0009 §"Verification" notes that a Redis-backed store is future
  work; for v1.0.0 we keep the in-memory default and document the
  upgrade path).

Configuration is read from environment variables; defaults are
production-safe (no keys, fail-closed on issue).
"""

from __future__ import annotations

import logging
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey,
    RSAPublicKey,
)
from jwt import (
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidSignatureError,
    PyJWKClient,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class JWTError(Exception):
    """Base class for all auth_jwt errors."""


class RevokedError(JWTError):
    """Raised when a previously-issued token is on the revocation list."""


class TokenExpiredError(JWTError):
    """Raised when the token's `exp` claim is in the past."""


class MissingKeyError(JWTError):
    """Raised when JWT_PRIVATE_KEY_PATH / JWT_PUBLIC_KEY_PATH is empty."""


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthConfig:
    """Resolved authentication configuration (read once at import time)."""

    private_key_path: str
    public_key_path: str
    issuer: str
    audience: str
    access_ttl_seconds: int
    refresh_ttl_seconds: int
    algorithm: str = "RS256"

    @classmethod
    def from_env(cls) -> "AuthConfig":
        return cls(
            private_key_path=os.getenv("JWT_PRIVATE_KEY_PATH", "keys/jwt_private.pem"),
            public_key_path=os.getenv("JWT_PUBLIC_KEY_PATH", "keys/jwt_public.pem"),
            issuer=os.getenv("JWT_ISSUER", "astrofin-sentinel"),
            audience=os.getenv("JWT_AUDIENCE", "astrofin-sentinel"),
            access_ttl_seconds=int(os.getenv("JWT_ACCESS_TTL", "3600")),
            refresh_ttl_seconds=int(os.getenv("JWT_REFRESH_TTL", "86400")),
        )


# ---------------------------------------------------------------------------
# Claims / Principal
# ---------------------------------------------------------------------------


@dataclass
class Claims:
    """Decoded JWT claims relevant to the application."""

    sub: str
    role: str
    scopes: list[str]
    jti: str
    typ: str
    exp: int
    iat: int
    iss: str
    aud: str | list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "sub": self.sub,
            "role": self.role,
            "scope": self.scopes,
            "jti": self.jti,
            "typ": self.typ,
            "exp": self.exp,
            "iat": self.iat,
            "iss": self.iss,
            "aud": self.aud,
        }


@dataclass
class Principal:
    """Authenticated principal exposed to route handlers."""

    sub: str
    role: str
    scopes: list[str] = field(default_factory=list)
    jti: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Key handling
# ---------------------------------------------------------------------------


def _load_pem(path: str) -> bytes:
    p = Path(path)
    if not p.is_file():
        raise MissingKeyError(f"JWT key file not found: {path}")
    return p.read_bytes()


def load_keypair(cfg: AuthConfig | None = None) -> tuple[RSAPrivateKey, RSAPublicKey]:
    """Load RSA private + public keys from PEM files."""
    cfg = cfg or AuthConfig.from_env()
    priv_pem = _load_pem(cfg.private_key_path)
    pub_pem = _load_pem(cfg.public_key_path)
    priv = serialization.load_pem_private_key(priv_pem, password=None)  # type: ignore[return-value]
    pub = serialization.load_pem_public_key(pub_pem)  # type: ignore[return-value]
    if not isinstance(priv, RSAPrivateKey) or not isinstance(pub, RSAPublicKey):
        raise JWTError("Loaded keys are not RSA keys")
    return priv, pub


def generate_keypair(out_dir: str = "keys") -> tuple[str, str]:
    """Generate a fresh 2048-bit RSA keypair. Returns (priv_path, pub_path)."""
    from cryptography.hazmat.primitives.asymmetric import rsa

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = priv.public_key()

    priv_path = Path(out_dir) / "jwt_private.pem"
    pub_path = Path(out_dir) / "jwt_public.pem"

    priv_path.write_bytes(
        priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    pub_path.write_bytes(
        pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    # Lock down private key permissions (best-effort, no-op on Windows).
    try:
        os.chmod(priv_path, 0o600)
    except OSError:  # pragma: no cover - platform dependent
        pass
    return str(priv_path), str(pub_path)


# ---------------------------------------------------------------------------
# Revocation store (in-process, TTL-bounded)
# ---------------------------------------------------------------------------


class _RevocationStore:
    """Process-local revocation list with TTL eviction.

    This is intentionally simple: a dict from jti -> expiry_epoch.
    ``revoke_token`` and the verify path acquire the same lock so the
    store is safe under concurrent verification.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._items: dict[str, int] = {}

    def revoke(self, jti: str, exp: int) -> None:
        with self._lock:
            self._items[jti] = exp
            self._gc()

    def is_revoked(self, jti: str) -> bool:
        with self._lock:
            self._gc()
            return jti in self._items

    def _gc(self) -> None:
        now = int(time.time())
        expired = [k for k, exp in self._items.items() if exp <= now]
        for k in expired:
            self._items.pop(k, None)


_REVOCATION = _RevocationStore()


def revoke_token(jti: str, exp: int) -> None:
    """Add a JTI to the revocation list until its `exp` is reached."""
    _REVOCATION.revoke(jti, exp)


# ---------------------------------------------------------------------------
# Issue / verify
# ---------------------------------------------------------------------------


def issue_access_token(
    sub: str,
    *,
    role: str = "user",
    scopes: list[str] | None = None,
    cfg: AuthConfig | None = None,
    ttl: int | None = None,
) -> tuple[str, Claims]:
    """Mint a fresh RS256 access token. Returns (jwt_string, claims)."""
    cfg = cfg or AuthConfig.from_env()
    priv, _ = load_keypair(cfg)
    now = int(time.time())
    exp = now + (ttl if ttl is not None else cfg.access_ttl_seconds)
    jti = uuid.uuid4().hex
    payload: dict[str, Any] = {
        "sub": sub,
        "role": role,
        "scope": list(scopes or []),
        "typ": "access",
        "iss": cfg.issuer,
        "aud": cfg.audience,
        "iat": now,
        "nbf": now,
        "exp": exp,
        "jti": jti,
    }
    token = jwt.encode(payload, priv, algorithm=cfg.algorithm)
    return token, Claims(
        sub=sub,
        role=role,
        scopes=list(scopes or []),
        jti=jti,
        typ="access",
        exp=exp,
        iat=now,
        iss=cfg.issuer,
        aud=cfg.audience,
    )


def issue_refresh_token(
    sub: str,
    *,
    cfg: AuthConfig | None = None,
) -> tuple[str, Claims]:
    """Mint a refresh token. Same shape as access but typ='refresh'."""
    cfg = cfg or AuthConfig.from_env()
    priv, _ = load_keypair(cfg)
    now = int(time.time())
    exp = now + cfg.refresh_ttl_seconds
    jti = uuid.uuid4().hex
    payload: dict[str, Any] = {
        "sub": sub,
        "role": "refresh",
        "scope": [],
        "typ": "refresh",
        "iss": cfg.issuer,
        "aud": cfg.audience,
        "iat": now,
        "nbf": now,
        "exp": exp,
        "jti": jti,
    }
    token = jwt.encode(payload, priv, algorithm=cfg.algorithm)
    return token, Claims(
        sub=sub,
        role="refresh",
        scopes=[],
        jti=jti,
        typ="refresh",
        exp=exp,
        iat=now,
        iss=cfg.issuer,
        aud=cfg.audience,
    )


def verify_token(
    token: str,
    expected_type: str = "access",
    *,
    cfg: AuthConfig | None = None,
) -> Claims:
    """Verify a JWT and return the decoded :class:`Claims`.

    Raises:
        TokenExpiredError: when ``exp`` is in the past.
        RevokedError: when the JTI is on the revocation list.
        InvalidSignatureError: signature doesn't match.
        InvalidAudienceError / InvalidIssuerError: claim mismatch.
    """
    cfg = cfg or AuthConfig.from_env()
    _, pub = load_keypair(cfg)
    public_pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    try:
        decoded: dict[str, Any] = jwt.decode(
            token,
            public_pem,
            algorithms=[cfg.algorithm],
            issuer=cfg.issuer,
            audience=cfg.audience,
            options={"require": ["exp", "iat", "iss", "aud", "sub", "jti"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpiredError(str(exc)) from exc
    except InvalidSignatureError:
        raise
    except InvalidAudienceError:
        raise
    except InvalidIssuerError:
        raise

    if decoded.get("typ") != expected_type:
        raise JWTError(
            f"token type mismatch: expected {expected_type!r}, got {decoded.get('typ')!r}"
        )

    if _REVOCATION.is_revoked(decoded["jti"]):
        raise RevokedError(f"token jti revoked: {decoded['jti']}")

    return Claims(
        sub=decoded["sub"],
        role=decoded.get("role", "user"),
        scopes=list(decoded.get("scope", [])),
        jti=decoded["jti"],
        typ=decoded["typ"],
        exp=int(decoded["exp"]),
        iat=int(decoded["iat"]),
        iss=decoded["iss"],
        aud=decoded["aud"],
    )


# ---------------------------------------------------------------------------
# JWKS client helper (used by 3rd-party verifiers; optional)
# ---------------------------------------------------------------------------


def build_jwks_client(jwks_uri: str) -> PyJWKClient:
    """Wrap PyJWT's PyJWKClient so callers can verify against a remote JWKS."""
    return PyJWKClient(jwks_uri)


__all__ = [
    "AuthConfig",
    "Claims",
    "JWTError",
    "MissingKeyError",
    "Principal",
    "RevokedError",
    "TokenExpiredError",
    "build_jwks_client",
    "generate_keypair",
    "issue_access_token",
    "issue_refresh_token",
    "load_keypair",
    "revoke_token",
    "verify_token",
]
