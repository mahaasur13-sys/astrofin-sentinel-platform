"""Unit tests for knowledge.bm25_retriever."""

from __future__ import annotations

import pytest

from knowledge.bm25_retriever import BM25Retriever, Chunk


@pytest.fixture
def finance_chunks() -> list[Chunk]:
    return [
        Chunk(id="1", content="Купить акции Apple по рыночной цене", metadata={}),
        Chunk(id="2", content="Продать облигации федерального займа", metadata={}),
        Chunk(
            id="3", content="Инвестиции в недвижимость и земельные участки", metadata={}
        ),
        Chunk(id="4", content="Дивидендная политика компании Apple", metadata={}),
    ]


def test_basic_ranking_keyword_match(finance_chunks: list[Chunk]) -> None:
    r = BM25Retriever(finance_chunks)
    results = r.retrieve("Apple", top_k=3)
    assert len(results) == 3
    top_ids = [c.id for c in results[:2]]
    # Both Apple-mentioning chunks should occupy the top-2.
    assert set(top_ids) == {"1", "4"}
    # All results carry a numeric bm25_score.
    for c in results:
        assert c.bm25_score is not None
        assert isinstance(c.bm25_score, float)


def test_scores_strictly_descending(finance_chunks: list[Chunk]) -> None:
    r = BM25Retriever(finance_chunks)
    results = r.retrieve("акции инвестиции", top_k=4)
    scores = [c.bm25_score for c in results]
    assert scores == sorted(scores, reverse=True)


def test_input_chunks_not_mutated(finance_chunks: list[Chunk]) -> None:
    r = BM25Retriever(finance_chunks)
    r.retrieve("Apple", top_k=2)
    # The original objects must remain untouched.
    for c in finance_chunks:
        assert c.bm25_score is None
        assert c.score is None


def test_empty_query_returns_empty(finance_chunks: list[Chunk]) -> None:
    r = BM25Retriever(finance_chunks)
    assert r.retrieve("") == []
    assert r.retrieve("   !!!  ") == []  # punctuation-only also tokenizes to []


def test_no_overlap_returns_zero_scores() -> None:
    chunks = [Chunk(id="1", content="apple orange banana", metadata={})]
    r = BM25Retriever(chunks)
    results = r.retrieve("квартальный отчёт", top_k=5)
    assert len(results) == 1
    # No shared tokens -> score must be exactly 0.0.
    assert results[0].bm25_score == 0.0


def test_empty_corpus_is_safe() -> None:
    r = BM25Retriever([])
    assert r.retrieve("anything", top_k=5) == []


def test_top_k_zero_or_negative() -> None:
    chunks = [Chunk(id="1", content="hello world", metadata={})]
    r = BM25Retriever(chunks)
    assert r.retrieve("hello", top_k=0) == []
    assert r.retrieve("hello", top_k=-3) == []


def test_top_k_larger_than_corpus(finance_chunks: list[Chunk]) -> None:
    r = BM25Retriever(finance_chunks)
    results = r.retrieve("Apple", top_k=100)
    assert len(results) == len(finance_chunks)


def test_idf_is_positive_and_finite(finance_chunks: list[Chunk]) -> None:
    r = BM25Retriever(finance_chunks)
    for token, idf in r._idf.items():
        assert math.isfinite(idf), token
        assert idf > 0, token


def test_russian_and_latin_tokenization() -> None:
    chunks = [Chunk(id="1", content="API FastAPI 2024 год", metadata={})]
    r = BM25Retriever(chunks)
    # Both "api" and "fastapi" should be in the IDF dict.
    assert "api" in r._idf
    assert "fastapi" in r._idf
    assert "2024" in r._idf


# Late import so the test file fails clearly if math is missing.
import math  # noqa: E402
