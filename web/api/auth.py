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


def create_access_token(sub: str) -> str:
    payload = {
        "sub": sub,
        "exp": _now() + timedelta(minutes=ACCESS_TTL_MIN),
        "iat": _now(),
        "type": "access",
    }
    return jwt.encode(payload, _require_secret(), algorithm=ALGORITHM)


def create_refresh_token(sub: str) -> str:
    payload = {
        "sub": sub,
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


def authenticate_user(username: str, password: str) -> Optional[str]:
    for user in DEV_USERS:
        if user.get("username") == username and verify_password(
            password, user.get("password_hash", "")
        ):
            return username
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


@router.post("/login", response_model=TokenPair)
def login(
    body: LoginIn,
    _lim: None = Depends(rate_limit_dependency(5, 60)),
) -> TokenPair:
    user = authenticate_user(body.username, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenPair(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
    )


@router.post("/refresh", response_model=AccessTokenOut)
def refresh(
    body: RefreshIn,
    _lim: None = Depends(rate_limit_dependency(10, 60)),
) -> AccessTokenOut:
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    return AccessTokenOut(access_token=create_access_token(payload["sub"]))


@router.get("/whoami", response_model=WhoAmIOut)
def whoami(payload: dict = Depends(fastapi_require_jwt)) -> WhoAmIOut:
    return WhoAmIOut(sub=payload["sub"])
