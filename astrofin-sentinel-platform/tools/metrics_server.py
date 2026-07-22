#!/usr/bin/env python3
"""Prometheus metrics server for AstroFin Sentinel V5.

Optional authentication via METRICS_AUTH_ENABLED / METRICS_API_KEY.
"""

from __future__ import annotations

import argparse
import os

from aiohttp import web
from prometheus_client import REGISTRY, generate_latest, Counter, Gauge, Histogram

# Metrics required by rag_retriever and other modules
CACHE_HITS = Counter("astrofin_cache_hits", "Cache hits")
CACHE_MISSES = Counter("astrofin_cache_misses", "Cache misses")
OLLAMA_STATUS = Gauge("astrofin_ollama_status", "Ollama service status (1=healthy)")
# ── RAG metrics (P2-04 observability sprint) ───────────────────────────────
# RAG_CHUNK_COUNT: Gauge of the total corpus size (chunks currently in the
# active backend's index). Distinct from RAG_CHUNKS_RETURNED below, which
# tracks the per-query returned chunk count as a distribution.
RAG_CHUNK_COUNT = Gauge(
    "astrofin_rag_chunk_count",
    "Number of chunks in the RAG index",
)
RAG_CHUNKS_RETURNED = Histogram(
    "astrofin_rag_chunks_returned",
    "Number of chunks returned per RAG query (post-filter)",
    buckets=(0, 1, 2, 3, 5, 8, 13, 21),
)
# Unified query counter: replaces RAG_QUERY_CACHE_HITS / RAG_QUERY_CACHE_MISSES.
# Labels: status=ok|error, backend=pgvector|faiss|hybrid, domain=trading|...|all
RAG_QUERIES_TOTAL = Counter(
    "astrofin_rag_queries_total",
    "RAG queries, partitioned by status, backend, and domain",
    ["status", "backend", "domain"],
)
# RAG_ERRORS_TOTAL: counts failures across retrieve/store/refresh paths.
RAG_ERRORS_TOTAL = Counter(
    "astrofin_rag_errors_total",
    "RAG errors by stage and kind",
    ["stage", "kind"],
)
# RAG_LATENCY_SECONDS: end-to-end query latency in seconds.
RAG_LATENCY_SECONDS = Histogram(
    "astrofin_rag_latency_seconds",
    "End-to-end RAG query latency (seconds)",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
# Average relevance score across a single query (set as a gauge; the histogram
# of per-chunk scores is RAG_RELEVANCE_SCORE_HIST below). The old RAG_RELEVANCE_SCORE
# is now a Histogram; we keep its name so dashboards don't break, and we add a
# separate Gauge for the per-query average.
RAG_RELEVANCE_SCORE = Histogram(
    "astrofin_rag_relevance_score",
    "Relevance score distribution of RAG chunks",
    buckets=(0.1, 0.3, 0.5, 0.7, 0.9, 1.0),
)
RAG_RELEVANCE_AVG = Gauge(
    "astrofin_rag_relevance_avg",
    "Average relevance score of the most recent RAG query",
)
# BM25 index freshness: epoch seconds at which the in-process BM25 index was
# last built. Exposed via Gauge.set_function() so Prometheus scrapes a live
# value without a setter call.
RAG_BM25_REFRESH_TIMESTAMP = Gauge(
    "astrofin_rag_bm25_refresh_timestamp",
    "Unix epoch (seconds) of the last BM25 index build, or 0 if never built",
)
# Back-compat aliases (deprecated; remove in P2-05).
# We keep them as no-op Counters so old import paths don't break, but new
# code MUST use RAG_QUERIES_TOTAL{status=...} instead.
RAG_QUERY_CACHE_HITS = Counter(
    "astrofin_rag_query_cache_hits_legacy",
    "DEPRECATED: use astrofin_rag_queries_total{status='ok'} instead",
)
RAG_QUERY_CACHE_MISSES = Counter(
    "astrofin_rag_query_cache_misses_legacy",
    "DEPRECATED: use astrofin_rag_queries_total{status='error'} instead",
)
AGENT_DURATION = Histogram(
    "astrofin_agent_duration_seconds",
    "Agent execution duration",
    labelnames=("agent_name",),
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30),
)
from meta_rl.metrics import *  # re-export

METRICS_AUTH_ENABLED = os.getenv("METRICS_AUTH_ENABLED", "false").lower() == "true"
METRICS_API_KEY = os.getenv("METRICS_API_KEY", "")


async def metrics_handler(request):
    # Check authentication if enabled
    if METRICS_AUTH_ENABLED:
        auth_header = request.headers.get("Authorization", "")
        if (
            not auth_header.startswith("Bearer ")
            or auth_header.split(" ", 1)[1] != METRICS_API_KEY
        ):
            return web.Response(text="Unauthorized", status=401)
    return web.Response(body=generate_latest(REGISTRY), content_type="text/plain")


async def health_handler(request):
    return web.Response(text="OK", content_type="text/plain")


def run_server(port: int = 9091, host: str = os.environ.get("BIND_HOST", "127.0.0.1")):
    app = web.Application()
    app.router.add_get("/metrics", metrics_handler)
    app.router.add_get("/health", health_handler)
    web.run_app(app, port=port, host=host, print=lambda *_: None)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AstroFin Prometheus metrics server")
    parser.add_argument("--port", type=int, default=9091)
    parser.add_argument("--host", default=os.environ.get("BIND_HOST", "127.0.0.1"))
    args = parser.parse_args()
    run_server(args.port, args.host)

# ── Missing metrics for backtest and observability ─────────────────────────────
BACKTEST_REAL_RUNS = Counter("astrofin_backtest_real_runs", "Real data backtest runs")
BACKTEST_SYNTHETIC_RUNS = Counter(
    "astrofin_backtest_synthetic_runs", "Synthetic data backtest runs"
)
AGENT_SELECTION_COUNTS = Counter(
    "astrofin_agent_selection_counts", "Agent selection counts", ["agent"]
)
THOMPSON_PARAMS = Gauge(
    "astrofin_thompson_params", "Thompson Sampling parameters", ["pool"]
)
