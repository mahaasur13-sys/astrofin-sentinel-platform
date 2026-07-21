"""Production RAG Index with Hybrid Search (FAISS + BM25 + Reciprocal Rank Fusion).

Stack:
    Embedding model: intfloat/multilingual-e5-large (1024-d) or all-MiniLM-L6-v2 (384-d fallback)
    Dense: FAISS IndexFlatIP (cosine similarity via L2 normalization)
    Sparse: rank_bm25.BM25Okapi (lexical/ticker matching)
    Fusion: Reciprocal Rank Fusion (RRF) — k=60

Usage:
    from knowledge.rag_index import RAGIndex, retrieve_context, init_index

    # One-shot (backward compatible)
    init_index()                              # lazy init with test docs
    ctx = retrieve_context("Apple revenue")   # → str

    # Production (class-based)
    rag = RAGIndex()
    rag.rebuild([(text, {"source": "doc.md"}), ...])
    chunks = rag.retrieve("query")
"""
from __future__ import annotations

import json
import logging
import os
import pickle
import re
from pathlib import Path
from typing import Any, Optional

import numpy as np

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False

try:
    from sentence_transformers import SentenceTransformer
    HAS_ST = True
except ImportError:
    HAS_ST = False

try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False

logger = logging.getLogger(__name__)
HAS_ML_DEPS = HAS_FAISS and HAS_ST

_TEST_DOCUMENTS = [
    "Apple Inc. reported Q4 2024 revenue of $94.9 billion, up 6% year-over-year. "
    "Services revenue reached an all-time high of $25 billion. iPhone revenue was $46.2 billion.",
    "Microsoft Corporation Q2 FY2025 revenue was $69.6 billion, up 12% YoY. "
    "Azure cloud revenue grew 31%. AI services contributed $13 billion annualized run rate.",
    "Bitcoin ETF inflows reached $35 billion cumulative in 2024. BlackRock IBIT leads with $21 billion AUM.",
    "Gold prices reached $2700/oz in Q4 2024, up 28% year-to-date.",
    "VIX index averaged 18.2 in 2024, below the 10-year average of 19.5.",
    "Oil (WTI) traded at $72/bbl in Q4 2024. OPEC+ extended production cuts through Q1 2025.",
    "The Federal Reserve maintained interest rates at 4.25-4.50% in January 2026.",
    "NVIDIA Corporation reported Q3 FY2025 revenue of $35.1 billion, up 94% YoY.",
    "Tesla Inc. Q4 2024 automotive revenue was $19.8 billion.",
    "SEC 10-K filing: JPMorgan Chase reported total assets of $4.1 trillion.",
]


class Chunk:
    __slots__ = ('id', 'text', 'metadata')

    def __init__(self, id: str, text: str, metadata: dict[str, Any] | None = None):
        self.id = id
        self.text = text
        self.metadata = metadata or {}

    def model_copy(self) -> Chunk:
        c = Chunk(self.id, self.text)
        c.metadata = dict(self.metadata)
        return c

    def model_dump(self) -> dict:
        return {"id": self.id, "text": self.text, "metadata": self.metadata}


