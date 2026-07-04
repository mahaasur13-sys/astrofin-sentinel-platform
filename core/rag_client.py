"""
core/rag_client.py — Unified RAG client with single-writer + read-fanout.

Architecture (Sprint W3 / P2-02, P2-02d):
  - Single source of truth: pgvector (after migration).
  - Write path:    RAG_BACKEND=pgvector (default) → documents table.
                   RAG_BACKEND=faiss → legacy FAISS index (pre-migration).
  - Read path:     Always query the active backend first.
                   If RAG_LEGACY_FALLBACK=true AND active backend fails,
                   fall back to FAISS (read-only mirror).
  - No dual-write. No read-merge. No score combination across systems.

Configuration (env):
  RAG_BACKEND          = pgvector | faiss     (default: pgvector)
  RAG_LEGACY_FALLBACK  = true | false         (default: true during W3)
  AFS_PG_DSN           = postgresql://...     (required if RAG_BACKEND=pgvector)
  RAG_PROVIDER         = openai | ollama | stub  (passed to EmbeddingClient)
  RAG_EMBEDDING_DIM    = 1536 | 768           (default: 1536)

Public API:
  - RAGClient(config: RAGConfig | None = None)
  - await client.store(docs: list[Document]) -> StoreResult
  - await client.retrieve(query, top_k=5, domain=None) -> list[RetrievedChunk]
  - await client.health() -> HealthStatus
  - await client.aclose()

Related: SPRINT_3.md §4 (W3A), §5 (P2-02d). Tools/embedding_client.py is the
embedder; this module is the storage + retrieval layer.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

import asyncpg
import faiss
import numpy as np
from pydantic import BaseModel, Field

from tools.embedding_client import EmbeddingClient, EmbeddingConfig
from tools.metrics_server import (  # type: ignore[import-not-found]
    RAG_CHUNK_COUNT,
    RAG_QUERY_CACHE_HITS,
    RAG_QUERY_CACHE_MISSES,
    RAG_RELEVANCE_SCORE,
)

logger = logging.getLogger(__name__)

# ─── Configuration ──────────────────────────────────────────────────────────


class RAGConfig(BaseModel):
    backend: Literal["pgvector", "faiss"] = "pgvector"  # RAG_BACKEND env var
    legacy_fallback: bool = True
    pg_dsn: Optional[str] = None
    faiss_dir: str = "knowledge/indexes"
    top_k: int = 5
    min_score: float = 0.5
    pg_pool_min: int = 2
    pg_pool_max: int = 10
    pg_command_timeout: float = 10.0

    @classmethod
    def from_env(cls) -> "RAGConfig":
        """Build config from environment."""
        backend = os.getenv("RAG_BACKEND", "pgvector").lower()
        if backend not in ("pgvector", "faiss"):
            raise ValueError(f"RAG_BACKEND must be 'pgvector' or 'faiss', got {backend!r}")
        if backend == "pgvector" and not os.getenv("AFS_PG_DSN"):
            logger.warning(
                "RAG_BACKEND=pgvector but no AFS_PG_DSN; auto-falling back to faiss"
            )
            backend = "faiss"
        return cls(
            backend=backend,
            legacy_fallback=os.getenv("RAG_LEGACY_FALLBACK", "true").lower()
            in ("true", "1", "yes", "on"),
            pg_dsn=os.getenv("AFS_PG_DSN"),
            faiss_dir=os.getenv("RAG_FAISS_DIR", "knowledge/indexes"),
        )


# ─── Data shapes ────────────────────────────────────────────────────────────


@dataclass
class Document:
    """Input to store(). Source-agnostic."""

    content: str
    source: str
    title: str = ""
    domain: str = "general"
    source_type: str = "news"  # news | filing | report | ephemeris | social | macro
    metadata: dict = field(default_factory=dict)
    doc_id: Optional[uuid.UUID] = None  # server-assigned if None


@dataclass
class RetrievedChunk:
    content: str
    source: str
    title: str
    domain: str
    relevance_score: float
    doc_id: Optional[uuid.UUID] = None
    backend: str = ""  # which backend served this result


@dataclass
class StoreResult:
    inserted: int
    failed: int
    backend: str
    errors: list[str] = field(default_factory=list)


@dataclass
class HealthStatus:
    backend: str
    healthy: bool
    legacy_available: bool
    details: dict = field(default_factory=dict)


# ─── RAG client ─────────────────────────────────────────────────────────────


class RAGClient:
    """Single-writer, read-fanout RAG client.

    Construct once per process. Use `get_rag_client()` for the process-wide
    singleton (preferred in app code).
    """

    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or RAGConfig.from_env()
        self.embedding = EmbeddingClient()  # uses its own env
        self._pg_pool: Optional[asyncpg.Pool] = None
        self._faiss_cache: dict[str, tuple[faiss.Index, list[dict]]] = {}
        self._check_config()

    def _check_config(self) -> None:
        if self.config.backend == "pgvector" and not self.config.pg_dsn:
            raise ValueError(
                "AFS_PG_DSN is required when RAG_BACKEND=pgvector. "
                "Set the env var, or switch to RAG_BACKEND=faiss."
            )

    # ─── Lifecycle ──────────────────────────────────────────────────────────

    async def aclose(self) -> None:
        if self._pg_pool is not None:
            await self._pg_pool.close()
            self._pg_pool = None
        await self.embedding.aclose()

    async def _get_pg_pool(self) -> asyncpg.Pool:
        if self._pg_pool is None:
            self._pg_pool = await asyncpg.create_pool(
                dsn=self.config.pg_dsn,
                min_size=self.config.pg_pool_min,
                max_size=self.config.pg_pool_max,
                command_timeout=self.config.pg_command_timeout,
            )
        return self._pg_pool

    # ─── Store ──────────────────────────────────────────────────────────────

    async def store(self, docs: list[Document]) -> StoreResult:
        """Embed + insert documents into the active backend. No dual-write."""
        if not docs:
            return StoreResult(inserted=0, failed=0, backend=self.config.backend)

        if self.config.backend == "pgvector":
            return await self._store_pgvector(docs)
        return await self._store_faiss(docs)

    async def _store_pgvector(self, docs: list[Document]) -> StoreResult:
        pool = await self._get_pg_pool()
        # Embed all docs in a single batched call.
        vectors = await self.embedding.embed([d.content for d in docs])
        inserted = 0
        errors: list[str] = []
        async with pool.acquire() as conn:
            async with conn.transaction():
                for doc, vec in zip(docs, vectors, strict=True):
                    try:
                        vec_str = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
                        await conn.execute(
                            """
                            INSERT INTO documents
                                (doc_id, source, source_type, title, body,
                                 tokens, lang, metadata, embedding)
                            VALUES (COALESCE($1, gen_random_uuid()), $2, $3, $4, $5,
                                    $6, COALESCE($7, 'en'), $8::jsonb, $9::vector)
                            ON CONFLICT (doc_id) DO NOTHING
                            """,
                            doc.doc_id,
                            doc.source,
                            doc.source_type,
                            doc.title or doc.source,
                            doc.content,
                            max(1, len(doc.content) // 4),  # rough token estimate
                            None,  # lang: leave NULL → default 'en'
                            json.dumps(doc.metadata),
                            vec_str,
                        )
                        inserted += 1
                    except Exception as e:  # noqa: BLE001 — log per-doc, continue batch
                        errors.append(f"{doc.source}: {type(e).__name__}: {e}")
                        logger.exception("store: failed for doc %s", doc.source)
        RAG_CHUNK_COUNT.set(inserted)
        return StoreResult(
            inserted=inserted, failed=len(docs) - inserted,
            backend="pgvector", errors=errors,
        )

    async def _store_faiss(self, docs: list[Document]) -> StoreResult:
        """Legacy path: writes to per-domain FAISS index. Pre-migration only.

        Not concurrency-safe. Held under a module-level lock; not optimal
        for high-throughput writes. Kept for backwards compatibility during W3.
        """
        async with _FAISS_WRITE_LOCK:
            vectors = await self.embedding.embed([d.content for d in docs])
            faiss_dir = Path(self.config.faiss_dir)
            faiss_dir.mkdir(parents=True, exist_ok=True)
            index_path = faiss_dir / f"{docs[0].domain}.index"
            meta_path = faiss_dir / f"{docs[0].domain}.meta.json"

            if index_path.exists():
                index = faiss.read_index(str(index_path))
                chunks = json.loads(meta_path.read_text(encoding="utf-8"))
            else:
                dim = len(vectors[0])
                index = faiss.IndexFlatIP(dim)
                chunks = []

            arr = np.array(vectors, dtype="float32")
            # L2-normalize so IndexFlatIP gives cosine similarity
            arr = arr / np.linalg.norm(arr, axis=1, keepdims=True)
            index.add(arr)
            for doc in docs:
                chunks.append({
                    "id": doc.doc_id or str(uuid.uuid4())[:12],
                    "content": doc.content,
                    "source": doc.source,
                    "title": doc.title or doc.source,
                    "domain": doc.domain,
                })
            faiss.write_index(index, str(index_path))
            meta_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
        RAG_CHUNK_COUNT.set(len(docs))
        return StoreResult(inserted=len(docs), failed=0, backend="faiss")

    # ─── Retrieve ───────────────────────────────────────────────────────────

    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        domain: Optional[str] = None,
        min_score: Optional[float] = None,
    ) -> list[RetrievedChunk]:
        """Query active backend; on failure + legacy_fallback, retry FAISS.

        Args:
            query: Natural-language query string. Embedded with the configured
                embedding provider (OpenAI / Ollama / Stub).
            top_k: Max results to return. Defaults to RAGConfig.top_k (5).
            domain: Restrict to one domain (trading | technical | astrology |
                general). None = search all domains.
            min_score: Drop results below this relevance (0..1). Defaults to
                RAGConfig.min_score (0.5). Set to 0.0 to disable.

        Result order: primary backend results first, then legacy-only results
        (if fallback fired). NEVER merges scores across systems.
        """
        k = top_k or self.config.top_k
        threshold = min_score if min_score is not None else self.config.min_score
        try:
            if self.config.backend == "pgvector":
                results = await self._retrieve_pgvector(query, k, domain)
            else:
                results = await self._retrieve_faiss(query, k, domain)
        except Exception as e:  # noqa: BLE001
            if not self.config.legacy_fallback or self.config.backend == "faiss":
                raise
            logger.warning(
                "primary backend %s failed (%s) — falling back to FAISS",
                self.config.backend, type(e).__name__,
            )
            results = await self._retrieve_faiss(query, k, domain)
        # Apply min_score uniformly (both primary and legacy paths).
        if threshold > 0.0:
            results = [r for r in results if r.relevance_score >= threshold]
        return results

    async def _retrieve_pgvector(
        self, query: str, k: int, domain: Optional[str],
    ) -> list[RetrievedChunk]:
        pool = await self._get_pg_pool()
        qvec = await self.embedding.embed_one(query)
        qvec_str = "[" + ",".join(f"{x:.6f}" for x in qvec) + "]"

        # Domain filter is optional. NULL = no filter (all domains).
        sql = """
            SELECT doc_id, source, title, body, domain,
                   1 - (embedding <=> $1::vector) AS score
            FROM documents
            WHERE ($2::text IS NULL OR domain = $2)
            ORDER BY embedding <=> $1::vector
            LIMIT $3
        """
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, qvec_str, domain, k)
        results = [
            RetrievedChunk(
                content=r["body"],
                source=r["source"],
                title=r["title"] or "",
                domain=r["domain"],
                relevance_score=float(r["score"]),
                doc_id=r["doc_id"],
                backend="pgvector",
            )
            for r in rows
            if float(r["score"]) >= self.config.min_score
        ]
        self._update_rag_metrics(results)
        return results

    async def _retrieve_faiss(
        self, query: str, k: int, domain: Optional[str],
    ) -> list[RetrievedChunk]:
        qvec = await self.embedding.embed_one(query)
        q = np.array([qvec], dtype="float32")
        # L2-normalize so IndexFlatIP gives cosine similarity
        q = q / np.linalg.norm(q, axis=1, keepdims=True)

        domains = [domain] if domain else [
            p.stem for p in Path(self.config.faiss_dir).glob("*.index")
        ]
        all_results: list[RetrievedChunk] = []
        for d in domains:
            index, chunks = self._load_faiss_domain(d)
            if index is None or index.ntotal == 0:
                continue
            n = min(k, index.ntotal)
            scores, indices = index.search(q, n)
            for score, idx in zip(scores[0], indices[0], strict=False):
                if idx < 0:
                    continue
                c = chunks[idx]
                all_results.append(RetrievedChunk(
                    content=c["content"],
                    source=c["source"],
                    title=c.get("title", ""),
                    domain=c.get("domain", d),
                    relevance_score=float(score),
                    backend="faiss",
                ))

        all_results.sort(key=lambda x: x.relevance_score, reverse=True)
        # Dedupe by (source, title), keep top-k above threshold.
        seen: set = set()
        deduped: list[RetrievedChunk] = []
        for r in all_results:
            key = (r.source, r.title)
            if key in seen or r.relevance_score < self.config.min_score:
                continue
            seen.add(key)
            deduped.append(r)
        self._update_rag_metrics(deduped)
        return deduped[:k]

    def _load_faiss_domain(self, domain: str) -> tuple[Optional[faiss.Index], list[dict]]:
        if domain in self._faiss_cache:
            return self._faiss_cache[domain]
        faiss_dir = Path(self.config.faiss_dir)
        index_path = faiss_dir / f"{domain}.index"
        meta_path = faiss_dir / f"{domain}.meta.json"
        if not index_path.exists() or not meta_path.exists():
            self._faiss_cache[domain] = (None, [])  # type: ignore[assignment]
            return None, []
        index = faiss.read_index(str(index_path))
        chunks = json.loads(meta_path.read_text(encoding="utf-8"))
        self._faiss_cache[domain] = (index, chunks)
        return index, chunks

    @staticmethod
    def _update_rag_metrics(results: list[RetrievedChunk]) -> None:
        # RAG_RELEVANCE_SCORE is declared as a Histogram in tools/metrics_server.py
        try:
            if results:
                avg = sum(r.relevance_score for r in results) / len(results)
                RAG_RELEVANCE_SCORE.set(avg)
                RAG_CHUNK_COUNT.set(len(results))
                RAG_QUERY_CACHE_HITS.inc()  # semantic: a successful retrieval counts as a "hit"
            else:
                RAG_QUERY_CACHE_MISSES.inc()
        except Exception:
            pass

    # ─── Health ─────────────────────────────────────────────────────────────

    async def health(self) -> HealthStatus:
        details: dict = {}
        healthy = True
        legacy_avail = False
        if self.config.backend == "pgvector":
            try:
                pool = await self._get_pg_pool()
                async with pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                details["pgvector"] = "ok"
            except Exception as e:  # noqa: BLE001
                healthy = False
                details["pgvector"] = f"{type(e).__name__}: {e}"
        else:
            details["faiss"] = "ok (active backend)"
        # Check FAISS presence for fallback.
        for d in ("astrology", "technical", "trading"):
            idx, _ = self._load_faiss_domain(d)
            if idx is not None:
                legacy_avail = True
                details[f"faiss:{d}"] = f"{idx.ntotal} chunks"
        return HealthStatus(
            backend=self.config.backend,
            healthy=healthy,
            legacy_available=legacy_avail,
            details=details,
        )


# Module-level lock for FAISS writes (FAISS is not thread-safe).
_FAISS_WRITE_LOCK = asyncio.Lock()


# ─── Singleton ──────────────────────────────────────────────────────────────


_singleton: Optional[RAGClient] = None


def get_rag_client() -> RAGClient:
    """Process-wide singleton. Built on first call from env config."""
    global _singleton
    if _singleton is None:
        _singleton = RAGClient()
    return _singleton
