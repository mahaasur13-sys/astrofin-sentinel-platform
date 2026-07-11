"""API Key authentication for FastAPI and Flask routes."""

from __future__ import annotations

import inspect
import logging
import os
import secrets
from functools import wraps

from fastapi import Request
from flask import request as flask_request

from core.error_schema import Forbidden, InternalError, Unauthorized, format_error

logger = logging.getLogger(__name__)


_TRUTHY = {"true", "1", "yes", "on"}


def _api_key() -> str:
    """Read the API key from the environment on each call (per-request)."""
    return os.getenv("API_KEY", "")


def _auth_disabled() -> bool:
    """Read the API_KEY_AUTH_DISABLED flag from the environment on each call.

    Truthy values ("true"|"1"|"yes"|"on", case-insensitive) mean auth is OFF.
    Default: False (auth ON).
    """
    return os.getenv("API_KEY_AUTH_DISABLED", "").lower() in _TRUTHY


def _legacy_require_auth() -> bool:
    """Back-compat shim: invert REQUIRE_AUTH into the new disabled-flag space.

    Older deployments / configs still set REQUIRE_AUTH=true|false. We honour
    it as the opposite of API_KEY_AUTH_DISABLED and log a one-time deprecation
    note so operators can migrate.
    """
    legacy = os.getenv("REQUIRE_AUTH")
    if legacy is None:
        return False
    logger.warning(
        "core.auth: REQUIRE_AUTH is deprecated, use API_KEY_AUTH_DISABLED instead (inverted semantics)",
    )
    # REQUIRE_AUTH=true means auth ON, which == API_KEY_AUTH_DISABLED=false.
    return legacy.strip().lower() not in _TRUTHY


# Module-level shims kept for backward compatibility with imports that still
# reference ``core.auth.API_KEY`` / ``core.auth.REQUIRE_AUTH``. They are read
# once at import time; helpers above re-read env on every call.
API_KEY: str = _api_key()
# Effective auth-required flag at import time. Honour both:
#   - new API_KEY_AUTH_DISABLED=true  -> auth OFF
#   - legacy REQUIRE_AUTH=true|false (inverted) -> respected, deprecated
#   - none set -> auth ON
_require_auth_now: bool = True
if _auth_disabled():
    _require_auth_now = False
elif os.getenv("REQUIRE_AUTH") is not None:
    _require_auth_now = os.getenv("REQUIRE_AUTH", "true").strip().lower() in _TRUTHY
REQUIRE_AUTH: bool = _require_auth_now


def validate_startup() -> None:
    """Validate auth config at process start.

    Kept as a stable public symbol for ``web.app``/``web.wsgi`` startup hooks
    and existing tests; delegates to :func:`_ensure_key_configured`.
    """
    _ensure_key_configured()


def _ensure_key_configured() -> None:
    """Raise RuntimeError if auth is required but API_KEY is missing."""
    if not _auth_disabled() and (not _api_key() or _api_key().strip() == ""):
        raise RuntimeError("API_KEY_AUTH_DISABLED is false but API_KEY is empty or unset")


def _resolve_request(args, kwargs):
    """Return a (request, path) tuple from FastAPI or Flask context."""
    request: Request | None = kwargs.get("request")
    if request is not None:
        return request, request.url.path
    for a in args:
        if isinstance(a, Request):
            return a, a.url.path
    # Flask path: flask.request is a thread-local proxy.
    if flask_request:
        return flask_request, flask_request.path
    return None, None


def _check_key(request, path):
    """Return None if authorized, or a (body, status) tuple error response."""
    api_key = _api_key()
    if not api_key or api_key.strip() == "":
        logger.critical("Server misconfiguration: API key required but not set")
        return (
            format_error(InternalError("Server misconfiguration: API key required but not set")),
            500,
        )

    key = request.headers.get("X-API-Key") if hasattr(request, "headers") else None
    if not key:
        logger.warning("auth.failed endpoint=%s missing key", path)
        return format_error(Unauthorized("Missing API key")), 401
    if not secrets.compare_digest(key, api_key):
        logger.warning("auth.failed endpoint=%s wrong key", path)
        return format_error(Forbidden("Invalid API key")), 403
    logger.debug("auth.success endpoint=%s", path)
    return None


def require_api_key(func):
    """Decorator that works on both FastAPI (async) and Flask (sync) routes.

    On a 401/403 it returns a ``(body, status)`` tuple, which both FastAPI and
    Flask interpret as ``(response_body, status_code)``.
    """
    is_coro = inspect.iscoroutinefunction(func)

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        if _auth_disabled():
            return await func(*args, **kwargs)
        request, path = _resolve_request(args, kwargs)
        if request is None:
            return format_error(Unauthorized("Missing request")), 401
        err = _check_key(request, path)
        if err is not None:
            return err
        return await func(*args, **kwargs)

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        if _auth_disabled():
            return func(*args, **kwargs)
        request, path = _resolve_request(args, kwargs)
        if request is None:
            return format_error(Unauthorized("Missing request")), 401
        err = _check_key(request, path)
        if err is not None:
            return err
        return func(*args, **kwargs)

    return async_wrapper if is_coro else sync_wrapper


def verify_api_key(key: str) -> bool:
    """Standalone verification helper."""
    if _auth_disabled():
        return True
    _ensure_key_configured()
    if not key:
        return False
    return secrets.compare_digest(key, _api_key())
