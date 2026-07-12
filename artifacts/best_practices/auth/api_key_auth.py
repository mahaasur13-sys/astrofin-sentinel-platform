"""API Key authentication for FastAPI and Flask routes."""

from __future__ import annotations

import inspect
import logging
import secrets
from functools import wraps

from fastapi import Request
from flask import request as flask_request

from core.error_schema import Forbidden, Unauthorized, format_error
from core.settings import get_settings

logger = logging.getLogger(__name__)

# Backwards-compatible module-level constants. The single source of truth
# is :func:`core.settings.get_settings`; these bindings are refreshed at
# startup and on every call to :func:`reload_auth_state` so tests that
# mutate env vars pick up the new values without process restart.
REQUIRE_AUTH: bool = True
API_KEY: str = ""


def _refresh_auth_state() -> tuple[bool, str]:
    """(Re)read auth-related settings from the central config."""
    s = get_settings()
    key = s.api_key
    if hasattr(key, "get_secret_value"):
        key = key.get_secret_value()
    return s.require_auth, key


REQUIRE_AUTH, API_KEY = _refresh_auth_state()


def reload_auth_state() -> None:
    """Public hook for tests / startup that re-reads settings.

    Sets the module-level ``REQUIRE_AUTH`` and ``API_KEY`` globals from the
    central :class:`core.settings.Settings` instance. Use this in fixtures
    after monkey-patching env vars instead of importing new values.
    """
    global REQUIRE_AUTH, API_KEY
    REQUIRE_AUTH, API_KEY = _refresh_auth_state()


def validate_startup() -> None:
    """Validate auth config at process start.

    Kept as a stable public symbol for ``web.app``/``web.wsgi`` startup hooks
    and existing tests; delegates to :func:`_ensure_key_configured`.
    """
    _ensure_key_configured()


def _ensure_key_configured() -> None:
    """Raise RuntimeError if auth is required but API_KEY is missing."""
    if REQUIRE_AUTH and (not API_KEY or API_KEY.strip() == ""):
        raise RuntimeError("REQUIRE_AUTH is true but API_KEY is empty or unset")


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
    if not API_KEY or API_KEY.strip() == "":
        logger.critical("Server misconfiguration: API key required but not set")
        return (
            format_error({"code": "ServerMisconfiguration", "message": "API key not configured"}),
            500,
        )

    key = request.headers.get("X-API-Key") if hasattr(request, "headers") else None
    if not key:
        logger.warning("auth.failed endpoint=%s missing key", path)
        return format_error(Unauthorized("Missing API key")), 401
    if not secrets.compare_digest(key, API_KEY):
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
        if not REQUIRE_AUTH:
            return await func(*args, **kwargs)
        request, path = _resolve_request(args, kwargs)
        if request is None:
            return format_error({"code": "Unauthorized", "message": "Missing request"}), 401
        err = _check_key(request, path)
        if err is not None:
            return err
        return await func(*args, **kwargs)

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        if not REQUIRE_AUTH:
            return func(*args, **kwargs)
        request, path = _resolve_request(args, kwargs)
        if request is None:
            return format_error({"code": "Unauthorized", "message": "Missing request"}), 401
        err = _check_key(request, path)
        if err is not None:
            return err
        return func(*args, **kwargs)

    return async_wrapper if is_coro else sync_wrapper


def verify_api_key(key: str) -> bool:
    """Standalone verification helper."""
    _ensure_key_configured()
    if not key:
        return False
    return secrets.compare_digest(key, API_KEY)
