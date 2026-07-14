"""Tests for P2-04 RAG observability metrics.

Validates that the new labeled metrics fire at the right call sites:
  * RAG_QUERIES_TOTAL{status, backend, domain}  - on every retrieve()
  * RAG_ERRORS_TOTAL{stage, kind}              - on every failure
  * RAG_LATENCY_SECONDS                         - observed on each query
  * RAG_CHUNKS_RETURNED                         - Histogram of per-query count
  * RAG_RELEVANCE_AVG                           - Gauge of last query avg
  * RAG_BM25_REFRESH_TIMESTAMP                  - Gauge set on refresh

These tests mock pgvector and the embedding client so they run without a live
database.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from tools.metrics_server import (
    RAG_BM25_REFRESH_TIMESTAMP,
    RAG_CHUNKS_RETURNED,
    RAG_ERRORS_TOTAL,
    RAG_LATENCY_SECONDS,
    RAG_QUERIES_TOTAL,
    RAG_RELEVANCE_AVG,
)


def _counter_total(metric) -> float:
    """Sum a Counter's value across all label combinations."""
    total = 0.0
    for fam in metric.collect():
        for sample in fam.samples:
            if sample.name.endswith("_total"):
                total += sample.value
    return total


def _label_value(metric, **labels) -> float:
    """Return the sum of samples matching the given label set."""
    total = 0.0
    for fam in metric.collect():
        for sample in fam.samples:
            if all(sample.labels.get(k) == v for k, v in labels.items()):
                total += sample.value
    return total


def _histogram_count(metric) -> float:
    """Return the _count sample of a Histogram (number of observations)."""
    for fam in metric.collect():
        for sample in fam.samples:
            if sample.name.endswith("_count"):
                return sample.value
    return 0.0


def _make_async_pool(rows):
    """Return a MagicMock asyncpg.Pool whose `acquire()` yields a conn
    whose `fetch()` returns the given rows.
    """
    conn = MagicMock()
    conn.fetch = AsyncMock(return_value=rows)
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=conn)
    cm.__aexit__ = AsyncMock(return_value=None)

    pool = MagicMock()
    pool.acquire = MagicMock(return_value=cm)
    return pool


# ─── RAGClient: pgvector path ───────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rag_client_retrieve_increments_queries_total_ok():
    """A successful pgvector retrieve bumps RAG_QUERIES_TOTAL{status=ok}."""
    from core.rag_client import RAGClient, RAGConfig

    cfg = RAGConfig(backend="pgvector", pg_dsn="postgresql://x")
    client = RAGClient.__new__(RAGClient)
    client.config = cfg
    client.embedding = MagicMock()
    client.embedding.embed_one = AsyncMock(return_value=[0.1] * 768)
    fake_row = {
        "doc_id": "00000000-0000-0000-0000-000000000001",
        "source": "s",
        "title": "t",
        "body": "b",
        "domain": "trading",
        "score": 0.9,
    }
    client._pg_pool = _make_async_pool([fake_row])

    before = _label_value(
        RAG_QUERIES_TOTAL,
        status="ok",
        backend="pgvector",
        domain="trading",
    )
    chunks = await client.retrieve("q", top_k=1, domain="trading")
    after = _label_value(
        RAG_QUERIES_TOTAL,
        status="ok",
        backend="pgvector",
        domain="trading",
    )

    assert len(chunks) == 1
    assert after > before, f"queries_total status=ok should rise: {before} -> {after}"
    # Latency histogram count should also rise.
    assert _histogram_count(RAG_LATENCY_SECONDS) > 0
    # Chunks-returned histogram should observe at least one sample.
    assert _histogram_count(RAG_CHUNKS_RETURNED) > 0
    # Avg relevance gauge should be > 0 (we returned one chunk with score 0.9).
    assert RAG_RELEVANCE_AVG._value.get() > 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rag_client_retrieve_on_error_bumps_errors_and_queries():
    """A pgvector retrieve failure (no fallback) bumps RAG_ERRORS_TOTAL and
    RAG_QUERIES_TOTAL{status=error}.
    """
    from core.rag_client import RAGClient, RAGConfig

    cfg = RAGConfig(backend="pgvector", pg_dsn="postgresql://x", legacy_fallback=False)
    client = RAGClient.__new__(RAGClient)
    client.config = cfg
    client.embedding = MagicMock()
    client.embedding.embed_one = AsyncMock(side_effect=RuntimeError("boom"))
    client._pg_pool = _make_async_pool(
        []
    )  # pool present, but embed fails before pool use

    before_errors = _label_value(
        RAG_ERRORS_TOTAL, stage="retrieve", kind="RuntimeError"
    )
    before_queries = _label_value(
        RAG_QUERIES_TOTAL,
        status="error",
        backend="pgvector",
        domain="trading",
    )
    with pytest.raises(RuntimeError):
        await client.retrieve("q", top_k=1, domain="trading")
    after_errors = _label_value(RAG_ERRORS_TOTAL, stage="retrieve", kind="RuntimeError")
    after_queries = _label_value(
        RAG_QUERIES_TOTAL,
        status="error",
        backend="pgvector",
        domain="trading",
    )

    assert after_errors > before_errors, (
        f"RAG_ERRORS_TOTAL{{stage=retrieve,kind=RuntimeError}} should rise: "
        f"{before_errors} -> {after_errors}"
    )
    assert (
        after_queries > before_queries
    ), f"RAG_QUERIES_TOTAL error should rise: {before_queries} -> {after_queries}"


