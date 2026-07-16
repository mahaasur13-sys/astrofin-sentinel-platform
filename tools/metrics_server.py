#!/usr/bin/env python3
"""Prometheus metrics server for AstroFin Sentinel V5.

Optional authentication via METRICS_AUTH_ENABLED / METRICS_API_KEY.
"""

import argparse
import os
import time

from aiohttp import web
from prometheus_client import REGISTRY, Counter, Gauge, Histogram, generate_latest

# Metrics required by rag_retriever and other modules
CACHE_HITS = Counter("astrofin_cache_hits", "Cache hits")
CACHE_MISSES = Counter("astrofin_cache_misses", "Cache misses")
OLLAMA_STATUS = Gauge("astrofin_ollama_status", "Ollama service status (1=healthy)")
RAG_CHUNK_COUNT = Gauge("astrofin_rag_chunk_count", "Number of chunks in RAG index")
RAG_QUERY_CACHE_HITS = Counter("astrofin_rag_query_cache_hits", "RAG query cache hits")
RAG_QUERY_CACHE_MISSES = Counter("astrofin_rag_query_cache_misses", "RAG query cache misses")
RAG_RELEVANCE_SCORE = Histogram(
    "astrofin_rag_relevance_score",
    "Relevance score of RAG chunks",
    buckets=(0.1, 0.3, 0.5, 0.7, 0.9, 1.0),
)
AGENT_DURATION = Histogram(
    "astrofin_agent_duration_seconds",
    "Agent execution duration",
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30),
)
# ── HTTP request metrics (used by middleware below) ──────────────────────────
REQUEST_COUNT = Counter(
    "astrofin_requests_total",
    "Total HTTP requests served by the metrics server",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "astrofin_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)
BROKER_ERRORS = Counter("astrofin_broker_errors_total", "Broker API errors")
OLLAMA_AVAILABLE = Gauge(
    "astrofin_ollama_available",
    "Ollama service availability (1=available, 0=unavailable)",
)
# Default to healthy until a health-check reports otherwise.
OLLAMA_AVAILABLE.set(1)
from meta_rl.metrics import *  # re-export

METRICS_AUTH_ENABLED = os.getenv("METRICS_AUTH_ENABLED", "false").lower() == "true"
METRICS_API_KEY = os.getenv("METRICS_API_KEY", "")


async def metrics_handler(request):
    # Check authentication if enabled
    if METRICS_AUTH_ENABLED:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer ") or auth_header.split(" ", 1)[1] != METRICS_API_KEY:
            return web.Response(text="Unauthorized", status=401)
    return web.Response(body=generate_latest(REGISTRY), content_type="text/plain")


async def health_handler(request):
    return web.Response(text="OK", content_type="text/plain")


@web.middleware
async def metrics_middleware(request, handler):
    """Record per-request metrics for the aiohttp metrics server."""
    start = time.perf_counter()
    try:
        response = await handler(request)
        status = str(getattr(response, "status", 200))
        return response
    except web.HTTPException as exc:
        status = str(exc.status)
        raise
    except Exception:  # noqa: BLE001 - we just want to observe the failure
        status = "500"
        raise
    finally:
        try:
            route = request.match_info.route
            endpoint = (
                route.resource.canonical
                if route is not None and getattr(route, "resource", None) is not None
                else request.path
            )
            REQUEST_COUNT.labels(request.method, endpoint, status).inc()
            REQUEST_LATENCY.labels(request.method, endpoint).observe(time.perf_counter() - start)
        except Exception:  # noqa: BLE001 - metrics must never break a request
            pass


def run_server(port: int = 9091, host: str = "0.0.0.0"):
    app = web.Application(middlewares=[metrics_middleware])
    app.router.add_get("/metrics", metrics_handler)
    app.router.add_get("/health", health_handler)
    web.run_app(app, port=port, host=host, print=lambda *_: None)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AstroFin Prometheus metrics server")
    parser.add_argument("--port", type=int, default=9091)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    run_server(args.port, args.host)

# ── Missing metrics for backtest and observability ─────────────────────────────
BACKTEST_REAL_RUNS = Counter("astrofin_backtest_real_runs", "Real data backtest runs")
BACKTEST_SYNTHETIC_RUNS = Counter("astrofin_backtest_synthetic_runs", "Synthetic data backtest runs")
AGENT_SELECTION_COUNTS = Counter("astrofin_agent_selection_counts", "Agent selection counts", ["agent"])
THOMPSON_PARAMS = Gauge("astrofin_thompson_params", "Thompson Sampling parameters", ["pool"])
