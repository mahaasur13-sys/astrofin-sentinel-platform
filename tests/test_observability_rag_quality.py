from __future__ import annotations

from unittest.mock import MagicMock, patch


from tools.metrics_server import (
    RAG_CHUNK_COUNT,
    RAG_CHUNKS_RETURNED,
    RAG_QUERIES_TOTAL,
    RAG_RELEVANCE_AVG,
    RAG_RELEVANCE_SCORE,
)


import pytest


@pytest.mark.unit
def test_rag_retrieve_updates_quality_metrics():
    """После retrieve должны обновиться метрики relevance_score и chunk_count."""


@pytest.mark.unit
def test_rag_query_cache_hits_increment():
    """Повторный запрос с теми же параметрами должен вернуть кешированный результат.
    (P2-04) Теперь метрика — RAG_QUERIES_TOTAL{status, backend, domain}."""
    from knowledge.rag_retriever import RAGRetriever

    retriever = RAGRetriever()
    with patch("knowledge.rag_retriever._embed") as mock_embed:
        mock_embed.return_value = __import__("numpy").array([0.1] * 768).reshape(1, -1)
        with patch.object(retriever, "_load") as mock_load:
            fake_chunks = [
                {
                    "content": "c",
                    "source": "s",
                    "title": "t",
                    "domain": "astrology",
                    "relevance_score": 0.9,
                }
            ]
            mock_index = MagicMock()
            mock_index.ntotal = 1
            mock_index.search.return_value = ([[0.9]], [[0]])
            mock_load.return_value = (mock_index, fake_chunks)

            def _query_count():
                # Sum across all label combinations of RAG_QUERIES_TOTAL.
                total = 0.0
                for metric in RAG_QUERIES_TOTAL.collect():
                    for sample in metric.samples:
                        if sample.name.endswith("_total"):
                            total += sample.value
                return total

            before = _query_count()
            res1 = retriever.retrieve("cache test", domain="astrology", top_k=1)
            res2 = retriever.retrieve("cache test", domain="astrology", top_k=1)
            after = _query_count()

            assert res1 == res2, "Cached result should match"
            assert (
                after > before
            ), f"Expected RAG_QUERIES_TOTAL to increase; before={before}, after={after}"
    retriever = RAGRetriever()
    # Мокаем _embed и FAISS-индекс, чтобы вернуть известные результаты
    with patch("knowledge.rag_retriever._embed") as mock_embed:
        mock_embed.return_value = __import__("numpy").array([0.1] * 768).reshape(1, -1)
        with patch.object(retriever, "_load") as mock_load:
            fake_chunks = [
                {
                    "content": "test1",
                    "source": "s1",
                    "title": "t1",
                    "domain": "astrology",
                    "relevance_score": 0.9,
                },
                {
                    "content": "test2",
                    "source": "s2",
                    "title": "t2",
                    "domain": "astrology",
                    "relevance_score": 0.7,
                },
            ]
            mock_index = MagicMock()
            mock_index.ntotal = 2
            mock_index.search.return_value = ([[0.9, 0.7]], [[0, 1]])
            mock_load.return_value = (mock_index, fake_chunks)

            results = retriever.retrieve("test query", domain="astrology", top_k=2)

    assert len(results) == 2
    # Проверяем, что средний relevance_score записан в Gauge
    avg_val = (
        RAG_RELEVANCE_AVG._value.get() if hasattr(RAG_RELEVANCE_AVG, "_value") else 0
    )
    assert avg_val > 0, f"Expected avg relevance > 0, got {avg_val}"
    # Проверяем количество чанков
    chunk_val = (
        RAG_CHUNK_COUNT._value.get() if hasattr(RAG_CHUNK_COUNT, "_value") else 0
    )
    assert chunk_val == 2, f"Expected chunk count 2, got {chunk_val}"