# ─── PersistentBM25Retriever ────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_bm25_refresh_sets_timestamp_gauge():
    """refresh() advances RAG_BM25_REFRESH_TIMESTAMP to time.time()."""
    from knowledge.persistent_bm25_retriever import PersistentBM25Retriever
    from core.rag_client import RAGClient

    # Build a stub RAGClient whose get_all_chunks returns one fake chunk.
    client = MagicMock(spec=RAGClient)
    fake_chunk = MagicMock()
    fake_chunk.doc_id = "doc-1"
    fake_chunk.content = "hello world"
    fake_chunk.source = "s"
    fake_chunk.title = "t"
    fake_chunk.domain = "trading"
    client.get_all_chunks = AsyncMock(return_value=[fake_chunk])

    retriever = PersistentBM25Retriever(rag_client=client, ttl_seconds=0)
    before = RAG_BM25_REFRESH_TIMESTAMP._value.get()
    # Sleep a hair so the timestamp is observably different.
    await asyncio.sleep(0.01)
    await retriever.refresh()
    after = RAG_BM25_REFRESH_TIMESTAMP._value.get()

    assert (
        after > before
    ), f"BM25 timestamp should advance; before={before}, after={after}"
    assert after > 0, "Timestamp should be a real epoch (got 0)"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_bm25_refresh_records_latency_histogram():
    """refresh() observes RAG_LATENCY_SECONDS."""
    from knowledge.persistent_bm25_retriever import PersistentBM25Retriever
    from core.rag_client import RAGClient

    client = MagicMock(spec=RAGClient)
    client.get_all_chunks = AsyncMock(return_value=[])

    retriever = PersistentBM25Retriever(rag_client=client, ttl_seconds=0)
    before = _histogram_count(RAG_LATENCY_SECONDS)
    await retriever.refresh()
    after = _histogram_count(RAG_LATENCY_SECONDS)
    assert (
        after > before
    ), f"RAG_LATENCY_SECONDS._count should rise: {before} -> {after}"


# ─── Static checks on metric declarations ──────────────────────────────────


def test_metrics_have_no_name_collisions():
    """Each metric must declare a unique Prometheus name."""
    from tools import metrics_server as ms

    names: list[str] = []
    for name in dir(ms):
        if name.startswith("_") or name.isupper() is False:
            continue
        obj = getattr(ms, name)
        # Histogram and Counter have a `_name` attribute set by prometheus_client.
        for attr in ("_name",):
            if hasattr(obj, attr):
                names.append(getattr(obj, attr))
    duplicates = {n for n in names if names.count(n) > 1}
    assert not duplicates, f"Duplicate metric names: {duplicates}"


def test_legacy_aliases_still_importable():
    """Old code (e.g. external scripts) can still import RAG_QUERY_CACHE_HITS."""
    from tools.metrics_server import (
        RAG_QUERY_CACHE_HITS,
        RAG_QUERY_CACHE_MISSES,
        RAG_CHUNK_COUNT,
    )

    # They are now labeled Counters / a Gauge, but they must be importable.
    assert RAG_QUERY_CACHE_HITS is not None
    assert RAG_QUERY_CACHE_MISSES is not None
    assert RAG_CHUNK_COUNT is not None
