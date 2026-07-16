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
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Literal, Optional

import asyncpg
import faiss
import numpy as np
from pydantic import BaseModel

from tools.embedding_client import EmbeddingClient
from tools.metrics_server import (  # type: ignore[import-not-found]
    RAG_CHUNK_COUNT,
    RAG_CHUNKS_RETURNED,
    RAG_ERRORS_TOTAL,
    RAG_LATENCY_SECONDS,
    RAG_QUERIES_TOTAL,
    RAG_RELEVANCE_AVG,
)

logger = logging.getLogger(__name__)

# ─── Configuration ──────────────────────────────────────────────────────────


def _safe_int(name: str, default: int, min_val: int = 0) -> int:
    """Parse an env var as int; on bad input or below min_val, return default.

    Used by RAGConfig.from_env() so a malformed value (e.g. HYBRID_RRF_K=abc)
    cannot crash the process at startup — we log and fall back to the default.
    """
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        val = int(raw)
    except ValueError:
        logger.warning("env %s=%r is not an int; using default %d", name, raw, default)
        return default
    if val < min_val:
        logger.warning("env %s=%d below min %d; using default %d", name, val, min_val, default)
        return default
    return val


def _safe_float(name: str, default: float, min_val: float = 0.0) -> float:
    """Parse an env var as float; on bad input or below min_val, return default."""
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        val = float(raw)
    except ValueError:
        logger.warning("env %s=%r is not a float; using default %f", name, raw, default)
        return default
    if val < min_val:
        logger.warning("env %s=%f below min %f; using default %f", name, val, min_val, default)
        return default
    return val


