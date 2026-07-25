"""API Key authentication for FastAPI and Flask routes."""

from __future__ import annotations

import inspect
import logging
import secrets
from functools import wraps

from fastapi import Request
from fastapi.responses import JSONResponse
from flask import request as flask_request

from core.error_schema import Forbidden, InternalError, Unauthorized, format_error
from core.settings import get_settings

logger = logging.getLogger(__name__)

REQUIRE_AUTH: bool = False
API_KEY: str = ""


def _ensure_key_configured() -> None:
    if REQUIRE_AUTH and (not API_KEY or API_KEY.strip() == ""):
        raise RuntimeError("REQUIRE_AUTH is true but API_KEY is empty or unset")


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


# Map an HTTP status code to the matching error-envelope exception so the
# client receives a stable machine-readable ``code`` (UNAUTHORIZED/FORBIDDEN/…).
_EXC_BY_STATUS = {401: Unauthorized, 403: Forbidden, 500: InternalError}


def _envelope(status_code: int, message: str) -> dict:
    exc_cls = _EXC_BY_STATUS.get(status_code, InternalError)
    return format_error(exc_cls(message))


def _fastapi_error(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(content=_envelope(status_code, message), status_code=status_code)


def _flask_error(status_code: int, message: str):
    from flask import jsonify

    return jsonify(_envelope(status_code, message)), status_code


def _error_for(request, status_code: int, message: str):
    """Build a framework-appropriate error response for the active request.

    FastAPI/Starlette routes need a ``JSONResponse``; Flask routes need a
    ``(body, status)`` tuple. Returning a Starlette response from a Flask
    route makes Flask raise on ``make_response`` (HTTP 500), so the response
    type must match the framework of the resolved request.
    """
    if isinstance(request, Request):  # Starlette/FastAPI request
        return _fastapi_error(status_code, message)
    return _flask_error(status_code, message)


def _resolve_request(args, kwargs):
    """Return a (request, path) tuple from FastAPI or Flask context."""
    request: Request | None = kwargs.get("request")
    if request is not None:
        return request, request.url.path
    for a in args:
        if isinstance(a, Request):
            return a, a.url.path
    # Flask fallback: only meaningful inside an active Flask request context.
    try:
        if flask_request:
            return flask_request, flask_request.path
    except RuntimeError:
        pass
    return None, None


def _check_key(request, path) -> tuple[int, str] | None:
    """Return an ``(status_code, message)`` error tuple if unauthorized, else None."""
    if not API_KEY or API_KEY.strip() == "":
        logger.critical("Server misconfiguration: API key required but not set")
        return (500, "API key not configured")

    key = None
    if hasattr(request, "headers"):
        key = request.headers.get("X-API-Key")
        if not key:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                key = auth_header[7:]

    if not key:
        logger.warning("auth.failed endpoint=%s missing key", path)
        return (401, "Missing API key")
    if not secrets.compare_digest(key, API_KEY):
        logger.warning("auth.failed endpoint=%s wrong key", path)
        return (403, "Invalid API key")
    logger.debug("auth.success endpoint=%s", path)
    return None


def require_api_key(func):
    """Decorator that works on both FastAPI (async) and Flask (sync) routes.

    Returns a framework-appropriate error response for 401/403 auth failures
    (a Starlette ``JSONResponse`` for FastAPI, a ``(body, status)`` tuple for
    Flask) and delegates to the wrapped endpoint on success. FastAPI endpoints
    must declare an explicit ``request: Request`` parameter so the request can
    be resolved; Flask routes are resolved from the active request context.
    """
    is_coro = inspect.iscoroutinefunction(func)

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        # Async routes are always FastAPI/Starlette here.
        if not REQUIRE_AUTH:
            return await func(*args, **kwargs)
        request, path = _resolve_request(args, kwargs)
        if request is None:
            return _fastapi_error(401, "Missing request")
        err = _check_key(request, path)
        if err is not None:
            return _fastapi_error(*err)
        return await func(*args, **kwargs)

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        # Sync routes may be Flask *or* FastAPI, so the response type is chosen
        # from the resolved request object.
        if not REQUIRE_AUTH:
            return func(*args, **kwargs)
        request, path = _resolve_request(args, kwargs)
        if request is None:
            return _error_for(None, 401, "Missing request")
        err = _check_key(request, path)
        if err is not None:
            return _error_for(request, *err)
        return func(*args, **kwargs)

    return async_wrapper if is_coro else sync_wrapper


def verify_api_key(key: str) -> bool:
    """Standalone verification helper."""
    if not key:
        return False
    if REQUIRE_AUTH and (not API_KEY or API_KEY.strip() == ""):
        raise RuntimeError("REQUIRE_AUTH is true but API_KEY is empty or unset")
    return secrets.compare_digest(key, API_KEY)
