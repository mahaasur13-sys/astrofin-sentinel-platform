from unittest.mock import MagicMock, patch


from knowledge.rag_retriever import RAGRetriever
from tools.metrics_server import CACHE_HITS, CACHE_MISSES


import pytest
@pytest.mark.unit
def test_faiss_load_cache_increments_counters():
    """Повторный вызов _load для одного домена должен инкрементировать hit/miss."""
    # Очищаем счётчики (значения сбрасываются только через REGISTRY, но используем текущие значения)
    before_hits = CACHE_HITS._value.get() if hasattr(CACHE_HITS, "_value") else 0
    before_misses = CACHE_MISSES._value.get() if hasattr(CACHE_MISSES, "_value") else 0

    # Создаём экземпляр без реальных файлов
    retriever = RAGRetriever()

    # Мокаем faiss.read_index и существование файлов
    mock_index = MagicMock()
    mock_index.ntotal = 10
    fake_chunks = [{"content": "test", "source": "test.md", "title": "Test"}]

    with (
        patch("faiss.read_index", return_value=mock_index),
        patch("pathlib.Path.exists", return_value=True),
        patch(
            "pathlib.Path.read_text",
            return_value='[{"content":"test","source":"test.md","title":"Test"}]',
        ),
        patch("json.loads", return_value=fake_chunks),
    ):  # чтобы не читать реальный JSON
        # Первый вызов – cache miss
        retriever._load("astrology")
        # Второй вызов – cache hit
        retriever._load("astrology")

    after_hits = CACHE_HITS._value.get() if hasattr(CACHE_HITS, "_value") else 0
    after_misses = CACHE_MISSES._value.get() if hasattr(CACHE_MISSES, "_value") else 0

    assert after_misses > before_misses, "Cache miss should be incremented"
    assert after_hits > before_hits, "Cache hit should be incremented"
