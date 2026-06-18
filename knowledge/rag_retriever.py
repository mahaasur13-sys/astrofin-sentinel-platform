"""
AstroFin Sentinel v5 — RAG Retriever
Unified knowledge retrieval interface for all agents.
FAISS-backed semantic search with Ollama embeddings.
"""

from __future__ import annotations
import json
import urllib.request
from pathlib import Path

import faiss
import numpy as np

from tools.metrics_server import (
    CACHE_HITS,
    CACHE_MISSES,
    OLLAMA_STATUS,
    RAG_CHUNK_COUNT,
    RAG_QUERY_CACHE_HITS,
    RAG_QUERY_CACHE_MISSES,
    RAG_RELEVANCE_SCORE,
)

DIM = 768


# ─── Embeddings ────────────────────────────────────────────────────────────────


def _embed(text: str) -> np.ndarray:
    """Get nomic-embed-text embedding via Ollama API, updating health status."""
    payload = json.dumps({"model": "nomic-embed-text", "prompt": text}).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/embeddings",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            emb = json.loads(resp.read())["embedding"]
        vec = np.array(emb, dtype="float32")
        vec = vec / (np.linalg.norm(vec) + 1e-8)
        OLLAMA_STATUS.set(1)
        return vec
    except Exception:
        OLLAMA_STATUS.set(0)
        raise


# ─── RAGRetriever ─────────────────────────────────────────────────────────────


class RAGRetriever:
    """
    FAISS-backed RAG retrieval.

    Agents call `retrieve(query, domain=None)` to get top-k relevant
    chunks with citation metadata.
    """

    def __init__(self, knowledge_dir: str = None):
        if knowledge_dir is None:
            self.kb_dir = Path(__file__).parent
        else:
            self.kb_dir = Path(knowledge_dir)

        self.indexes_dir = self.kb_dir / "indexes"
        self.chunks_dir = self.kb_dir / "chunks"

        self._cache: dict[str, tuple[faiss.Index, list[dict]]] = {}
        self._query_cache: dict[tuple, list[dict]] = {}

    def _load(self, domain: str):
        """Load (and cache) FAISS index + metadata for a domain."""
        if domain in self._cache:
            CACHE_HITS.inc()  # cache hit
            return self._cache[domain]

        index_path = self.indexes_dir / f"{domain}.index"
        meta_path = self.indexes_dir / f"{domain}.meta.json"

        if not index_path.exists() or not meta_path.exists():
            self._cache[domain] = (None, [])
            return None, []

        index = faiss.read_index(str(index_path))
        chunks = json.loads(meta_path.read_text(encoding="utf-8"))
        self._cache[domain] = (index, chunks)
        CACHE_MISSES.inc()  # cache miss (first load)
        return index, chunks

    def retrieve(
        self,
        query: str,
        domain: str | None = None,
        top_k: int = 5,
        min_score: float = 0.5,
    ) -> list[dict]:
        """
        Semantic search across knowledge chunks.

        Args:
            query: Natural-language query from the agent
            domain: Optional domain filter (astrology / technical / trading).
                    If None, searches all available domains and merges results.
            top_k: Number of results to return per domain
            min_score: Minimum cosine similarity threshold

        Returns:
            List of dicts with keys: content, source, title, domain, relevance_score
        """
        # Проверка кеша запросов
        cache_key = (query, domain, top_k)
        if cache_key in self._query_cache:
            RAG_QUERY_CACHE_HITS.inc()
            return self._query_cache[cache_key]
        RAG_QUERY_CACHE_MISSES.inc()

        domains = [domain] if domain else ["astrology", "technical", "trading"]
        all_results: list[dict] = []

        q_vec = _embed(query).reshape(1, -1)

        for d in domains:
            index, chunks = self._load(d)
            if index is None or index.ntotal == 0:
                continue

            k = min(top_k, index.ntotal)
            scores, indices = index.search(q_vec.astype("float32"), k)

            for score, idx in zip(scores[0], indices[0], strict=False):
                if idx < 0:
                    continue
                chunk = chunks[idx]
                result = {
                    "content": chunk["content"],
                    "source": chunk["source"],
                    "title": chunk["title"],
                    "domain": chunk.get("domain", d),
                    "relevance_score": float(score),
                }
                all_results.append(result)

        # Sort by score, filter, deduplicate by source+title
        all_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        seen: set = set()
        deduped: list[dict] = []
        for r in all_results:
            key = (r["source"], r["title"])
            if key not in seen and r["relevance_score"] >= min_score:
                seen.add(key)
                deduped.append(r)

        # Обновляем RAG quality метрики
        if deduped:
            avg_rel = sum(r["relevance_score"] for r in deduped) / len(deduped)
        else:
            avg_rel = 0.0
        RAG_RELEVANCE_SCORE.set(avg_rel)
        RAG_CHUNK_COUNT.set(len(deduped))

        # Сохраняем результат в кеш запросов
        self._query_cache[cache_key] = deduped[:top_k]

        return deduped[:top_k]

    def stats(self) -> dict:
        """Return per-domain index statistics."""
        domains = ["astrology", "technical", "trading"]
        result = {}
        for d in domains:
            index, chunks = self._load(d)
            result[d] = {
                "indexed_chunks": index.ntotal if index else 0,
                "files": list(set(c["source"] for c in chunks)),
            }
        return result


# ─── Agent Tool ───────────────────────────────────────────────────────────────


def retrieve_knowledge(
    query: str,
    domain: str | None = None,
    top_k: int = 5,
) -> str:
    """
    Agent tool: semantic search over the knowledge base.

    Agents call this when:
    - The question is not answered by their instructions.md
    - They need factual grounding, not speculation

    Returns a markdown string with cited chunks.
    """
    retriever = RAGRetriever()
    chunks = retriever.retrieve(query, domain=domain, top_k=top_k)

    if not chunks:
        return "⚠ В базе знаний не найдена релевантная информация."

    lines = [f"### Результаты RAG-поиска по запросу: «{query}»\n"]
    for i, chunk in enumerate(chunks, 1):
        pct = chunk["relevance_score"]
        bar = "█" * int(pct * 10) + "░" * (10 - int(pct * 10))
        lines.append(
            f"**[{i}]** {chunk['source']} — {chunk['title']}  "
            f"`{bar}` {pct:.1%}\n\n"
            f"{chunk['content'][:400]}"
            f"{'…' if len(chunk['content']) > 400 else ''}\n"
        )

    return "\n---\n".join(lines)


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RAG Retriever CLI")
    parser.add_argument("query", nargs="?")
    parser.add_argument("--domain", choices=["astrology", "technical", "trading"])
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    retriever = RAGRetriever()

    if args.query:
        results = retriever.retrieve(args.query, domain=args.domain, top_k=args.top_k)
        print(retrieve_knowledge(args.query, domain=args.domain, top_k=args.top_k))
    else:
        print("\n📊 Index stats:")
        for domain, stat in retriever.stats().items():
            print(f"  {domain:12s}: {stat['indexed_chunks']:3d} chunks  files={stat['files']}")
