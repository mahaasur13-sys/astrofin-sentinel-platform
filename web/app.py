#!/usr/bin/env python3
"""
web/app.py — AstroFinSentinelV5 Meta-RL Web Dashboard (ATOM-META-RL-006)

Production-ready Dash app with:
  - Gunicorn-compatible (via wsgi.py)
  - Configurable via environment variables
  - Security headers (via Flask middleware)
  - Health check endpoint
  - Data Room API endpoints

Run:
    Development: python app.py
    Production:  gunicorn -w 4 -b 0.0.0.0:8050 web.wsgi:app
    Zo Service:  registered via register_user_service
"""

from __future__ import annotations
import logging
import signal
import os
import sys
from datetime import datetime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html

from web.data_room import data_room_bp


# ── Config ──────────────────────────────────────────────────────────────────────
DEBUG = os.getenv("DEBUG_MODE", "false").lower() == "true"
PORT = int(os.getenv("PORT", "8050"))
SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(16).hex())
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")
from core.auth import validate_startup

validate_startup()

# ── App setup ──────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    title="AstroFinSentinelV5 • Meta-RL",
    suppress_callback_exceptions=True,
    assets_folder="assets",
    assets_url_path="assets",
    url_base_pathname=os.getenv("URL_BASE_PATHNAME", "/"),
    meta_tags=[
        {
            "name": "description",
            "content": "AstroFinSentinelV5 Meta-RL Strategy Discovery Engine",
        },
        {
            "name": "viewport",
            "content": "width=device-width, initial-scale=1",
        },
    ],
)

app.title = "AstroFinSentinelV5 • Meta-RL Engine"
app.secret_key = SECRET_KEY

# Flask server for Gunicorn
server = app.server

# ── Security middleware (CORS + headers + request-id) ──────────────────────────
from core.security_middleware import (
    install_security_middleware,
    add_security_headers_to_server,
)
install_security_middleware(
    server,
    allowed_origins=ALLOWED_ORIGINS.split(",") if ALLOWED_ORIGINS else ["*"],
)
add_security_headers_to_server(server)

# Register Flask blueprints
server.register_blueprint(data_room_bp)

# ── Standardised error handling (ERR-01) ──────────────────────────────────────
from web.middleware import install_error_handling
install_error_handling(server)

import logging as _logging
_log = _logging.getLogger(__name__)
_log.addHandler(_logging.NullHandler())
werkzeug_log = _logging.getLogger("werkzeug")
_log.setLevel(logging.WARNING if not DEBUG else logging.INFO)


class EngineRef:
    """Shared engine state between callbacks."""

    _engine = None


_engine_ref = EngineRef()


# ── Layout ──────────────────────────────────────────────────────────────────────
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Span("🧬", className="fs-3 me-2"),
                                html.H1(
                                    "AstroFinSentinelV5",
                                    className="d-inline fs-4",
                                ),
                                html.Span(
                                    " • ",
                                    className="text-muted",
                                ),
                                html.Span(
                                    "Meta-RL Engine",
                                    className="text-info",
                                ),
                                html.Span(
                                    " • ",
                                    className="text-muted",
                                ),
                                html.Span(
                                    "ATOM-META-RL-006",
                                    className="text-warning",
                                    id="header-version",
                                ),
                            ],
                            className="d-flex align-items-center",
                        ),
                    ],
                    width=9,
                ),
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Code(
                                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    className="text-muted small",
                                    id="header-time",
                                ),
                            ],
                            className="text-end",
                        ),
                    ],
                    width=3,
                ),
            ],
            className="mb-3 border-bottom pb-2",
        ),
        dcc.Tabs(
            id="main-tabs",
            value="tab-dashboard",
            children=[
                dcc.Tab(
                    label="📊 Dashboard",
                    value="tab-dashboard",
                ),
                dcc.Tab(
                    label="▶ Evolution",
                    value="tab-evolution",
                ),
                dcc.Tab(
                    label="📋 Sessions",
                    value="tab-sessions",
                ),
                dcc.Tab(
                    label="🔬 Explorer",
                    value="tab-explorer",
                ),
                dcc.Tab(
                    label="📡 Live",
                    value="tab-live",
                ),
            ],
        ),
        html.Div(
            id="tab-content",
            className="mt-3",
        ),
        dcc.Interval(
            id="clock-interval",
            interval=60000,
            n_intervals=0,
        ),
    ],
    fluid=True,
    className="pe-4 ps-4 pt-3",
)


@app.callback(
    Output("header-time", "children"),
    Input("clock-interval", "n_intervals"),
)
def update_clock(_):
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ── Register callbacks ──────────────────────────────────────────────────────────
from web.callbacks import register_callbacks
from web.sessions_callbacks import register_sessions_callbacks

register_callbacks(app, _engine_ref)
register_sessions_callbacks(app)

_log.info(f"[DASH] AstroFinSentinelV5 ready → http://0.0.0.0:{PORT}")
_log.info(f"[DASH] Config: DEBUG={DEBUG} PORT={PORT} URL_BASE={os.getenv('URL_BASE_PATHNAME', '/')}")




# ── Graceful shutdown (SIGTERM) ────────────────────────────────────────────────
def _graceful_shutdown(signum, frame):  # noqa: ARG001
    _log.info("[DASH] Received signal %s — shutting down gracefully", signum)
    try:
        # Dash/Flask doesn't expose a clean shutdown; rely on host supervisor
        # (gunicorn / supervisord / Zo service manager) to reap the process.
        sys.exit(0)
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover — defensive  # noqa: BLE001
        _log.error("[DASH] Shutdown error: %s", exc)
        sys.exit(1)


signal.signal(signal.SIGTERM, _graceful_shutdown)
try:
    signal.signal(signal.SIGINT, _graceful_shutdown)
except Exception:  # pragma: no cover — SIGINT may be unavailable on Windows  # noqa: BLE001
    pass
# ── Global exception handler ─────────────────────────────────────────────────────
def _log_uncaught(exc_type, exc_value, exc_tb):
    """Log uncaught exceptions with full traceback instead of swallowing them."""
    _log.critical(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_tb),
    )


sys.excepthook = _log_uncaught


if __name__ == "__main__":

    app.run(
        debug=DEBUG,
        host="0.0.0.0",  # nosec B104 — dev dashboard, internal network only
        port=PORT,
    )
