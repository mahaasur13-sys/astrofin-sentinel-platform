#!/usr/bin/env python3
"""AstroFin Sentinel — Prometheus Metrics Exporter (standalone HTTP server).

Freeze-compliant: no changes to agents/, core/, meta_rl/, data_room/,
orchestration/. Uses the same prometheus_client metric registry as
tools/metrics_server.py.

Usage:
    METRICS_PORT=9091 python scripts/metrics_exporter.py
    # Optional auth:
    METRICS_AUTH_ENABLED=1 METRICS_API_KEY=secret python scripts/metrics_exporter.py

Scraped by: deploy/monitoring/prometheus.yml → job astrofin-metrics-exporter
Health:    GET /health → {"status":"ok","uptime_seconds":N}
Metrics:   GET /metrics → Prometheus text format (Content-Type: text/plain)
"""

from __future__ import annotations

import argparse
import os
import signal
import sys
import time
from pathlib import Path

# Ensure the project root is on sys.path so tools.metrics_server can be imported.
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from aiohttp import web
from prometheus_client import REGISTRY, generate_latest, Counter, Gauge

# Reuse the global metrics that core/rag_client.py and core/cache.py already use.
# The import side-effect registers them with REGISTRY — no duplication.
from tools.metrics_server import (  # noqa: F401 — side-effect import
    CACHE_HITS,
    CACHE_MISSES,
    OLLAMA_STATUS,
    RAG_CHUNK_COUNT,
    RAG_CHUNKS_RETURNED,
    RAG_QUERIES_TOTAL,
    RAG_ERRORS_TOTAL,
    RAG_LATENCY_SECONDS,
    BROKER_ERRORS,
    BACKTEST_REAL_RUNS,
    BACKTEST_SYNTHETIC_RUNS,
    AGENT_SELECTION_COUNTS,
    THOMPSON_PARAMS,
)

# ── Exporter-specific metrics ────────────────────────────────────────────────
EXPORTER_UPTIME = Gauge(
    "astrofin_exporter_uptime_seconds",
    "Exporter process uptime in seconds",
)
EXPORTER_SCRAPES = Counter(
    "astrofin_exporter_scrapes_total",
    "Total Prometheus scrape requests",
)
EXPORTER_ERRORS = Counter(
    "astrofin_exporter_errors_total",
    "Exporter internal errors",
)


def _auth_enabled() -> bool:
    return os.environ.get("METRICS_AUTH_ENABLED", "").lower() in ("1", "true", "yes")


def _valid_api_key(request: web.Request) -> bool:
    if not _auth_enabled():
        return True
    expected = os.environ.get("METRICS_API_KEY", "")
    if not expected:
        return True  # auth requested but no key configured — allow
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:] == expected
    return False


async def handle_metrics(request: web.Request) -> web.Response:
    """Prometheus /metrics endpoint — scraped by prometheus.yml."""
    if not _valid_api_key(request):
        return web.Response(status=401, text="Unauthorized\n")
    EXPORTER_SCRAPES.inc()
    try:
        body = generate_latest(REGISTRY)
        return web.Response(body=body, content_type="text/plain; version=0.0.4")
    except Exception:
        EXPORTER_ERRORS.inc()
        return web.Response(status=500, text="Internal error generating metrics\n")


async def handle_health(request: web.Request) -> web.Response:
    """Kubernetes-style liveness/readiness probe."""
    return web.json_response({
        "status": "ok",
        "uptime_seconds": round(time.time() - _start_time, 2),
        "service": "astrofin-metrics-exporter",
    })


async def handle_root(request: web.Request) -> web.Response:
    """Simple index: lists available endpoints."""
    return web.json_response({
        "endpoints": {
            "/health": "liveness probe",
            "/metrics": "Prometheus scrape target",
        },
        "auth_enabled": _auth_enabled(),
    })


_start_time: float = 0.0


def _on_shutdown(app: web.Application) -> None:
    pass


def build_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", handle_root)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/metrics", handle_metrics)
    app.on_shutdown.append(_on_shutdown)
    return app


def run_server(port: int, host: str) -> None:
    global _start_time
    _start_time = time.time()
    EXPORTER_UPTIME.set_function(lambda: time.time() - _start_time)

    app = build_app()
    print(f"[metrics_exporter] listening on {host}:{port}  auth={'on' if _auth_enabled() else 'off'}")
    web.run_app(app, host=host, port=port, print=None)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AstroFin Prometheus Metrics Exporter")
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("METRICS_PORT", "9091")),
        help="Listen port (default: METRICS_PORT or 9091)",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("METRICS_HOST", "127.0.0.1"),
        help="Listen host (default: METRICS_HOST or 127.0.0.1)",
    )
    args = parser.parse_args(argv)

    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))

    run_server(args.port, args.host)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