class RAGConfig(BaseModel):
    backend: Literal["pgvector", "faiss"] = "pgvector"  # RAG_BACKEND env var
    legacy_fallback: bool = True
    pg_dsn: str | None = None
    faiss_dir: str = "knowledge/indexes"
    top_k: int = 5
    min_score: float = 0.5
    pg_pool_min: int = 2
    pg_pool_max: int = 10
    pg_command_timeout: float = 10.0
    # Hybrid (P2-03b): RRF fusion knobs. Read by HybridRetriever in P2-03c.
    # Defaults match the RRF paper (k=60) and balanced weights (1.0/1.0).
    hybrid_rrf_k: int = 60
    hybrid_vector_weight: float = 1.0
    hybrid_bm25_weight: float = 1.0

    @classmethod
    def from_env(cls) -> RAGConfig:
        """Build config from environment."""
        backend = os.getenv("RAG_BACKEND", "pgvector").lower()
        if backend not in ("pgvector", "faiss"):
            raise ValueError(f"RAG_BACKEND must be 'pgvector' or 'faiss', got {backend!r}")
        if backend == "pgvector" and not os.getenv("AFS_PG_DSN"):
            logger.warning("RAG_BACKEND=pgvector but no AFS_PG_DSN; auto-falling back to faiss")
            backend = "faiss"
        return cls(
            backend=backend,
            legacy_fallback=os.getenv("RAG_LEGACY_FALLBACK", "true").lower() in ("true", "1", "yes", "on"),
            pg_dsn=os.getenv("AFS_PG_DSN"),
            faiss_dir=os.getenv("RAG_FAISS_DIR", "knowledge/indexes"),
            # Hybrid env knobs (P2-03b). Defensive parsing: bad ints/floats
            # fall back to the dataclass defaults instead of crashing boot.
            hybrid_rrf_k=_safe_int("HYBRID_RRF_K", 60, min_val=1),
            hybrid_vector_weight=_safe_float("HYBRID_VECTOR_WEIGHT", 1.0, min_val=0.0),
            hybrid_bm25_weight=_safe_float("HYBRID_BM25_WEIGHT", 1.0, min_val=0.0),
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
    doc_id: uuid.UUID | None = None  # server-assigned if None


@dataclass
class RetrievedChunk:
    content: str
    source: str
    title: str
    domain: str
    relevance_score: float
    doc_id: uuid.UUID | None = None
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

    def __init__(self, config: RAGConfig | None = None):
        self.config = config or RAGConfig.from_env()
        self.embedding = EmbeddingClient()  # uses its own env
        self._pg_pool: asyncpg.Pool | None = None
        self._faiss_cache: dict[str, tuple[faiss.Index, list[dict]]] = {}
        self._check_config()

    def _check_config(self) -> None:
        if self.config.backend == "pgvector" and not self.config.pg_dsn:
            raise ValueError(
                "AFS_PG_DSN is required when RAG_BACKEND=pgvector. Set the env var, or switch to RAG_BACKEND=faiss."
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
        """Embed + insert documents into the active backend. No dual-write.

        Records: latency → RAG_LATENCY_SECONDS, errors → RAG_ERRORS_TOTAL{stage='store'}.
        """
        if not docs:
            return StoreResult(inserted=0, failed=0, backend=self.config.backend)

        with RAG_LATENCY_SECONDS.time():
            try:
                if self.config.backend == "pgvector":
                    return await self._store_pgvector(docs)
                return await self._store_faiss(docs)
            except Exception as e:  # noqa: BLE001
                RAG_ERRORS_TOTAL.labels(stage="store", kind=type(e).__name__).inc()
                logger.error(
                    "rag_store_failed: backend=%s, error=%s",
                    self.config.backend,
                    str(e),
                )
                raise

    async def get_all_chunks(self, domain: str | None = None) -> list[RetrievedChunk]:
        """Return every chunk in `documents` (pgvector backend) as RetrievedChunk.

        Used by PersistentBM25Retriever (P2-03c) to build a lexical index over
        the same corpus the vector retriever searches. Returns [] when the
        active backend is faiss (BM25 is then built from disk by the retriever
        itself). Domain filter is optional; NULL = all domains.
        """
        if self.config.backend != "pgvector":
            return []
        pool = await self._get_pg_pool()
        sql = """
            SELECT doc_id, source, title, body, domain, metadata
            FROM documents
            WHERE ($1::text IS NULL OR domain = $1)
        """
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, domain)
        return [
            RetrievedChunk(
                content=r["body"],
                source=r["source"],
                title=r["title"] or "",
                domain=r["domain"] or "",
                relevance_score=0.0,
                doc_id=r["doc_id"],
                backend="pgvector",
            )
            for r in rows
        ]

    async def _store_pgvector(self, docs: list[Document]) -> StoreResult:
        pool = await self._get_pg_pool()
        # Embed all docs in a single batched call.
        vectors = await self.embedding.embed([d.content for d in docs])
        inserted = 0
        errors: list[str] = []
        async with pool.acquire() as conn:
            # Outer transaction keeps the connection in a healthy state; an
            # aborted savepoint inside does NOT poison the outer transaction,
            # so we can continue with the next document after a per-doc failure.
            async with conn.transaction():
                for doc, vec in zip(docs, vectors, strict=True):
                    try:
                        # Nested asyncpg.transaction() creates a SAVEPOINT.
                        # On exception the savepoint is rolled back and the
                        # outer transaction can continue.
                        async with conn.transaction():
                            vec_str = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
                            await conn.execute(
                                """
                                INSERT INTO documents
                                    (doc_id, source, source_type, title, body,
                                     tokens, lang, domain, metadata, embedding)
                                VALUES (COALESCE($1, gen_random_uuid()), $2, $3, $4, $5,
                                        $6, COALESCE($7, 'en'), $8, $9::jsonb, $10::vector)
                                ON CONFLICT (doc_id) DO NOTHING
                                """,
                                doc.doc_id,
                                doc.source,
                                doc.source_type,
                                doc.title or doc.source,
                                doc.content,
                                max(1, len(doc.content) // 4),  # rough token estimate
                                None,  # lang: leave NULL → default 'en'
                                doc.domain or None,
                                json.dumps(doc.metadata),
                                vec_str,
                            )
                            inserted += 1
                    except Exception as e:  # noqa: BLE001 — log per-doc, continue batch
                        errors.append(f"{doc.source}: {type(e).__name__}: {e}")
                        logger.exception("store: failed for doc %s", doc.source)
        RAG_CHUNK_COUNT.set(inserted)
        return StoreResult(
            inserted=inserted,
            failed=len(docs) - inserted,
            backend="pgvector",
            errors=errors,
        )

    async def _store_faiss(self, docs: list[Document]) -> StoreResult:
        """Legacy path: writes to per-domain FAISS index. Pre-migration only.

        Not concurrency-safe. Held under a module-level lock; not optimal
        for high-throughput writes. Kept for backwards compatibility during W3.
        """
        # Guard: mixed-domain batches used to be silently written to docs[0].domain,
        # which corrupted retrieval. Reject explicitly so callers can split the batch.
        domains_in_batch = {d.domain for d in docs}
        if len(domains_in_batch) > 1:
            raise ValueError(
                f"_store_faiss requires a single domain per batch; got {sorted(domains_in_batch)}. Group docs by domain before calling."
            )

        async with _FAISS_WRITE_LOCK:
            vectors = await self.embedding.embed([d.content for d in docs])
            domain = docs[0].domain
            faiss_dir = Path(self.config.faiss_dir)
            faiss_dir.mkdir(parents=True, exist_ok=True)
            index_path = faiss_dir / f"{domain}.index"
            meta_path = faiss_dir / f"{domain}.meta.json"

            if index_path.exists():
                index = faiss.read_index(str(index_path))
                chunks = json.loads(meta_path.read_text(encoding="utf-8"))
            else:
                dim = len(vectors[0])
                index = faiss.IndexFlatIP(dim)
                chunks = []

            arr = np.array(vectors, dtype="float32")
            # L2-normalize so IndexFlatIP gives cosine similarity.
            # NaN-safe: zero vectors stay zero instead of producing NaN/Inf
            # that would poison FAISS search results downstream.
            norms = np.linalg.norm(arr, axis=1, keepdims=True)
            np.divide(arr, norms, out=arr, where=norms > 0)
            index.add(arr)
            for doc in docs:
                chunks.append(
                    {
                        "id": doc.doc_id or str(uuid.uuid4())[:12],
                        "content": doc.content,
                        "source": doc.source,
                        "title": doc.title or doc.source,
                        "domain": doc.domain,
                    }
                )
            faiss.write_index(index, str(index_path))
            meta_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
        RAG_CHUNK_COUNT.set(len(docs))
        return StoreResult(inserted=len(docs), failed=0, backend="faiss")

    # ─── Retrieve ───────────────────────────────────────────────────────────

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        domain: str | None = None,
        min_score: float | None = None,
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

        Records: latency → RAG_LATENCY_SECONDS, outcome → RAG_QUERIES_TOTAL{status,backend,domain},
        errors → RAG_ERRORS_TOTAL{stage='retrieve'}, chunk count → RAG_CHUNKS_RETURNED,
        avg relevance → RAG_RELEVANCE_AVG.
        """
        k = top_k or self.config.top_k
        threshold = min_score if min_score is not None else self.config.min_score
        backend_label = self.config.backend
        domain_label = domain or "all"
        with RAG_LATENCY_SECONDS.time():
            try:
                if self.config.backend == "pgvector":
                    results = await self._retrieve_pgvector(query, k, domain, threshold)
                else:
                    results = await self._retrieve_faiss(query, k, domain, threshold)
            except Exception as e:  # noqa: BLE001
                if not self.config.legacy_fallback or self.config.backend == "faiss":
                    RAG_ERRORS_TOTAL.labels(
                        stage="retrieve",
                        kind=type(e).__name__,
                    ).inc()
                    RAG_QUERIES_TOTAL.labels(
                        status="error",
                        backend=backend_label,
                        domain=domain_label,
                    ).inc()
                    logger.error(
                        "rag_retrieve_failed: backend=%s, domain=%s, error=%s, error_type=%s",
                        backend_label,
                        domain_label,
                        str(e),
                        type(e).__name__,
                    )
                    raise
                logger.warning(
                    "primary backend %s failed (%s) — falling back to FAISS",
                    self.config.backend,
                    type(e).__name__,
                )
                RAG_ERRORS_TOTAL.labels(
                    stage="retrieve_fallback",
                    kind=type(e).__name__,
                ).inc()
                backend_label = "faiss"
                results = await self._retrieve_faiss(query, k, domain, threshold)
        # Apply min_score uniformly (both primary and legacy paths).
        if threshold > 0.0:
            results = [r for r in results if r.relevance_score >= threshold]
        RAG_QUERIES_TOTAL.labels(
            status="ok",
            backend=backend_label,
            domain=domain_label,
        ).inc()
        RAG_CHUNKS_RETURNED.observe(len(results))
        if results:
            RAG_RELEVANCE_AVG.set(sum(r.relevance_score for r in results) / len(results))
        logger.info(
            "rag_retrieve: backend=%s, domain=%s, top_k=%d, returned=%d, min_score=%f",
            backend_label,
            domain_label,
            k,
            len(results),
            threshold,
        )
        return results

    async def _retrieve_pgvector(
        self,
        query: str,
        k: int,
        domain: str | None,
        threshold: float,
    ) -> list[RetrievedChunk]:
        pool = await self._get_pg_pool()
        qvec = await self.embedding.embed_one(query)
        qvec_str = "[" + ",".join(f"{x:.6f}" for x in qvec) + "]"

        # Domain filter is optional. NULL = no filter (all domains).
        # domain is a first-class column (see migrations_postgres/0009_pgvector.sql)
        # so the planner can use the B-tree pre-filter before HNSW.
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
                domain=r["domain"] or "",
                relevance_score=float(r["score"]),
                doc_id=r["doc_id"],
                backend="pgvector",
            )
            for r in rows
            if float(r["score"]) >= threshold
        ]
        self._update_rag_metrics(results)
        return results

    async def _retrieve_faiss(
        self,
        query: str,
        k: int,
        domain: str | None,
        threshold: float,
    ) -> list[RetrievedChunk]:
        qvec = await self.embedding.embed_one(query)
        q = np.array([qvec], dtype="float32")
        # L2-normalize so IndexFlatIP gives cosine similarity
        q = q / np.linalg.norm(q, axis=1, keepdims=True)

        domains = [domain] if domain else [p.stem for p in Path(self.config.faiss_dir).glob("*.index")]
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
                all_results.append(
                    RetrievedChunk(
                        content=c["content"],
                        source=c["source"],
                        title=c.get("title", ""),
                        domain=c.get("domain", d),
                        relevance_score=float(score),
                        backend="faiss",
                    )
                )

        all_results.sort(key=lambda x: x.relevance_score, reverse=True)
        # Dedupe by (source, title), keep top-k above threshold.
        seen: set = set()
        deduped: list[RetrievedChunk] = []
        for r in all_results:
            key = (r.source, r.title)
            if key in seen or r.relevance_score < threshold:
                continue
            seen.add(key)
            deduped.append(r)
        self._update_rag_metrics(deduped)
        return deduped[:k]

    def _load_faiss_domain(self, domain: str) -> tuple[faiss.Index | None, list[dict]]:
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
        # Back-compat shim — actual metrics are emitted from retrieve() at the
        # call-site so that latency / errors / queries_total line up with the
        # caller's domain/backend labels. Previously this method called
        # RAG_RELEVANCE_SCORE.set(avg) on a Histogram, which is a no-op
        # (Histogram has no .set); the bug is fixed in P2-04.
        return

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


_singleton: RAGClient | None = None


def get_rag_client() -> RAGClient:
    """Process-wide singleton. Built on first call from env config."""
    global _singleton
    if _singleton is None:
        _singleton = RAGClient()
    return _singleton
