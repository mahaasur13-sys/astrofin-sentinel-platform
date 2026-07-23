"""Tests for HybridRetriever (P2-03b). Mocks both vector and BM25 retrievers.

We test the fusion algorithm itself: ranking, weighting, dedup, edge cases.
Real RAGClient integration is covered in P2-03c.
"""

from __future__ import annotations

import pytest

from knowledge.bm25_retriever import Chunk
from knowledge.hybrid_retriever import HybridRetriever, HybridScore

# ─── Fixtures ───────────────────────────────────────────────────────────────


def _chunk(cid: str, content: str) -> Chunk:
    return Chunk(id=cid, content=content, metadata={})


def _async(items: list[Chunk]):
    """Build an async-stub retriever from a fixed list. Mirrors RAGClient."""

    class _Stub:
        async def retrieve(self, query: str, top_k: int) -> list[Chunk]:
            return items[:top_k]

    return _Stub()


def _sync(items: list[Chunk]):
    """Build a sync-stub retriever (matches BM25Retriever signature)."""

    class _Stub:
        def retrieve(self, query: str, top_k: int) -> list[Chunk]:
            return items[:top_k]

    return _Stub()


# ─── Basic fusion ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rrf_fuses_two_ranks_and_sorts_desc():
    """Chunk present in both lists must outrank a chunk present in only one."""
    a, b, c = _chunk("1", "apple"), _chunk("2", "banana"), _chunk("3", "cherry")
    vec = _async([a, c])  # vec ranks: a=1, c=2
    bm = _sync([b, a])  # bm ranks:  b=1, a=2
    h = HybridRetriever(vec, bm)
    out = await h.retrieve("anything", top_k=3)

    # 3 unique chunks, sorted by hybrid score desc
    assert len(out) == 3
    assert all(isinstance(r, HybridScore) for r in out)
    assert [r.chunk.id for r in out] == ["1", "2", "3"]
    # '1' (apple) appears in both → highest RRF sum
    assert out[0].chunk.id == "1"
    assert out[0].vector_rank == 1
    assert out[0].bm25_rank == 2
    # '3' (cherry) only in vector → lowest
    assert out[2].chunk.id == "3"
    assert out[2].vector_rank == 2
    assert out[2].bm25_rank is None
    # scores strictly descending
    assert out[0].hybrid_score > out[1].hybrid_score > out[2].hybrid_score


@pytest.mark.asyncio
async def test_rrf_score_formula_matches_definition():
    """hybrid_score = w_vec/(k+rank_vec) + w_bm25/(k+rank_bm25)."""
    a, b = _chunk("1", "x"), _chunk("2", "y")
    vec = _async([a, b])
    bm = _sync([b, a])
    h = HybridRetriever(vec, bm, rrf_k=60, vector_weight=1.0, bm25_weight=1.0)
    out = await h.retrieve("q", top_k=2)
    by_id = {r.chunk.id: r for r in out}
    # both chunks have the same ranks, so their hybrid scores MUST be equal
    assert by_id["1"].hybrid_score == pytest.approx(1 / 61 + 1 / 62)
    assert by_id["2"].hybrid_score == pytest.approx(1 / 61 + 1 / 62)
    assert by_id["1"].hybrid_score == by_id["2"].hybrid_score


# ─── Weights ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_vector_weight_dominates_when_bm25_weight_zero():
    """With bm25_weight=0, fusion reduces to pure vector ranking."""
    a, b, c = _chunk("1", "x"), _chunk("2", "y"), _chunk("3", "z")
    vec = _async([a, b, c])  # a=1, b=2, c=3
    bm = _sync([c, b, a])  # c=1, b=2, a=3  (opposite order)
    h = HybridRetriever(vec, bm, vector_weight=1.0, bm25_weight=0.0)
    out = await h.retrieve("q", top_k=3)
    # Only vector contributes → a first
    assert [r.chunk.id for r in out] == ["1", "2", "3"]


