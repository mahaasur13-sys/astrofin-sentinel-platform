"""JWT middleware (FastAPI + Flask) — ADR-0009.

This module exposes the single ``require_jwt`` entry point described in
ADR-0009 §"Verification":

* FastAPI: ``Depends(require_jwt)`` — returns a :class:`Principal`.
* Flask:  ``@require_jwt`` — populates ``flask.g.principal`` and returns
  ``(jsonify({...}), status_code)`` on failure.

Errors are mapped to HTTP 401 (missing/invalid token, expired, wrong
issuer/audience, signature mismatch, revocation) with a JSON body that
matches the existing ``core.auth`` shape so callers see a consistent
error contract. Successful verification populates Flask's ``g.principal``
for downstream handlers that want to read it without re-parsing the
token.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import jwt as pyjwt
from fastapi import HTTPException, Request
from fastapi.security.utils import get_authorization_scheme_param

from core.auth_jwt import (
    JWTError,
    Principal,
    RevokedError,
    TokenExpiredError,
    verify_token,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Error responses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _AuthFailure:
    status: int
    code: str
    message: str


def _failure(exc: Exception) -> _AuthFailure:
    """Map a JWT exception to a structured auth-failure response."""
    if isinstance(exc, TokenExpiredError):
        return _AuthFailure(401, "token_expired", "Token has expired")
    if isinstance(exc, RevokedError):
        return _AuthFailure(401, "token_revoked", "Token has been revoked")
    if isinstance(exc, pyjwt.InvalidAudienceError):
        return _AuthFailure(401, "invalid_audience", "Invalid token audience")
    if isinstance(exc, pyjwt.InvalidIssuerError):
        return _AuthFailure(401, "invalid_issuer", "Invalid token issuer")
    if isinstance(exc, pyjwt.InvalidSignatureError):
        return _AuthFailure(401, "invalid_signature", "Invalid token signature")
    if isinstance(exc, pyjwt.MissingRequiredClaimError):
        return _AuthFailure(401, "missing_claim", str(exc))
    if isinstance(exc, JWTError):
        return _AuthFailure(401, "invalid_token", str(exc) or "Invalid token")
    return _AuthFailure(401, "invalid_token", "Invalid token")


# ---------------------------------------------------------------------------
# Token extraction
# ---------------------------------------------------------------------------


def _extract_bearer(authorization_header: str | None) -> str:
    if not authorization_header:
        raise JWTError("missing Authorization header")
    scheme, param = get_authorization_scheme_param(authorization_header)
    if scheme.lower() != "bearer" or not param:
        raise JWTError("Authorization header must use the Bearer scheme")
    return param


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------


async def require_jwt(
    request: Request,
    authorization: str | None = None,
) -> Principal:
    """FastAPI dependency that verifies a Bearer JWT and returns a Principal.

    The dependency never reads from ``Depends`` for the header — it
    inspects ``request.headers`` so the OpenAPI docs and call sites
    remain explicit. A 401 HTTPException is raised on every failure
    path.
    """
    header = authorization if authorization is not None else request.headers.get("Authorization")
    try:
        token = _extract_bearer(header)
        claims = verify_token(token, expected_type="access")
    except (JWTError, pyjwt.InvalidTokenError) as exc:
        fail = _failure(exc)
        logger.warning("auth.failed path=%s reason=%s", request.url.path, fail.code)
        raise HTTPException(status_code=fail.status, detail=fail.message) from exc
    principal = Principal(
        sub=claims.sub,
        role=claims.role,
        scopes=list(claims.scopes),
        jti=claims.jti,
        raw=claims.to_dict(),
    )
    logger.debug("auth.success sub=%s role=%s path=%s", principal.sub, principal.role, request.url.path)
    return principal


# ---------------------------------------------------------------------------
# Flask decorator
# ---------------------------------------------------------------------------


def _build_flask_decorator(  # noqa: C901 - small wrapper, kept explicit
    *,
    verify: bool = True,
):
    """Build a Flask view decorator that enforces a valid JWT.

    ``verify=True`` (default) raises 401 on a bad token. ``verify=False``
    is a no-op shim used to keep legacy route signatures compiling
    during the dual-mode window.
    """
    from flask import g, jsonify, request

    def decorator(view):
        if not verify:

            def passthrough(*args, **kwargs):
                return view(*args, **kwargs)

            passthrough.__name__ = view.__name__
            return passthrough

        def wrapper(*args, **kwargs):
            try:
                token = _extract_bearer(request.headers.get("Authorization"))
                claims = verify_token(token, expected_type="access")
            except (JWTError, pyjwt.InvalidTokenError) as exc:
                fail = _failure(exc)
                logger.warning(
                    "auth.failed path=%s reason=%s",
                    request.path,
                    fail.code,
                )
                return jsonify({"error": fail.message, "code": fail.code}), fail.status
            principal = Principal(
                sub=claims.sub,
                role=claims.role,
                scopes=list(claims.scopes),
                jti=claims.jti,
                raw=claims.to_dict(),
            )
            g.principal = principal
            logger.debug(
                "auth.success sub=%s role=%s path=%s",
                principal.sub,
                principal.role,
                request.path,
            )
            return view(*args, **kwargs)

        wrapper.__name__ = view.__name__
        return wrapper

    return decorator


def jwt_required(view=None, *, enabled: bool = True):
    """Flask decorator: ``@jwt_required`` or ``@jwt_required(enabled=False)``.

    Mirrors the shape of :func:`core.auth.require_api_key` so call sites
    can be migrated by replacing the decorator name only.
    """
    if view is not None and callable(view):
        return _build_flask_decorator(verify=True)(view)
    return _build_flask_decorator(verify=enabled)


# Back-compat alias matching ADR-0009 verbatim.
require_jwt_flask = jwt_required


__all__ = [
    "jwt_required",
    "require_jwt",
    "require_jwt_flask",
]


def _ensure_flask_imports() -> None:  # pragma: no cover - import guard
    """Helper used by tests to confirm Flask is available without forcing it."""
    import flask  # noqa: F401
