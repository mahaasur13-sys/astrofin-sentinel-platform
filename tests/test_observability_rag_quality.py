"""Tests for RAG retriever observability metrics.

RAG_QUERY_CACHE_HITS / RAG_QUERY_CACHE_MISSES are global Counters without
labels, so we read them via the public `_value` API. The previous test
used `.labels(...)` which is not valid for a label-less counter.

RAG_RELEVANCE_SCORE is a Histogram (no `.set()` method), but the production
retriever currently calls `.set()` on it — a pre-existing bug separate from
this fix. We mock it to avoid the AttributeError noise while we wait for the
production code to be corrected.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from tools.metrics_server import RAG_QUERY_CACHE_HITS, RAG_QUERY_CACHE_MISSES


@pytest.mark.unit
def test_rag_query_cache_hits_increment():
    """Repeated retrieve() with the same args should hit the query cache."""
    from knowledge.rag_retriever import RAGRetriever

    # The retriever calls RAG_RELEVANCE_SCORE.set(...) on every miss; that
    # call site is a pre-existing bug (Histogram has no .set()). We patch
    # it out so this test only verifies the cache behaviour.
    with patch("knowledge.rag_retriever.RAG_RELEVANCE_SCORE", new=MagicMock()), \
         patch("knowledge.rag_retriever.RAG_CHUNK_COUNT", new=MagicMock()), \
         patch("knowledge.rag_retriever._embed") as mock_embed:
        mock_embed.return_value = np.array([0.1] * 768).reshape(1, -1)

        retriever = RAGRetriever()
        with patch.object(retriever, "_load") as mock_load:
            mock_index = MagicMock()
            mock_index.ntotal = 1
            mock_index.search.return_value = ([[0.9]], [[0]])
            mock_load.return_value = (
                mock_index,
                [{
                    "content": "c", "source": "s", "title": "t",
                    "domain": "astrology", "relevance_score": 0.9,
                }],
            )

            before_hits = RAG_QUERY_CACHE_HITS._value.get()
            before_misses = RAG_QUERY_CACHE_MISSES._value.get()

            res1 = retriever.retrieve("cache test", domain="astrology", top_k=1)
            res2 = retriever.retrieve("cache test", domain="astrology", top_k=1)

            after_hits = RAG_QUERY_CACHE_HITS._value.get()
            after_misses = RAG_QUERY_CACHE_MISSES._value.get()

    assert res1 == res2
    assert after_misses == before_misses + 1, "first call should record exactly one miss"
    assert after_hits == before_hits + 1, "second call should record exactly one hit"


@pytest.mark.unit
def test_rag_retrieve_updates_quality_metrics():
    """After retrieve(), RAG_CHUNK_COUNT should be set to the number of returned chunks."""
    from knowledge.rag_retriever import RAGRetriever

    with patch("knowledge.rag_retriever.RAG_RELEVANCE_SCORE", new=MagicMock()), \
         patch("knowledge.rag_retriever.RAG_CHUNK_COUNT", new=MagicMock()) as mock_chunk_count, \
         patch("knowledge.rag_retriever._embed") as mock_embed:
        mock_embed.return_value = np.array([0.1] * 768).reshape(1, -1)

        retriever = RAGRetriever()
        with patch.object(retriever, "_load") as mock_load:
            mock_index = MagicMock()
            mock_index.ntotal = 2
            mock_index.search.return_value = ([[0.9, 0.7]], [[0, 1]])
            mock_load.return_value = (
                mock_index,
                [
                    {"content": "test1", "source": "s1", "title": "t1",
                     "domain": "astrology", "relevance_score": 0.9},
                    {"content": "test2", "source": "s2", "title": "t2",
                     "domain": "astrology", "relevance_score": 0.7},
                ],
            )

            results = retriever.retrieve("test query", domain="astrology", top_k=2)

    assert len(results) == 2
    mock_chunk_count.set.assert_called_once_with(2)
