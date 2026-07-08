"""core/security_middleware.py — Production security middleware for Flask.

Provides:
  - Security headers (HSTS, X-Content-Type-Options, X-Frame-Options, CSP, ...)
  - Per-request UUIDv4 X-Request-Id (request + response) — note: generates
    UUIDv4 on Python 3.10-3.12 because uuid.uuid7 is not yet in stdlib.
  - Optional CORS init helper (flask-cors) with origin allow-list from env.

Used by:
  - web/app.py (Dash -> Flask `server`)
  - deploy/docker/supervisord.conf workers

All functions are no-op safe when called multiple times.
"""
from __future__ import annotations

import logging
import os
import re
import uuid

try:
    from flask_cors import CORS  # type: ignore
except ImportError:  # pragma: no cover - flask-cors is optional in some envs
    CORS = None  # type: ignore

from flask import Flask, g, request

_log = logging.getLogger(__name__)

# ── Security headers ──────────────────────────────────────────────────────────
_DEFAULT_SECURITY_HEADERS: dict[str, str] = {
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    # CSP: a strict default for API/JSON responses. Dash pages can override
    # via their own after_request hook if they need inline scripts.
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}

_REQUEST_ID_HEADER = "X-Request-ID"
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def _generate_request_id() -> str:
    """Return a fresh request id.

    The pinned Python runtime (3.10-3.12) does not ship ``uuid.uuid7`` in the
    standard library, so we fall back to ``uuid.uuid4``. Keep this function as
    the single point of change if the runtime constraint is relaxed.
    """
    return str(uuid.uuid4())


def _validated_request_id(candidate: str | None) -> str | None:
    """Return *candidate* if it matches a strict request-id pattern, else None.

    Defends against CRLF/log-forging: any non-[A-Za-z0-9._-] character is
    rejected. Length capped at 128 chars.
    """
    if not candidate:
        return None
    if _REQUEST_ID_RE.match(candidate):
        return candidate
    return None


def _attach_request_id() -> None:
    """Flask ``before_request`` hook: stamp ``g.request_id`` and request.environ."""
    raw = request.headers.get(_REQUEST_ID_HEADER)
    rid = _validated_request_id(raw) or _generate_request_id()
    g.request_id = rid
    request.environ["astrofin.request_id"] = rid


def _echo_request_id(response):  # type: ignore[no-untyped-def]
    """Flask ``after_request`` hook: echo the validated/generated id back."""
    rid = getattr(g, "request_id", None) or _generate_request_id()
    response.headers[_REQUEST_ID_HEADER] = rid
    return response


def add_security_headers(response):  # type: ignore[no-untyped-def]
    """Inject default security headers on *response* in-place and return it."""
    for name, value in _DEFAULT_SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    return response


def add_security_headers_to_server(response):  # type: ignore[no-untyped-def]
    """Alias used by ``web/app.py`` and tests — delegates to ``add_security_headers``."""
    return add_security_headers(response)


def install_cors(app) -> None:
    """Install flask-cors on *app* using ``ALLOWED_ORIGINS`` env (comma-separated)."""
    if CORS is None:  # pragma: no cover - defensive
        _log.warning("flask-cors is not installed; CORS headers will not be added")
        return
    origins_env = os.environ.get("ALLOWED_ORIGINS", "*")
    if origins_env.strip() == "*":
        origins: list[str] | str = "*"
    else:
        origins = [o.strip() for o in origins_env.split(",") if o.strip()]
    CORS(
        app,
        resources={r"/*": {"origins": origins}},
        expose_headers=[_REQUEST_ID_HEADER],
        supports_credentials=False,
    )


def install_request_id(app) -> None:
    """Register before/after hooks for request-id propagation."""
    app.before_request(_attach_request_id)
    app.after_request(_echo_request_id)


def install_security(app) -> None:
    """One-shot installer used by ``web/app.py`` and tests.

    Wires: CORS -> request-id before/after hooks -> security-headers after hook.
    """
    install_cors(app)
    install_request_id(app)

    @app.after_request
    def _apply_headers(response):  # type: ignore[no-untyped-def]
        return add_security_headers(response)


def install_security_middleware(
    app,
    allowed_origins: list[str] | str | None = None,
) -> None:
    """Register CORS, request-ID, and security headers on a Dash/Flask app.

    Works for both ``dash.Dash`` (which exposes ``app.server``) and a plain
    Flask ``app`` -- we always operate on ``app.server`` (a Flask instance).

    *allowed_origins* overrides the ``ALLOWED_ORIGINS`` env var for this
    install; pass ``"*"`` or a list of origins. ``None`` means "read from env".
    """
    flask_app: Flask = getattr(app, "server", app)

    # 1. CORS — read allowed origins from the explicit arg first, then env.
    if allowed_origins is None:
        origins_env = os.environ.get("ALLOWED_ORIGINS", "*")
        origins: list[str] | str = (
            "*"
            if origins_env.strip() == "*"
            else [o.strip() for o in origins_env.split(",") if o.strip()]
        )
    else:
        origins = allowed_origins
    if CORS is not None:  # pragma: no branch - covered above
        CORS(
            flask_app,
            resources={r"/*": {"origins": origins}},
            expose_headers=[_REQUEST_ID_HEADER],
            supports_credentials=False,
        )
    else:  # pragma: no cover - defensive
        flask_app.logger.warning("flask-cors is not installed; skipping CORS")

    # 2. Request-ID + security headers
    flask_app.before_request(_attach_request_id)
    flask_app.after_request(_echo_request_id)
    flask_app.after_request(add_security_headers_to_server)

    # 3. Global JSON error handler — log sanitized request path, return 500 JSON.
    @flask_app.errorhandler(Exception)
    def _on_exception(exc):  # type: ignore[no-untyped-def]
        from flask import jsonify

        rid = getattr(g, "request_id", _generate_request_id())
        # Sanitize path to avoid CRLF / log forging via untrusted input.
        safe_path = (request.path or "/").replace("\r", "\\r").replace("\n", "\\n")
        flask_app.logger.exception(
            "Unhandled error (request_id=%s, method=%s, path=%s)",
            rid,
            request.method,
            safe_path,
        )
        return jsonify({"error": "internal server error", "request_id": rid}), 500

    flask_app.logger.info(
        "[security_middleware] installed: CORS origins=%r, request-id=enabled",
        origins,
    )