class RAGIndex:
    """Production RAG Index with Hybrid Search (FAISS + BM25 + RRF)."""

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or os.getenv("RAG_MODEL_NAME", "all-MiniLM-L6-v2")
        self.index_path = Path(os.getenv("RAG_INDEX_PATH", "data/rag_index"))
        self.index_path.mkdir(parents=True, exist_ok=True)
        self.faiss_index: Any = None
        self.bm25: Any = None
        self.chunks: list[Chunk] = []
        self.model: Any = None
        self._load_index()

    def _load_index(self) -> None:
        faiss_file = self.index_path / "faiss.index"
        bm25_file = self.index_path / "bm25.pkl"
        chunks_file = self.index_path / "chunks.json"
        if chunks_file.exists():
            with open(chunks_file, encoding="utf-8") as f:
                chunks_data = json.load(f)
            self.chunks = [Chunk(**c) for c in chunks_data]
            if HAS_ML_DEPS and faiss_file.exists():
                self.faiss_index = faiss.read_index(str(faiss_file))
                self.model = SentenceTransformer(self.model_name)
                logger.info("FAISS index loaded, chunks=%d", len(self.chunks))
            if HAS_BM25 and bm25_file.exists():
                with open(bm25_file, "rb") as f:
                    self.bm25 = pickle.load(f)
                logger.info("BM25 index loaded")
        else:
            logger.info("No existing RAG index found; call rebuild() to create one.")

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        if len(text) <= chunk_size:
            return [text]
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += (chunk_size - overlap)
        return chunks

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r'\w+', text.lower())

    def rebuild(self, documents: list[tuple[str, dict[str, Any]]]) -> None:
        if not HAS_ML_DEPS:
            raise RuntimeError("Cannot rebuild index: missing ML dependencies (faiss + sentence-transformers).")
        logger.info("Starting RAG index rebuild, documents=%d", len(documents))
        all_chunks: list[Chunk] = []
        for doc_idx, (text, metadata) in enumerate(documents):
            for chunk_idx, t in enumerate(self._chunk_text(text)):
                all_chunks.append(Chunk(
                    id=f"doc_{doc_idx}_chunk_{chunk_idx}",
                    text=t,
                    metadata={**metadata, "doc_idx": doc_idx, "chunk_idx": chunk_idx},
                ))
        self.chunks = all_chunks
        texts = [c.text for c in self.chunks]
        if not self.model:
            self.model = SentenceTransformer(self.model_name)
        logger.info("Encoding %d chunks for FAISS...", len(texts))
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        embeddings = embeddings.astype('float32')
        dim = embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dim)
        faiss.normalize_L2(embeddings)
        self.faiss_index.add(embeddings)
        if HAS_BM25:
            logger.info("Building BM25 index...")
            tokenized_corpus = [self._tokenize(t) for t in texts]
            self.bm25 = BM25Okapi(tokenized_corpus)
        self._save_index()
        logger.info("RAG index rebuild complete, chunks=%d", len(self.chunks))

    def _save_index(self) -> None:
        faiss_file = self.index_path / "faiss.index"
        bm25_file = self.index_path / "bm25.pkl"
        chunks_file = self.index_path / "chunks.json"
        if self.faiss_index:
            faiss.write_index(self.faiss_index, str(faiss_file))
        if self.bm25:
            with open(bm25_file, "wb") as f:
                pickle.dump(self.bm25, f)
        with open(chunks_file, "w", encoding="utf-8") as f:
            json.dump([c.model_dump() for c in self.chunks], f, ensure_ascii=False, indent=2)

    def retrieve(self, query: str, top_k: int = 5) -> list[Chunk]:
        if not self.chunks:
            return []
        dense_scores: dict[int, float] = {}
        if self.faiss_index is not None and self.model is not None:
            query_vec = self.model.encode([query], convert_to_numpy=True).astype('float32')
            faiss.normalize_L2(query_vec)
            k_search = min(len(self.chunks), top_k * 3)
            scores, indices = self.faiss_index.search(query_vec, k_search)
            for rank, idx in enumerate(indices[0]):
                if idx != -1:
                    dense_scores[int(idx)] = 1.0 / (60 + rank + 1)

        sparse_scores: dict[int, float] = {}
        if self.bm25 is not None:
            tokenized_query = self._tokenize(query)
            bm25_scores = self.bm25.get_scores(tokenized_query)
            top_bm25_idx = np.argsort(bm25_scores)[::-1][:top_k * 3]
            for rank, idx in enumerate(top_bm25_idx):
                if bm25_scores[idx] > 0:
                    sparse_scores[int(idx)] = 1.0 / (60 + rank + 1)

        rrf_scores: dict[int, float] = {}
        all_indices = set(list(dense_scores.keys()) + list(sparse_scores.keys()))
        for idx in all_indices:
            rrf_scores[idx] = dense_scores.get(idx, 0.0) + sparse_scores.get(idx, 0.0)

        sorted_indices = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        results: list[Chunk] = []
        for idx, score in sorted_indices:
            chunk = self.chunks[idx].model_copy()
            chunk.metadata["rrf_score"] = score
            results.append(chunk)
        return results

    def add(self, documents: list[tuple[str, dict[str, Any]]]) -> None:
        logger.warning("RAGIndex.add() triggers full rebuild (incremental not yet supported).")
        existing = [(c.text, c.metadata) for c in self.chunks]
        self.rebuild(existing + documents)


# ── Backward-compatible module-level API ──────────────────────────

_MODEL: Optional[SentenceTransformer] = None
_INDEX: Optional[Any] = None  # faiss.IndexFlatL2
_DOCS: list[str] = []
_MODULE_INITIALIZED = False


def init_index(documents: Optional[list[str]] = None) -> bool:
    global _MODEL, _INDEX, _DOCS, _MODULE_INITIALIZED
    docs = documents or _TEST_DOCUMENTS
    _DOCS = list(docs)
    if not HAS_ML_DEPS:
        logger.warning("RAG init failed: missing ML deps")
        return False
    try:
        _MODEL = SentenceTransformer(os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
        embeddings = _MODEL.encode(docs, normalize_embeddings=True)
        dim = embeddings.shape[1]
        _INDEX = faiss.IndexFlatL2(dim)
        _INDEX.add(np.ascontiguousarray(embeddings.astype(np.float32)))
        _MODULE_INITIALIZED = True
        logger.info("RAG index initialized: %d docs, dim=%d", len(docs), dim)
        return True
    except Exception as exc:
        logger.warning("RAG init failed (degraded mode): %s", exc)
        _MODEL = None
        _INDEX = None
        return False


def retrieve_context(query: str, top_k: int = 3) -> str:
    global _MODEL, _INDEX, _DOCS
    if _INDEX is None or _MODEL is None or not _DOCS:
        return ""
    try:
        qvec = _MODEL.encode([query], normalize_embeddings=True)
        distances, indices = _INDEX.search(
            np.ascontiguousarray(qvec.astype(np.float32)),
            min(top_k, len(_DOCS)),
        )
        chunks = [_DOCS[i] for i in indices[0] if 0 <= i < len(_DOCS)]
        return "\n\n".join(chunks) if chunks else ""
    except Exception as exc:
        logger.warning("RAG retrieve failed: %s", exc)
        return ""
