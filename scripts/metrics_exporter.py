#!/usr/bin/env python3
"""AstroFin Sentinel — Prometheus Metrics Exporter (standalone HTTP server).

Freeze-compliant: no changes to agents/, core/, meta_rl/, data_room/, orchestration/.
Uses the same prometheus_client metric registry as tools/metrics_server.py.

Usage:
    METRICS_PORT=9191 python scripts/metrics_exporter.py
    METRICS_AUTH_ENABLED=1 METRICS_API_KEY=secret python scripts/metrics_exporter.py

Scraped by: deploy/monitoring/prometheus.yml → job astrofin-metrics-exporter
Health:    GET /health → {"status":"ok","uptime_seconds":N}
Metrics:   GET /metrics → Prometheus text format
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import REGISTRY, CONTENT_TYPE_LATEST, generate_latest, Counter

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

EXPORTER_SCRAPES = Counter("astrofin_exporter_scrapes_total", "Total Prometheus scrape requests")
EXPORTER_ERRORS = Counter("astrofin_exporter_errors_total", "Metrics generation errors")

_start_time = time.time()

app = FastAPI(title="AstroFin Metrics Exporter", docs_url=None, redoc_url=None)


def _auth_enabled() -> bool:
    return os.environ.get("METRICS_AUTH_ENABLED", "").lower() in ("1", "true", "yes")


def _valid_api_key(request: Request) -> bool:
    if not _auth_enabled():
        return True
    expected = os.environ.get("METRICS_API_KEY", "")
    if not expected:
        return True
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:] == expected
    return False


@app.get("/health")
async def handle_health() -> JSONResponse:
    return JSONResponse({
        "status": "ok",
        "uptime_seconds": round(time.time() - _start_time, 2),
        "service": "astrofin-metrics-exporter",
    })


@app.get("/metrics")
async def handle_metrics(request: Request) -> Response:
    if not _valid_api_key(request):
        return Response(status_code=401, content="Unauthorized\n")
    EXPORTER_SCRAPES.inc()
    try:
        body = generate_latest(REGISTRY)
        return Response(content=body, media_type=CONTENT_TYPE_LATEST)
    except Exception:
        EXPORTER_ERRORS.inc()
        return Response(status_code=500, content="Internal error generating metrics\n")


@app.get("/")
async def handle_root() -> JSONResponse:
    return JSONResponse({
        "endpoints": {"/health": "liveness probe", "/metrics": "Prometheus scrape target"},
        "auth_enabled": _auth_enabled(),
    })


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AstroFin Prometheus Metrics Exporter")
    parser.add_argument(
        "--port", type=int,
        default=int(os.environ.get("METRICS_PORT", "9191")),
        help="Listen port (default: METRICS_PORT or 9191)",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("METRICS_HOST", "127.0.0.1"),
        help="Listen host (default: METRICS_HOST or 127.0.0.1)",
    )
    args = parser.parse_args(argv)

    print(f"[metrics_exporter] listening on {args.host}:{args.port}  auth={'on' if _auth_enabled() else 'off'}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning", access_log=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
