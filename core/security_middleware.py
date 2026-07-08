"""core/security_middleware.py — Production security middleware for Flask.

Provides:
  - Security headers (HSTS, X-Content-Type-Options, X-Frame-Options, CSP, …)
  - Per-request UUIDv4 X-Request-Id (request + response). UUIDv7 is unavailable
    on the supported Python runtimes (3.10–3.12 stdlib), so we use uuid4().
  - Optional CORS init helper (flask-cors) with origin allow-list from env.

Public API (stable, used by web/app.py and tests):
  - add_security_headers(response) -> Response
  - add_security_headers_to_server(server) -> None
  - install_security_middleware(app_or_server, allowed_origins=None) -> None
  - install_cors(app_or_server, allowed_origins=None) -> None
  - install_request_id(app_or_server) -> None
  - get_request_id() -> str

All functions are idempotent and no-op safe when called multiple times.

Used by:
  - web/app.py (Dash → Flask ``server``)
  - deploy/docker/supervisord.conf workers
"""
from __future__ import annotations

import logging
import os
import re
import uuid
from typing import Iterable

from flask import g, request

_log = logging.getLogger(__name__)

# ── Security headers ──────────────────────────────────────────────────────────
_DEFAULT_SECURITY_HEADERS: dict[str, str] = {
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    # Strict CSP for API/JSON responses. Dash pages may override via their own
    # after_request hook if they need inline scripts.
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    # NOTE: X-XSS-Protection is intentionally omitted — the modern
    # CSP-based model supersedes it and the legacy header has known
    # attack vectors. See OWASP "X-XSS-Protection: 0".
}

_REQUEST_ID_HEADER = "X-Request-ID"
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def _generate_request_id() -> str:
    """Return a fresh request ID.

    UUIDv7 is unavailable on the supported Python runtimes (3.10–3.12 stdlib);
    we use uuid4() instead. If a future runtime ships uuid7() we will switch.
    """
    return str(uuid.uuid4())


def add_security_headers(response):
    """Return ``response`` with the default security headers applied."""
    for k, v in _DEFAULT_SECURITY_HEADERS.items():
        response.headers.setdefault(k, v)
    return response


# ── Request-ID middleware ─────────────────────────────────────────────────────
def _attach_request_id() -> None:
    """Validate the inbound X-Request-Id (if any), otherwise mint a fresh one.

    We validate the client-supplied header against a strict format. Anything
    outside [A-Za-z0-9._-]{1,128} is dropped and a fresh UUIDv4 is generated.
    The value is stored on ``flask.g.request_id`` — both the echo hook and
    the error handler read from the same place, so they always agree.
    """
    incoming = request.headers.get(_REQUEST_ID_HEADER, "")
    if incoming and _REQUEST_ID_RE.match(incoming):
        g.request_id = incoming
    else:
        g.request_id = _generate_request_id()


def _echo_request_id(response):
    rid = getattr(g, "request_id", None) or _generate_request_id()
    response.headers.setdefault(_REQUEST_ID_HEADER, rid)
    return response


def get_request_id() -> str:
    """Return the request ID for the current request (or a fresh one)."""
    rid = getattr(g, "request_id", None)
    if rid:
        return rid
    rid = _generate_request_id()
    g.request_id = rid
    return rid


def install_request_id(app) -> None:
    """Register before/after hooks for request-ID handling."""
    flask_app = getattr(app, "server", app)
    flask_app.before_request(_attach_request_id)
    flask_app.after_request(_echo_request_id)


# ── CORS ──────────────────────────────────────────────────────────────────────
def install_cors(app, allowed_origins: Iterable[str] | str | None = None) -> None:
    """Wire CORS onto the Flask app using flask-cors.

    ``allowed_origins`` may be:
      - a list of origins (``["https://a", "https://b"]``)
      - the string ``"*"`` (default if env is ``"*"``)
      - ``None`` — falls back to env ``ALLOWED_ORIGINS`` or ``"*"``.
    """
    flask_app = getattr(app, "server", app)
    if allowed_origins is None:
        env = os.environ.get("ALLOWED_ORIGINS", "*")
        if env == "*":
            origins: list[str] | str = "*"
        else:
            origins = [o.strip() for o in env.split(",") if o.strip()]
    else:
        origins = allowed_origins

    try:
        from flask_cors import CORS  # type: ignore[import-not-found]
    except ImportError:  # pragma: no cover — defensive
        _log.warning(
            "flask-cors is not installed; CORS headers will not be set. "
            "Install flask-cors>=4.0.0 to enable CORS."
        )
        return

    CORS(
        flask_app,
        resources={r"/*": {"origins": origins}},
        expose_headers=[_REQUEST_ID_HEADER],
        supports_credentials=False,
    )


# ── Server-wide installer ─────────────────────────────────────────────────────
def add_security_headers_to_server(server) -> None:
    """Install the default after_request hook on a Flask server instance."""
    server.after_request(add_security_headers)


def install_security_middleware(
    app,
    allowed_origins: Iterable[str] | str | None = None,
) -> None:
    """Register CORS, request-ID, security headers and a JSON error handler.

    Works for both ``dash.Dash`` (which exposes ``app.server``) and a plain
    Flask ``app`` — we always operate on ``app.server`` (a Flask instance).
    """
    flask_app = getattr(app, "server", app)

    # 1. CORS — read allowed origins from env at call time so tests can override
    install_cors(flask_app, allowed_origins=allowed_origins)

    # 2. Request-ID + security headers
    install_request_id(flask_app)
    add_security_headers_to_server(flask_app)

    # 3. Global JSON error handler — always returns JSON, never leaks a stack
    # trace or an HTML page to API clients.
    @flask_app.errorhandler(Exception)
    def _on_exception(exc):  # type: ignore[no-untyped-def]
        from flask import jsonify

        rid = get_request_id()
        flask_app.logger.exception(
            "Unhandled error (request_id=%s): %s", rid, exc
        )
        return jsonify({"error": "internal server error", "request_id": rid}), 500

    _log.info(
        "[security_middleware] installed: CORS origins=%s, request-id=enabled, "
        "security-headers=enabled, json-error-handler=enabled",
        allowed_origins if allowed_origins is not None else os.environ.get("ALLOWED_ORIGINS", "*"),
    )
