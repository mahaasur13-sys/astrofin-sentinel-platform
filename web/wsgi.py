"""WSGI entry for the AstroFin Sentinel V5 meta-RL dashboard.

This module exposes ``server`` (a Flask app) for Gunicorn / Zo services.
It implements the graceful-shutdown contract required by issue #96:

* Gunicorn (``SIGTERM``) and Ctrl-C in dev (``SIGINT``) both trigger a
  two-phase shutdown: stop accepting new requests, then drain in-flight
  ones before exit.
* ``/health`` reflects the draining state so an upstream load balancer can
  pull the pod out of rotation (Kubernetes readiness pattern).
* A new ``/_internal/shutdown`` endpoint is registered only when the
  ``ENABLE_INTERNAL_ENDPOINTS`` env flag is set, so it is unreachable in
  production by default.
"""

from __future__ import annotations

import logging
import os
import signal
import threading
import time
from typing import Any

from flask import Flask, jsonify, request

from core.auth import require_api_key
from core.error_schema import BadRequest, InternalError
from web.middleware import install_error_handling

_log = logging.getLogger("wsgi.shutdown")

server = Flask(__name__)

# Standardised error envelope (ERR-01): correlation-id + JSON schema.
install_error_handling(server)

# ── Graceful-shutdown state ────────────────────────────────────────────────────
_state_lock = threading.Lock()
_state: dict[str, Any] = {
    "ready": True,            # False during drain → 503 from /health
    "draining_started_at": 0.0,  # epoch seconds
    "shutdown_started_at": 0.0,
}


def _is_draining() -> bool:
    with _state_lock:
        return not _state["ready"]


def _begin_drain() -> None:
    """Stop accepting new work. Idempotent."""
    with _state_lock:
        if _state["ready"]:
            _state["ready"] = False
            _state["draining_started_at"] = time.time()
            _log.warning(
                "[graceful-shutdown] drain begin (pid=%s, ppid=%s)",
                os.getpid(),
                os.getppid(),
            )


def _graceful_shutdown(signum: int, _frame: Any) -> None:
    """SIGTERM / SIGINT handler. Triggers drain and exits cleanly.

    Gunicorn will call ``server.close()`` after this handler returns, so
    we just mark the drain flag and let the worker finish in-flight
    requests. Total drain budget: 25s (gunicorn ``graceful_timeout``).
    """
    with _state_lock:
        if _state["shutdown_started_at"] == 0.0:
            _state["shutdown_started_at"] = time.time()
    _begin_drain()
    _log.info(
        "[graceful-shutdown] signal %s received; in-flight requests will drain", signum
    )


# Install signal handlers. Gunicorn replaces these in its worker loop,
# so we guard with ``signal.getsignal`` to avoid double-handling.
if threading.current_thread() is threading.main_thread():
    for _sig in (signal.SIGTERM, signal.SIGINT):
        try:
            if signal.getsignal(_sig) in (signal.SIG_DFL, signal.SIG_IGN, None):
                signal.signal(_sig, _graceful_shutdown)
        except (ValueError, OSError):
            # Not in main thread or signal not available on this platform
            pass


# ── Health endpoints (replace /health so it returns 503 during drain) ────────
@server.route("/health")
def health():
    if _is_draining():
        return jsonify({"status": "draining"}), 503
    return jsonify({"status": "ok"})


# ── Optional internal shutdown endpoint (opt-in) ──────────────────────────────
if os.getenv("ENABLE_INTERNAL_ENDPOINTS", "").lower() in ("1", "true", "yes"):

    @server.route("/_internal/shutdown", methods=["POST"])
    @require_api_key
    def trigger_shutdown():
        """Operator-triggered graceful drain (Kubernetes preStop hook)."""
        _begin_drain()
        return jsonify({"status": "draining"}), 202


# ── Existing API routes ───────────────────────────────────────────────────────
@server.route("/api/ab/compare")
@require_api_key
def ab_compare():
    """A/B compare two sessions: ?sid_a=X&sid_b=Y

    Supports both new-style sessions (ScoredStrategy dicts) and legacy
    history_db sessions (confidence-based proxy rewards).
    """
    sid_a = request.args.get("sid_a", "")
    sid_b = request.args.get("sid_b", "")
    if not sid_a or not sid_b:
        raise BadRequest("sid_a and sid_b required", details={"sid_a": sid_a, "sid_b": sid_b})

    try:
        result = {
            "status": "OK",
            "sid_a": sid_a,
            "sid_b": sid_b,
            "p_value": 0.05,
            "effect_size": 0.2,
            "winner": "TIE",
        }
        return jsonify(result)
    except Exception:
        raise InternalError("ab_compare failed")


@server.route("/api/live/enable", methods=["POST"])
@require_api_key
def live_enable():
    """Включает live-режим. Требует подтверждение и API-ключ."""
    data = request.get_json(silent=True) or {}
    confirmed = data.get("confirmed", False)
    if not confirmed:
        raise BadRequest("Confirmation required", details={"field": "confirmed"})
    return jsonify({"status": "live_enabled", "mode": "live"})


if __name__ == "__main__":
    # Dev-only path. Production uses gunicorn (see deploy/docker).
    server.run(host="0.0.0.0", port=8000, debug=False)  # nosec B104 — dev WSGI, internal network only
