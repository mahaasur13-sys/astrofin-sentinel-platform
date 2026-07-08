"""Tests for PersistentBM25Retriever (P2-03c).

Mocks RAGClient.get_all_chunks (added in P2-03c) so the retriever
can be exercised without a real Postgres connection.
"""

from __future__ import annotations

import time  # noqa: F401  -- kept for debugging hooks
import uuid
from typing import List
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.rag_client import RetrievedChunk
from knowledge.persistent_bm25_retriever import PersistentBM25Retriever


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _make_chunk(content: str, doc_id: str | None = None) -> RetrievedChunk:
    return RetrievedChunk(
        content=content,
        source="test",
        title="",
        domain="",
        relevance_score=0.0,
        doc_id=doc_id or str(uuid.uuid4()),
        backend="pgvector",
    )


def _make_rag_client(chunks: List[RetrievedChunk]) -> MagicMock:
    client = MagicMock()
    client.get_all_chunks = AsyncMock(return_value=chunks)
    return client


# ─────────────────────────────────────────────────────────────────────────────
# Core: refresh + retrieve
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_first_retrieve_triggers_refresh():
    """If index is empty, retrieve() must build it before searching."""
    client = _make_rag_client(
        [
            _make_chunk("inflation rising across emerging markets"),
            _make_chunk("central bank raises rates to fight inflation"),
        ]
    )
    r = PersistentBM25Retriever(rag_client=client, ttl_seconds=300.0)

    assert not r.is_indexed
    results = await r.retrieve("inflation", top_k=2)

    assert r.is_indexed
    assert r._chunk_count == 2
    assert len(results) == 2
    assert all(r2.bm25_score is not None for r2 in results)
    contents = {r2.content for r2 in results}
    assert contents == {
        "inflation rising across emerging markets",
        "central bank raises rates to fight inflation",
    }


@pytest.mark.asyncio
async def test_explicit_refresh_rebuilds_index():
    """Calling refresh() must replace the in-memory index even if TTL not expired."""
    client = _make_rag_client([_make_chunk("old content")])
    r = PersistentBM25Retriever(rag_client=client, ttl_seconds=3600.0)
    await r.retrieve("old")  # build with 1 chunk
    assert r._chunk_count == 1

    # Replace corpus without TTL expiring
    client.get_all_chunks = AsyncMock(
        return_value=[
            _make_chunk("new content 1"),
            _make_chunk("new content 2"),
            _make_chunk("new content 3"),
        ]
    )
    await r.refresh()
    assert r._chunk_count == 3


@pytest.mark.asyncio
async def test_refresh_resets_age():
    """After refresh(), the index age must be near zero."""
    client = _make_rag_client([_make_chunk("alpha beta gamma")])
    r = PersistentBM25Retriever(rag_client=client)
    await r.retrieve("alpha")  # builds index

    # Force age > 0 by rewinding the timestamp
    r._indexed_at -= 100
    assert r.age_seconds > 50

    await r.refresh()
    assert r.age_seconds < 1.0


@pytest.mark.asyncio
async def test_refresh_handles_empty_corpus():
    """Empty corpus must not crash and must produce empty results."""
    client = _make_rag_client([])
    r = PersistentBM25Retriever(rag_client=client)
    assert not r.is_indexed

    await r.refresh()
    assert r.is_indexed
    assert r._chunk_count == 0
    assert await r.retrieve("q") == []


@pytest.mark.asyncio
async def test_ttl_triggers_refresh_on_stale_index():
    """After TTL expires, the next retrieve() must rebuild the index."""
    client = _make_rag_client([_make_chunk("v1 chunk")])
    r = PersistentBM25Retriever(rag_client=client, ttl_seconds=0.1)
    await r.retrieve("v1")
    assert r._chunk_count == 1

    # Change corpus + force staleness
    client.get_all_chunks = AsyncMock(
        return_value=[
            _make_chunk("v2 chunk A"),
            _make_chunk("v2 chunk B"),
        ]
    )
    r._indexed_at -= 1.0  # > ttl_seconds

    results = await r.retrieve("v2")
    assert r._chunk_count == 2
    assert any("v2" in r2.content for r2 in results)


@pytest.mark.asyncio
async def test_ttl_zero_disables_auto_refresh():
    """ttl_seconds=0 must never auto-refresh."""
    client = _make_rag_client([_make_chunk("original")])
    r = PersistentBM25Retriever(rag_client=client, ttl_seconds=0)
    await r.retrieve("original")

    # Change corpus but DO NOT age the index
    client.get_all_chunks = AsyncMock(return_value=[_make_chunk("never seen")])
    results = await r.retrieve("never")
    # Index still has only the original chunk
    assert r._chunk_count == 1
    assert all(r2.content == "original" for r2 in results)


@pytest.mark.asyncio
async def test_repeated_retrieve_does_not_rebuild():
    """If TTL is not expired, retrieve() must not re-fetch from pgvector."""
    client = _make_rag_client([_make_chunk("stable content")])
    r = PersistentBM25Retriever(rag_client=client, ttl_seconds=3600.0)

    await r.retrieve("stable")
    assert client.get_all_chunks.await_count == 1
    await r.retrieve("stable")
    assert client.get_all_chunks.await_count == 1  # still 1
    await r.retrieve("stable")
    assert client.get_all_chunks.await_count == 1


@pytest.mark.asyncio
async def test_domain_filter_passed_to_rag_client():
    """The retriever must pass its domain filter to RAGClient.get_all_chunks."""
    client = _make_rag_client([])
    r = PersistentBM25Retriever(rag_client=client, domain="trading")
    await r.refresh()
    client.get_all_chunks.assert_awaited_once_with(domain="trading")


@pytest.mark.asyncio
async def test_top_k_caps_results():
    """retrieve(top_k=N) must return at most N chunks even if corpus is larger."""
    chunks = [_make_chunk(f"term doc {i}") for i in range(20)]
    client = _make_rag_client(chunks)
    r = PersistentBM25Retriever(rag_client=client)
    results = await r.retrieve("term", top_k=5)
    assert len(results) == 5
