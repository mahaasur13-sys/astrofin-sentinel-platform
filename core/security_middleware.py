"""core/security_middleware.py — Production security middleware for Flask.

Provides:
  - Security headers (HSTS, X-Content-Type-Options, X-Frame-Options, …)
  - Per-request UUIDv7 X-Request-Id (request + response)
  - Optional CORS init helper (flask-cors) with origin allow-list from env.

Used by:
  - web/app.py (Dash → Flask `server`)
  - deploy/docker/supervisord.conf workers

All functions are no-op safe when called multiple times.
"""
from __future__ import annotations

import logging
import os
import uuid
from typing import Iterable

from flask import Flask, g, request

_log = logging.getLogger(__name__)

# ── Security headers ────────────────────────────────────────────────────────────
_DEFAULT_SECURITY_HEADERS: dict[str, str] = {
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}


def add_security_headers(response):
    """Apply the default security headers to ``response`` in-place.

    Existing headers of the same name are overwritten with our values, so
    upstream proxies can still set HSTS but the rest is opinionated.
    """
    for header, value in _DEFAULT_SECURITY_HEADERS.items():
        response.headers[header] = value
    return response


# ── Request-ID ─────────────────────────────────────────────────────────────────
_REQUEST_ID_HEADER = "X-Request-Id"


def _generate_request_id() -> str:
    """UUIDv7 (time-ordered) when available, else UUID4 fallback."""
    try:
        return str(uuid.uuid7())  # type: ignore[attr-defined]
    except AttributeError:
        return str(uuid.uuid4())


def install_request_id(app: Flask) -> None:
    """Attach a unique X-Request-Id to every request and response.

    The id is stored in ``flask.g.request_id`` for downstream code (logging,
    error handlers) and echoed back in the response header.
    """

    @app.before_request
    def _attach_request_id() -> None:  # noqa: WPS430
        incoming = request.headers.get(_REQUEST_ID_HEADER)
        g.request_id = incoming if incoming else _generate_request_id()
        g._request_start = None  # placeholder for future timing

    @app.after_request
    def _echo_request_id(response):  # noqa: WPS430
        rid = getattr(g, "request_id", None)
        if rid:
            response.headers[_REQUEST_ID_HEADER] = rid
        return response


# ── CORS ───────────────────────────────────────────────────────────────────────
def _parse_origins(raw: str | None) -> list[str]:
    if not raw or raw.strip() in ("", "*"):
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


def install_cors(app: Flask, allowed_origins: Iterable[str] | None = None) -> None:
    """Enable CORS on ``app`` using flask-cors.

    Origins come from ``allowed_origins`` first, falling back to the
    ``ALLOWED_ORIGINS`` env var (comma-separated, ``*`` = allow all).
    """
    try:
        from flask_cors import CORS  # type: ignore
    except ImportError:  # pragma: no cover — dev image may lack flask-cors
        _log.warning("flask-cors not installed; CORS disabled")
        return

    origins: list[str]
    if allowed_origins is None:
        origins = _parse_origins(os.getenv("ALLOWED_ORIGINS"))
    else:
        origins = list(allowed_origins) or ["*"]

    CORS(
        app,
        resources={r"/*": {"origins": origins}},
        expose_headers=["X-Request-Id"],
        supports_credentials=False,
    )


# ── Combined installer ─────────────────────────────────────────────────────────
def install_security(app: Flask) -> None:
    """One-shot installer used by ``web/app.py`` and tests.

    Wires: CORS → request-id before/after hooks → security-headers after hook.
    """
    install_cors(app)
    install_request_id(app)

    @app.after_request
    def _apply_headers(response):  # noqa: WPS430
        return add_security_headers(response)


def install_security_middleware(app) -> None:
    """Register CORS, request-ID and security headers on a Dash/Flask app.

    Works for both ``dash.Dash`` (which exposes ``app.server``) and a plain
    Flask ``app`` — we always operate on ``app.server`` (a Flask instance).
    """
    flask_app = getattr(app, "server", app)

    # 1. CORS — read allowed origins from env at call time so tests can override
    origins_env = os.environ.get("ALLOWED_ORIGINS", "*")
    origins: list[str] | str = [o.strip() for o in origins_env.split(",") if o.strip()] if origins_env != "*" else "*"
    CORS(
        flask_app,
        resources={r"/*": {"origins": origins}},
        expose_headers=["X-Request-ID"],
        supports_credentials=False,
    )

    # 2. Request-ID + security headers
    flask_app.before_request(_before_request)
    flask_app.after_request(_after_request)

    # 3. Global JSON error handlers
    @flask_app.errorhandler(Exception)
    def _on_exception(exc):  # type: ignore[no-untyped-def]
        from flask import jsonify, request

        rid = getattr(request, "request_id", str(uuid.uuid4()))
        flask_app.logger.exception("Unhandled error (request_id=%s)", rid)
        return jsonify({"error": "internal server error", "request_id": rid}), 500

    flask_app.logger.info(
        "[security_middleware] installed: CORS origins=%s, request-id=enabled", origins_env
    )
