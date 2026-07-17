"""Refresh-token rotation logic (ADR-0009 §\"Issuance\" → migration plan step 1).

The endpoint lives in this module — separate from the FastAPI app — so the
logic can be unit-tested without spinning up a real server. Wiring
``POST /auth/refresh`` into a real FastAPI app is a 3-line call to
:func:`register_refresh_route` (see :mod:`web.app_fastapi` if you need a
reference, or just call it from your own app).
"""

from __future__ import annotations

import logging
from typing import Any

import jwt as pyjwt
from fastapi import APIRouter, HTTPException, Request

from core.auth_jwt import (
    Claims,
    JWTError,
    TokenExpiredError,
    issue_access_token,
    issue_refresh_token,
    revoke_token,
    verify_token,
)
from core.auth_jwt_middleware import _extract_bearer  # noqa: PLC2701 — internal helper

logger = logging.getLogger(__name__)


class RefreshError(Exception):
    """Raised when a refresh attempt is rejected. Mapped to HTTP 401."""


def rotate(refresh_token_str: str) -> dict[str, str]:
    """Verify a refresh token, revoke it, and mint a fresh access+refresh pair.

    Returns a dict with the new ``access_token``, ``refresh_token`` and
    ``token_type`` ("bearer"). Raises :class:`RefreshError` on any failure
    path (expired, revoked, wrong type, bad signature).
    """
    try:
        claims: Claims = verify_token(refresh_token_str, expected_type="refresh")
    except TokenExpiredError as exc:
        raise RefreshError(f"refresh expired: {exc}") from exc
    except pyjwt.InvalidTokenError as exc:
        raise RefreshError(f"refresh invalid: {exc}") from exc
    except JWTError as exc:
        raise RefreshError(f"refresh rejected: {exc}") from exc

    # Rotate: revoke the consumed refresh token, mint a new pair.
    revoke_token(claims.jti, claims.exp)

    new_access, _ = issue_access_token(claims.sub)
    new_refresh, _ = issue_refresh_token(claims.sub)
    logger.info("auth.refresh sub=%s jti_old=%s", claims.sub, claims.jti)
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


def register_refresh_route(app: Any, path: str = "/auth/refresh") -> None:
    """Attach a ``POST <path>`` handler to a FastAPI/Starlette app.

    Accepts the refresh token either via ``Authorization: Bearer …`` or in
    the JSON body as ``{"refresh_token": "..."}``. The body form is useful
    for clients that don't want to round-trip a header.
    """

    @app.post(path)  # type: ignore[union-attr]
    async def _refresh(request: Request) -> dict[str, str]:
        # Try header first, then JSON body.
        token: str | None = None
        try:
            token = _extract_bearer(request.headers.get("Authorization"))
        except JWTError:
            token = None
        if not token:
            try:
                payload = await request.json()
            except Exception:
                payload = None
            if isinstance(payload, dict):
                token = str(payload.get("refresh_token", "")).strip() or None
        if not token:
            raise HTTPException(status_code=400, detail="missing refresh_token")
        try:
            return rotate(token)
        except RefreshError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc


# Convenience: a pre-built router callers can ``app.include_router(router)``.
router = APIRouter()
register_refresh_route(router)


__all__ = [
    "RefreshError",
    "register_refresh_route",
    "rotate",
    "router",
]
