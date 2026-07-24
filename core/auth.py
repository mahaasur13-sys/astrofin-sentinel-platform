"""API Key authentication for FastAPI and Flask routes."""

from __future__ import annotations

import inspect
import logging
import secrets
from functools import wraps

from fastapi import Request
from fastapi.responses import JSONResponse
from flask import request as flask_request

from core.error_schema import format_error
from core.settings import get_settings

logger = logging.getLogger(__name__)

REQUIRE_AUTH: bool = False
API_KEY: str = ""



def _ensure_key_configured() -> None:
    if REQUIRE_AUTH and (not API_KEY or API_KEY.strip() == ''):
        raise RuntimeError('REQUIRE_AUTH is true but API_KEY is empty or unset')


def validate_startup() -> None:
    _ensure_key_configured()

def _refresh_auth_state() -> tuple[bool, str]:
    s = get_settings()
    key = s.api_key
    if hasattr(key, "get_secret_value"):
        key = key.get_secret_value()
    return s.require_auth, key


REQUIRE_AUTH, API_KEY = _refresh_auth_state()


def reload_auth_state() -> None:
    global REQUIRE_AUTH, API_KEY
    REQUIRE_AUTH, API_KEY = _refresh_auth_state()


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        content=format_error({"code": code, "message": message}),
        status_code=status_code,
    )


def _resolve_request(args, kwargs):
    """Return a (request, path) tuple from FastAPI or Flask context."""
    request: Request | None = kwargs.get("request")
    if request is not None:
        return request, request.url.path
    for a in args:
        if isinstance(a, Request):
            return a, a.url.path
    # FastAPI contextvar fallback (for endpoints without explicit `request: Request`)
    try:
        from starlette.requests import request as _sr
    except ImportError:
        _sr = None
    if _sr:
        try:
            r = _sr.get()
            if r is not None:
                return r, r.url.path
        except (LookupError, RuntimeError):
            pass
    if flask_request:
        return flask_request, flask_request.path
    return None, None


def _check_key(request, path) -> JSONResponse | None:
    """Return an error JSONResponse if unauthorized, or None if authorized."""
    if not API_KEY or API_KEY.strip() == "":
        logger.critical("Server misconfiguration: API key required but not set")
        return _error_response(500, "ServerMisconfiguration", "API key not configured")

    key = None
    if hasattr(request, "headers"):
        key = request.headers.get("X-API-Key")
        if not key:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                key = auth_header[7:]

    if not key:
        logger.warning("auth.failed endpoint=%s missing key", path)
        return _error_response(401, "Unauthorized", "Missing API key")
    if not secrets.compare_digest(key, API_KEY):
        logger.warning("auth.failed endpoint=%s wrong key", path)
        return _error_response(403, "Forbidden", "Invalid API key")
    logger.debug("auth.success endpoint=%s", path)
    return None


def require_api_key(func):
    """Decorator that works on both FastAPI (async) and Flask (sync) routes.

    Returns a JSONResponse for 401/403 auth failures, and delegates to the
    wrapped endpoint on success. Uses starlette contextvar for FastAPI endpoints
    that don't have an explicit ``request: Request`` parameter.
    """
    is_coro = inspect.iscoroutinefunction(func)

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        if not REQUIRE_AUTH:
            return await func(*args, **kwargs)
        request, path = _resolve_request(args, kwargs)
        if request is None:
            return _error_response(401, "Unauthorized", "Missing request")
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
            return _error_response(401, "Unauthorized", "Missing request")
        err = _check_key(request, path)
        if err is not None:
            return err
        return func(*args, **kwargs)

    return async_wrapper if is_coro else sync_wrapper


def verify_api_key(key: str) -> bool:
    """Standalone verification helper."""
    if not key:
        return False
    if REQUIRE_AUTH and (not API_KEY or API_KEY.strip() == ""):
        raise RuntimeError("REQUIRE_AUTH is true but API_KEY is empty or unset")
    return secrets.compare_digest(key, API_KEY)
