"""Persistent BM25 retriever (P2-03c).

Builds and maintains a BM25 index over the `documents` table (pgvector, 0009).
Source of truth is the same table the vector retriever reads from, so the
lexical and dense halves of HybridRetriever are guaranteed to search the same
corpus.

Refresh strategy is hybrid:
  * TTL (default 300s): index is rebuilt lazily on first retrieve() after expiry.
  * Explicit refresh() : caller invokes after RAGClient.store() to make new
    chunks immediately searchable (e.g. right after document ingestion).

Design notes
------------
* The index is in-process (no external service). For a corpus of ~1k-10k
  chunks this is hundreds of ms to a few seconds; for 100k+ chunks consider
  an external BM25 service (out of scope for P2-03c).
* get_all_chunks() reads `body` + `doc_id` + `title` + `source` + `domain`
  from `documents` — no embeddings are pulled (saves 6KB/row bandwidth).
* Domain filter is applied at fetch time to keep the index in sync with
  whatever the vector retriever would see.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import List, Optional

from knowledge.bm25_retriever import BM25Retriever, Chunk
from core.rag_client import RAGClient
from tools.metrics_server import RAG_BM25_REFRESH_TIMESTAMP, RAG_LATENCY_SECONDS

logger = logging.getLogger(__name__)


@dataclass
class PersistentBM25Retriever:
    """BM25 retriever backed by pgvector `documents` table.

    Args:
        rag_client: Initialized RAGClient (must use pgvector backend).
        ttl_seconds: Auto-refresh interval. 0 = no TTL refresh.
        domain: Optional domain filter (None = all domains).
    """

    rag_client: RAGClient
    ttl_seconds: float = 300.0
    domain: Optional[str] = None

    _index: Optional[BM25Retriever] = None
    _indexed_at: float = 0.0  # epoch seconds; 0 = never indexed
    _chunk_count: int = 0

    async def _fetch_chunks(self) -> List[Chunk]:
        """Pull all chunks for the configured domain via RAGClient.

        Using RAGClient.get_all_chunks (added in P2-03c) keeps the
        pgvector query in one place and lets the retriever work whether
        the corpus lives in pgvector or the legacy FAISS backend.
        """
        retrieved = await self.rag_client.get_all_chunks(domain=self.domain)
        return [
            Chunk(
                id=str(rc.doc_id) if rc.doc_id is not None else "",
                content=rc.content,
                metadata={
                    "source": rc.source,
                    "title": rc.title,
                    "domain": rc.domain,
                },
            )
            for rc in retrieved
        ]

    async def _ensure_index(self) -> BM25Retriever:
        """Build index if absent or stale (TTL expired)."""
        now = time.monotonic()
        stale = (
            self._index is None
            or (self.ttl_seconds > 0 and (now - self._indexed_at) > self.ttl_seconds)
        )
        if stale:
            await self.refresh()
        assert self._index is not None, "refresh() failed to populate index"
        return self._index

    async def refresh(self) -> None:
        """Force a rebuild of the BM25 index from pgvector.

        Call this explicitly after RAGClient.store() if you need new chunks
        to be searchable without waiting for TTL expiry.

        Observability (P2-04):
          * RAG_LATENCY_SECONDS  — observed across the full rebuild.
          * RAG_BM25_REFRESH_TIMESTAMP — set to time.time() when the rebuild
            completes successfully. Prometheus scrapes this Gauge to compute
            index freshness (now - timestamp).
        """
        with RAG_LATENCY_SECONDS.time():
            t0 = time.monotonic()
            chunks = await self._fetch_chunks()
            self._index = BM25Retriever(chunks)
            self._indexed_at = time.monotonic()
            self._chunk_count = len(chunks)
        logger.info(
            "PersistentBM25Retriever: indexed %d chunks (domain=%s) in %.3fs",
            self._chunk_count, self.domain, self._indexed_at - t0,
        )
        RAG_BM25_REFRESH_TIMESTAMP.set(time.time())

    async def retrieve(self, query: str, top_k: int = 10) -> List[Chunk]:
        """Return top-k chunks by BM25 score, refreshing the index if stale."""
        index = await self._ensure_index()
        return index.retrieve(query, top_k=top_k)

    @property
    def is_indexed(self) -> bool:
        return self._index is not None

    @property
    def age_seconds(self) -> float:
        if self._indexed_at == 0.0:
            return float("inf")
        return time.monotonic() - self._indexed_at


__all__ = ["PersistentBM25Retriever"]