@pytest.mark.asyncio
async def test_higher_bm25_weight_promotes_bm25_only_hits():
    """Heavy bm25_weight should bump a bm25-only chunk above a vector-only one."""
    a, b, c = _chunk("1", "x"), _chunk("2", "y"), _chunk("3", "z")
    vec = _async([a, b])  # a=1, b=2
    bm = _sync([c, a])  # c=1, a=2
    # With default weights (1.0, 1.0):
    #   a (1,2): 1/61 + 1/62 ≈ 0.0326
    #   b (2,_): 1/62 ≈ 0.0161
    #   c (_,1): 1/61 ≈ 0.0164
    # So default order: a, c, b
    h_default = HybridRetriever(vec, bm)
    out = await h_default.retrieve("q", top_k=3)
    assert out[0].chunk.id == "1"
    assert out[1].chunk.id == "3"

    # Now crank bm25 weight to 5.0:
    #   a (1,2): 1/61 + 5/62 = 0.0971
    #   b (2,_): 1/62 + 0    = 0.0161
    #   c (_,1): 0    + 5/61 = 0.0820
    # Still a first, but now c should beat b.
    h_heavy = HybridRetriever(vec, bm, vector_weight=1.0, bm25_weight=5.0)
    out2 = await h_heavy.retrieve("q", top_k=3)
    assert out2[0].chunk.id == "1"
    assert out2[1].chunk.id == "3"  # bm25-only beats vector-only
    assert out2[2].chunk.id == "2"


# ─── Edge cases ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_empty_query_returns_empty():
    vec = _async([_chunk("1", "x")])
    bm = _sync([_chunk("1", "x")])
    h = HybridRetriever(vec, bm)
    assert await h.retrieve("", top_k=5) == []


@pytest.mark.asyncio
async def test_zero_top_k_returns_empty():
    vec = _async([_chunk("1", "x")])
    bm = _sync([_chunk("1", "x")])
    h = HybridRetriever(vec, bm)
    assert await h.retrieve("q", top_k=0) == []


@pytest.mark.asyncio
async def test_both_empty_returns_empty():
    h = HybridRetriever(_async([]), _sync([]))
    assert await h.retrieve("q", top_k=10) == []


@pytest.mark.asyncio
async def test_dedup_same_id_appears_once_with_ranks_from_both():
    """If both retrievers return the same chunk id, we should see ONE entry
    with both ranks populated (not two duplicate entries)."""
    a = _chunk("dup", "shared content")
    vec = _async([a])
    bm = _sync([a])
    h = HybridRetriever(vec, bm)
    out = await h.retrieve("q", top_k=5)
    assert len(out) == 1
    assert out[0].chunk.id == "dup"
    assert out[0].vector_rank == 1
    assert out[0].bm25_rank == 1
    # Score: 1/61 + 1/61 = 2/61
    assert out[0].hybrid_score == pytest.approx(2.0 / 61.0)


@pytest.mark.asyncio
async def test_top_k_caps_results_after_fusion():
    """Even if both retrievers return many chunks, we cap at top_k."""
    chunks = [_chunk(str(i), f"text {i}") for i in range(10)]
    vec = _async(chunks[:8])  # 1..8
    bm = _sync(chunks[2:])  # 3..10
    h = HybridRetriever(vec, bm)
    out = await h.retrieve("q", top_k=3)
    assert len(out) == 3


@pytest.mark.asyncio
async def test_default_rrf_k_is_60():
    """The RRF constant k=60 is the original paper's recommendation."""
    h = HybridRetriever(_async([]), _sync([]))
    assert h.rrf_k == 60
    assert h.vector_weight == 1.0
    assert h.bm25_weight == 1.0


@pytest.mark.asyncio
async def test_custom_rrf_k_changes_scores():
    """A smaller k makes top ranks matter more."""
    a, b = _chunk("1", "x"), _chunk("2", "y")
    vec = _async([a, b])
    bm = _sync([a, b])  # both retrievers agree on order
    h60 = HybridRetriever(vec, bm, rrf_k=60)
    h1 = HybridRetriever(vec, bm, rrf_k=1)
    out60 = await h60.retrieve("q", top_k=1)
    out1 = await h1.retrieve("q", top_k=1)
    # k=1 produces larger per-rank scores (1/2 vs 1/61)
    assert out1[0].hybrid_score > out60[0].hybrid_score
