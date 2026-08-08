"""
DAG Observability — OpenTelemetry tracing + Prometheus metrics for DAG nodes.

Integrates with the existing core.tracing module for OTEL and exports
Prometheus metrics via the global registry (scraped by Prometheus on :9191).

All functions gracefully degrade to no-ops when OTEL/Prometheus are unavailable.

Metrics exported:
    dag_node_duration_seconds       — Histogram (pipeline, node_id, level)
    dag_node_errors_total           — Counter   (pipeline, node_id, error_type)
    dag_cache_hits_total            — Counter   (cache_name, hit_type)
    dag_cache_misses_total          — Counter   (cache_name)
    dag_pipeline_run_total          — Counter   (pipeline, status)
    dag_pipeline_duration_seconds   — Histogram (pipeline)

Usage:
    from core.dag.observability import observe_node, observe_pipeline
    async with observe_node("RouterNode", "BTCUSDT_analysis", 0) as obs:
        trace_id = obs.get("trace_id", "")
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional

logger = logging.getLogger(__name__)

_ENABLED = os.getenv("DAG_OBSERVABILITY_ENABLED", "true").lower() == "true"

TRACER_NAME = "astrofin.dag"

# ---------------------------------------------------------------------------
# Prometheus metrics (lazy init)
# ---------------------------------------------------------------------------

_DAG_NODE_DURATION: Any = None
_DAG_NODE_ERRORS: Any = None
_DAG_CACHE_HITS: Any = None
_DAG_CACHE_MISSES: Any = None
_DAG_PIPELINE_RUN: Any = None
_DAG_PIPELINE_DURATION: Any = None
_METRICS_READY = False


def _init_prometheus() -> None:
    global _DAG_NODE_DURATION, _DAG_NODE_ERRORS, _DAG_CACHE_HITS
    global _DAG_CACHE_MISSES, _DAG_PIPELINE_RUN, _DAG_PIPELINE_DURATION
    global _METRICS_READY
    if _METRICS_READY:
        return
    try:
        from prometheus_client import Counter, Histogram

        _DAG_NODE_DURATION = Histogram(
            "dag_node_duration_seconds",
            "Duration of DAG node execution",
            labelnames=["pipeline", "node_id", "level"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
        )
        _DAG_NODE_ERRORS = Counter(
            "dag_node_errors_total",
            "Total DAG node errors",
            labelnames=["pipeline", "node_id", "error_type"],
        )
        _DAG_CACHE_HITS = Counter(
            "dag_cache_hits_total",
            "Total cache hits for prompt/RAG caches",
            labelnames=["cache_name", "hit_type"],
        )
        _DAG_CACHE_MISSES = Counter(
            "dag_cache_misses_total",
            "Total cache misses for prompt/RAG caches",
            labelnames=["cache_name"],
        )
        _DAG_PIPELINE_RUN = Counter(
            "dag_pipeline_run_total",
            "Total DAG pipeline runs",
            labelnames=["pipeline", "status"],
        )
        _DAG_PIPELINE_DURATION = Histogram(
            "dag_pipeline_duration_seconds",
            "DAG pipeline total execution time",
            labelnames=["pipeline"],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
        )
        _METRICS_READY = True
        logger.debug("[DAG observability] Prometheus metrics initialised")
    except ImportError:
        logger.debug("[DAG observability] prometheus_client not available — metrics disabled")
    except Exception as exc:
        logger.warning("[DAG observability] metrics init failed: %s", exc)


def _get_tracer():
    """Get OTEL tracer with graceful fallback."""
    try:
        from core.tracing import tracer
        if tracer is not None:
            return tracer
    except Exception:
        pass

    try:
        from opentelemetry import trace
        return trace.get_tracer(TRACER_NAME)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Public metrics recorders
# ---------------------------------------------------------------------------

def record_node_duration(
    pipeline: str,
    node_id: str,
    level: int,
    duration_s: float,
) -> None:
    """Record node duration histogram."""
    if not _ENABLED:
        return
    _init_prometheus()
    if _DAG_NODE_DURATION is not None:
        try:
            _DAG_NODE_DURATION.labels(
                pipeline=pipeline,
                node_id=node_id,
                level=str(level),
            ).observe(duration_s)
        except Exception:
            pass


def record_node_error(
    pipeline: str,
    node_id: str,
    error_type: str,
) -> None:
    """Increment node error counter."""
    if not _ENABLED:
        return
    _init_prometheus()
    if _DAG_NODE_ERRORS is not None:
        try:
            _DAG_NODE_ERRORS.labels(
                pipeline=pipeline,
                node_id=node_id,
                error_type=error_type,
            ).inc()
        except Exception:
            pass


def record_cache_hit(cache_name: str, hit_type: str = "exact") -> None:
    """Record a cache hit."""
    if not _ENABLED:
        return
    _init_prometheus()
    if _DAG_CACHE_HITS is not None:
        try:
            _DAG_CACHE_HITS.labels(cache_name=cache_name, hit_type=hit_type).inc()
        except Exception:
            pass


def record_cache_miss(cache_name: str) -> None:
    """Record a cache miss."""
    if not _ENABLED:
        return
    _init_prometheus()
    if _DAG_CACHE_MISSES is not None:
        try:
            _DAG_CACHE_MISSES.labels(cache_name=cache_name).inc()
        except Exception:
            pass


def record_pipeline_run(pipeline: str, status: str, duration_s: float) -> None:
    """Record pipeline run counter + duration histogram."""
    if not _ENABLED:
        return
    _init_prometheus()
    try:
        if _DAG_PIPELINE_RUN is not None:
            _DAG_PIPELINE_RUN.labels(pipeline=pipeline, status=status).inc()
        if _DAG_PIPELINE_DURATION is not None:
            _DAG_PIPELINE_DURATION.labels(pipeline=pipeline).observe(duration_s)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Async context managers for OTEL spans
# ---------------------------------------------------------------------------

@asynccontextmanager
async def observe_node(
    node_id: str,
    pipeline: str,
    level: int,
) -> AsyncIterator[dict[str, str]]:
    """
    Async context manager wrapping a DAG node execution.

    Yields a dict with 'trace_id' for downstream propagation.
    Automatically records span duration, errors and sets status.
    """
    obs_data: dict[str, str] = {"trace_id": ""}
    span = None
    tracer = _get_tracer() if _ENABLED else None

    if tracer is not None:
        try:
            span = tracer.start_as_current_span(
                f"DAG.{node_id}",
                attributes={
                    "dag.node_id": node_id,
                    "dag.pipeline": pipeline,
                    "dag.level": level,
                },
            )
            span_ctx = span.get_span_context() if hasattr(span, "get_span_context") else None
            if span_ctx and hasattr(span_ctx, "trace_id"):
                tid = span_ctx.trace_id
                obs_data["trace_id"] = format(tid, "032x") if isinstance(tid, int) else str(tid)
        except Exception:
            pass

    t0 = time.time()
    error_occurred = False

    try:
        yield obs_data
    except Exception:
        error_occurred = True
        raise
    finally:
        if span is not None:
            try:
                duration_ns = int((time.time() - t0) * 1_000_000_000)
                if hasattr(span, "set_attribute"):
                    span.set_attribute("dag.duration_ms", int(duration_ns / 1_000_000))
                if error_occurred and hasattr(span, "set_status"):
                    from opentelemetry.trace.status import Status, StatusCode
                    span.set_status(Status(StatusCode.ERROR))
                elif hasattr(span, "set_status"):
                    from opentelemetry.trace.status import Status, StatusCode
                    span.set_status(Status(StatusCode.OK))
                if hasattr(span, "end"):
                    span.end()
            except Exception:
                pass


@asynccontextmanager
async def observe_pipeline(
    pipeline: str,
    node_count: int = 0,
    max_level: int = 0,
    run_number: int = 0,
) -> AsyncIterator[dict[str, str]]:
    """
    Async context manager wrapping a full DAG pipeline run.

    Creates a root span for the entire run and yields trace_id
    for propagation to child node spans.
    """
    obs_data: dict[str, str] = {"trace_id": ""}
    span = None
    tracer = _get_tracer() if _ENABLED else None

    if tracer is not None:
        try:
            span = tracer.start_as_current_span(
                f"DAG.Run::{pipeline}",
                attributes={
                    "dag.pipeline": pipeline,
                    "dag.node_count": node_count,
                    "dag.max_level": max_level,
                    "dag.run_number": run_number,
                },
            )
            span_ctx = span.get_span_context() if hasattr(span, "get_span_context") else None
            if span_ctx and hasattr(span_ctx, "trace_id"):
                tid = span_ctx.trace_id
                obs_data["trace_id"] = format(tid, "032x") if isinstance(tid, int) else str(tid)
        except Exception:
            pass

    t0 = time.time()
    error_occurred = False

    try:
        yield obs_data
    except Exception:
        error_occurred = True
        raise
    finally:
        if span is not None:
            try:
                duration_ns = int((time.time() - t0) * 1_000_000_000)
                if hasattr(span, "set_attribute"):
                    span.set_attribute("dag.duration_ms", int(duration_ns / 1_000_000))
                if error_occurred and hasattr(span, "set_status"):
                    from opentelemetry.trace.status import Status, StatusCode
                    span.set_status(Status(StatusCode.ERROR))
                elif hasattr(span, "set_status"):
                    from opentelemetry.trace.status import Status, StatusCode
                    span.set_status(Status(StatusCode.OK))
                if hasattr(span, "end"):
                    span.end()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Cache metrics integration helpers
# ---------------------------------------------------------------------------

def _patch_prompt_cache_metrics(pc):
    """Monkey-patch PromptCache.get_exact/set_exact to emit Prometheus metrics."""
    if not _ENABLED:
        return

    _init_prometheus()
    if _DAG_CACHE_HITS is None and _DAG_CACHE_MISSES is None:
        return

    orig_get_exact = pc.get_exact

    def _get_exact(prompt, model="", ttl=None):
        result = orig_get_exact(prompt, model, ttl)
        if result is not None:
            record_cache_hit("prompt_cache", "exact")
        else:
            record_cache_miss("prompt_cache")
        return result

    pc.get_exact = _get_exact  # type: ignore[method-assign]

    if hasattr(pc, "get_semantic"):
        orig_get_semantic = pc.get_semantic
        def _get_semantic(prompt, threshold=0.95, model=""):
            result = orig_get_semantic(prompt, threshold, model)
            if result is not None:
                record_cache_hit("prompt_cache", "semantic")
            else:
                record_cache_miss("prompt_cache")
            return result
        pc.get_semantic = _get_semantic  # type: ignore[method-assign]


def _patch_session_rag_cache_metrics(sc):
    """Monkey-patch SessionRAGCache.get to emit Prometheus metrics."""
    if not _ENABLED:
        return

    _init_prometheus()
    if _DAG_CACHE_HITS is None and _DAG_CACHE_MISSES is None:
        return

    orig_get = sc.get

    def _get(query, top_k=3):
        result = orig_get(query, top_k)
        if result is not None:
            record_cache_hit("session_rag_cache", "exact")
        else:
            record_cache_miss("session_rag_cache")
        return result

    sc.get = _get  # type: ignore[method-assign]
