"""Hybrid retriever with Reciprocal Rank Fusion (P2-03b).

Combines a vector retriever and the in-process BM25Retriever from P2-03a via
weighted RRF. Used in P2-03c by MacroAgent in place of the pure-vector RAGClient.

Why RRF and not score-blending?
- Vector scores (cosine, 0..1) and BM25 scores (open-ended, log-derived) live
  on different scales. Naive normalization hides the real issue: the two
  retrievers rank the *same* chunk differently depending on whether the query
  is lexically specific (BM25 wins) or semantically broad (vector wins).
  RRF only uses ranks, so it is invariant to score scale.

Public API:
  - HybridScore(chunk, hybrid_score, vector_rank, bm25_rank)
  - HybridRetriever(vector_retriever, bm25_retriever, rrf_k, vector_weight, bm25_weight)
        .retrieve(query, top_k) -> list[HybridScore]   # async

Adapter contract: both retrievers must expose a method called `retrieve`
that returns a list of `Chunk` (or any object with `.id`). Vector side is
async (matches RAGClient); BM25 side is sync (pure-Python, no I/O).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Protocol

from .bm25_retriever import Chunk


class _VectorRetrieverLike(Protocol):
    """Async retriever returning Chunk-like objects with `.id`."""

    async def retrieve(self, query: str, top_k: int) -> List[Chunk]: ...


class _BM25RetrieverLike(Protocol):
    """Sync retriever returning Chunk-like objects with `.id`."""

    def retrieve(self, query: str, top_k: int) -> List[Chunk]: ...


@dataclass
class HybridScore:
    """A chunk after RRF fusion.

    `hybrid_score` is the weighted RRF score (higher = better). Source ranks
    are 1-based and may be None when the chunk appeared in only one retriever.
    """

    chunk: Chunk
    hybrid_score: float
    vector_rank: Optional[int] = None
    bm25_rank: Optional[int] = None


class HybridRetriever:
    """Reciprocal Rank Fusion of vector + BM25 retrieval.

    Args:
        vector_retriever: Anything with `async retrieve(query, top_k) -> list[Chunk]`.
            Typically a thin async adapter over RAGClient (built in P2-03c).
        bm25_retriever: An instantiated BM25Retriever with chunks already loaded.
        rrf_k: RRF constant. 60 is the value from the original RRF paper
            (Cormack et al., 2009); smaller values amplify rank differences.
        vector_weight: Multiplier for the vector half of the RRF sum.
        bm25_weight: Multiplier for the BM25 half of the RRF sum.
    """

    def __init__(
        self,
        vector_retriever: _VectorRetrieverLike,
        bm25_retriever: _BM25RetrieverLike,
        rrf_k: int = 60,
        vector_weight: float = 1.0,
        bm25_weight: float = 1.0,
    ) -> None:
        if rrf_k <= 0:
            raise ValueError(f"rrf_k must be positive, got {rrf_k}")
        if vector_weight < 0 or bm25_weight < 0:
            raise ValueError("weights must be non-negative")
        self.vector_retriever = vector_retriever
        self.bm25_retriever = bm25_retriever
        self.rrf_k = rrf_k
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight

    async def retrieve(self, query: str, top_k: int = 10) -> List[HybridScore]:
        """Top-`top_k` chunks by weighted RRF, descending by hybrid_score.

        Implementation notes:
        - Fetches `top_k * 4` from each side so the fused ranking has enough
          candidates (otherwise the tail of the vector list is never re-ranked
          against BM25 hits, and good BM25-only chunks lose out).
        - Dedupe key is `chunk.id` (string). Callers that build chunks from
          RAGClient must map `doc_id` -> str (UUID) when constructing Chunk.
        - An empty / whitespace query or non-positive top_k returns [] without
          hitting either retriever (cheaper for hot paths).
        """
        if not query or not query.strip() or top_k <= 0:
            return []

        fetch_k = top_k * 4

        vec_results = await self.vector_retriever.retrieve(query, top_k=fetch_k)
        # BM25Retriever.retrieve is sync; calling it from an async method is
        # safe because it does no I/O (pure in-process scoring).
        bm25_results = self.bm25_retriever.retrieve(query, top_k=fetch_k)

        # chunk_id -> {"vector": rank, "bm25": rank}
        ranks: dict = {}
        for rank, chunk in enumerate(vec_results, start=1):
            ranks.setdefault(chunk.id, {})["vector"] = rank
        for rank, chunk in enumerate(bm25_results, start=1):
            ranks.setdefault(chunk.id, {})["bm25"] = rank

        # Build a quick lookup for chunk objects by id.
        chunk_by_id: dict = {}
        for c in vec_results:
            chunk_by_id.setdefault(c.id, c)
        for c in bm25_results:
            chunk_by_id.setdefault(c.id, c)

        fused: List[HybridScore] = []
        for chunk_id, src_ranks in ranks.items():
            score = 0.0
            v_rank = src_ranks.get("vector")
            b_rank = src_ranks.get("bm25")
            if v_rank is not None:
                score += self.vector_weight / (self.rrf_k + v_rank)
            if b_rank is not None:
                score += self.bm25_weight / (self.rrf_k + b_rank)
            chunk = chunk_by_id.get(chunk_id)
            if chunk is None:
                # Should be unreachable: we just iterated over these lists.
                continue
            fused.append(
                HybridScore(
                    chunk=chunk,
                    hybrid_score=score,
                    vector_rank=v_rank,
                    bm25_rank=b_rank,
                )
            )

        fused.sort(key=lambda x: x.hybrid_score, reverse=True)
        return fused[:top_k]


__all__ = ["HybridScore", "HybridRetriever"]
