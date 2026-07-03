"""JWT access+refresh authentication for FastAPI endpoints (P1-03).

Reads JWT settings and dev users from ``config/secrets.yaml``, which is
produced by the CI step that decrypts ``config/secrets.secret.yaml`` via
SOPS.  In local development you can decrypt once with::

    export SOPS_AGE_KEY_FILE=$(pwd)/age.key
    sops -d config/secrets.secret.yaml > config/secrets.yaml

Tokens are HS256 JWTs with a ``type`` claim (``access`` or ``refresh``)
and a ``sub`` (subject = username).  ``fastapi_require_jwt`` is a
FastAPI dependency that validates the ``Authorization: Bearer ...``
header and returns the decoded payload.

Endpoints
---------
* ``POST /auth/login``   – exchange username/password for tokens.
* ``POST /auth/refresh`` – exchange a refresh token for a new access token.
* ``GET  /auth/whoami``  – return the current subject (protected).
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import bcrypt
import jwt
import yaml
from core.access_policy import normalize_role
from core.audit import write_audit
from core.rate_limiter import rate_limit_dependency
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Secrets loading
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SECRETS_PATH = os.getenv("SECRETS_FILE", str(_PROJECT_ROOT / "config" / "secrets.yaml"))


def _load_secrets(path: str = _SECRETS_PATH) -> Dict[str, Any]:
    """Load the (already decrypted) secrets file.

    Returns an empty dict if the file is missing or malformed – callers
    must treat that as a hard configuration error and raise.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except FileNotFoundError:
        return {}
    except yaml.YAMLError:
        return {}


def _get_cfg() -> Dict[str, Any]:
    cfg = _load_secrets()
    jwt_cfg = cfg.get("jwt") or {}
    return {
        "secret": jwt_cfg.get("secret"),
        "access_ttl_min": int(jwt_cfg.get("access_ttl_min", 15)),
        "refresh_ttl_days": int(jwt_cfg.get("refresh_ttl_days", 7)),
        "algorithm": jwt_cfg.get("algorithm", "HS256"),
        "dev_users": cfg.get("dev_users", []),
    }


_CFG = _get_cfg()
JWT_SECRET: Optional[str] = _CFG["secret"]
ACCESS_TTL_MIN: int = _CFG["access_ttl_min"]
REFRESH_TTL_DAYS: int = _CFG["refresh_ttl_days"]
ALGORITHM: str = _CFG["algorithm"]
DEV_USERS: List[Dict[str, str]] = _CFG["dev_users"]


def _require_secret() -> str:
    if not JWT_SECRET:
        raise RuntimeError(
            "JWT secret is not configured. Decrypt config/secrets.secret.yaml "
            "into config/secrets.yaml or set the SECRETS_FILE env var."
        )
    return JWT_SECRET


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_access_token(sub: str, role: str = "reader") -> str:
    role_norm = normalize_role(role)
    payload = {
        "sub": sub,
        "role": role_norm,
        "exp": _now() + timedelta(minutes=ACCESS_TTL_MIN),
        "iat": _now(),
        "type": "access",
    }
    return jwt.encode(payload, _require_secret(), algorithm=ALGORITHM)


def create_refresh_token(sub: str, role: str = "reader") -> str:
    role_norm = normalize_role(role)
    payload = {
        "sub": sub,
        "role": role_norm,
        "exp": _now() + timedelta(days=REFRESH_TTL_DAYS),
        "iat": _now(),
        "type": "refresh",
    }
    return jwt.encode(payload, _require_secret(), algorithm=ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, _require_secret(), algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------


def fastapi_require_jwt(request: Request) -> Dict[str, Any]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid Authorization header"
        )
    token = auth_header.split(" ", 1)[1].strip()
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    return payload


# ---------------------------------------------------------------------------
# User lookup
# ---------------------------------------------------------------------------


def authenticate_user(username: str, password: str) -> Optional[Dict[str, str]]:
    """Return user record on success, else None.

    A user record is ``{"username": str, "role": str}`` where ``role`` is
    normalized via :func:`core.access_policy.normalize_role`. The dev
    users table lives in ``config/secrets.yaml`` and may optionally carry
    a ``role`` field per entry; missing or unknown values fall back to
    ``"reader"`` (least privilege).
    """
    for user in DEV_USERS:
        if user.get("username") == username and verify_password(
            password, user.get("password_hash", "")
        ):
            return {
                "username": username,
                "role": normalize_role(user.get("role")),
            }
    return None


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    username: str
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class WhoAmIOut(BaseModel):
    sub: str
    role: str = "reader"


def _client_ip(request: Request) -> str:
    try:
        return request.client.host if request.client else "-"
    except Exception:
        return "-"


@router.post("/login", response_model=TokenPair)
def login(
    body: LoginIn,
    request: Request,
    _lim: None = Depends(rate_limit_dependency(5, 60)),
) -> TokenPair:
    ip = _client_ip(request)
    user = authenticate_user(body.username, body.password)
    if not user:
        write_audit(
            "auth.login.failure",
            actor=body.username,
            ip=ip,
            method=request.method,
            path=request.url.path,
            status="denied",
            detail={"reason": "invalid_credentials"},
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")
    role = user["role"]
    access = create_access_token(user["username"], role=role)
    refresh = create_refresh_token(user["username"], role=role)
    write_audit(
        "auth.login.success",
        actor=user["username"],
        ip=ip,
        method=request.method,
        path=request.url.path,
        status="ok",
        detail={"role": role},
    )
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=AccessTokenOut)
def refresh(
    body: RefreshIn,
    request: Request,
    _lim: None = Depends(rate_limit_dependency(10, 60)),
) -> AccessTokenOut:
    ip = _client_ip(request)
    try:
        payload = decode_token(body.refresh_token)
    except HTTPException:
        write_audit(
            "auth.refresh.failure",
            actor="-",
            ip=ip,
            method=request.method,
            path=request.url.path,
            status="denied",
            detail={"reason": "invalid_refresh_token"},
        )
        raise
    if payload.get("type") != "refresh":
        write_audit(
            "auth.refresh.failure",
            actor=payload.get("sub", "-"),
            ip=ip,
            method=request.method,
            path=request.url.path,
            status="denied",
            detail={"reason": "wrong_token_type"},
        )
        raise HTTPException(status_code=401, detail="Invalid token type")
    sub = payload.get("sub", "")
    role = normalize_role(payload.get("role"))
    access = create_access_token(sub, role=role)
    write_audit(
        "auth.refresh.success",
        actor=sub,
        ip=ip,
        method=request.method,
        path=request.url.path,
        status="ok",
        detail={"role": role},
    )
    return AccessTokenOut(access_token=access)


@router.get("/whoami", response_model=WhoAmIOut)
def whoami(
    request: Request,
    payload: dict = Depends(fastapi_require_jwt),
) -> WhoAmIOut:
    sub = payload.get("sub", "")
    role = normalize_role(payload.get("role"))
    write_audit(
        "auth.whoami",
        actor=sub,
        ip=_client_ip(request),
        method=request.method,
        path=request.url.path,
        status="ok",
        detail={"role": role},
    )
    return WhoAmIOut(sub=sub, role=role)
