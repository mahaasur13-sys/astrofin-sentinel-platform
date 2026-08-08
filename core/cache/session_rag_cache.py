"""
AstroFin — Session RAG Cache

Кэширует результаты FAISS-retrieval в рамках одной DAG-сессии,
чтобы повторные запросы к RAG не дублировались внутри одного анализа.

Использование:
    from core.cache.session_rag_cache import get_session_rag_cache
    cache = get_session_rag_cache(session_id="abc123")
    result = cache.get(query) or cache.set(query, rag.retrieve(query))
"""

from __future__ import annotations

import hashlib
import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)

# Время жизни кэша по умолчанию — 5 минут (одна DAG-сессия)
DEFAULT_SESSION_TTL_S = 300.0
MAX_ENTRIES_PER_SESSION = 50


class SessionRAGCache:
    """Кэш RAG-результатов для одной сессии."""

    def __init__(self, session_id: str, ttl_s: float = DEFAULT_SESSION_TTL_S):
        self.session_id = session_id
        self.ttl_s = ttl_s
        self._cache: dict[str, tuple[float, str]] = {}
        self._lock = threading.Lock()

    def _key(self, query: str, top_k: int = 3) -> str:
        """Хэш запроса для быстрого exact match."""
        return hashlib.md5(f"{query}:{top_k}".encode()).hexdigest()

    def get(self, query: str, top_k: int = 3) -> Optional[str]:
        """Получить кэшированный результат RAG, если он свежий."""
        import time

        key = self._key(query, top_k)
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            ts, result = entry
            if time.time() - ts > self.ttl_s:
                del self._cache[key]
                return None
            logger.debug("[SessionRAG] Hit for query hash=%s", key[:8])
            return result

    def set(self, query: str, result: str, top_k: int = 3) -> str:
        """Сохранить результат RAG в кэш и вернуть его."""
        import time

        key = self._key(query, top_k)
        with self._lock:
            if len(self._cache) >= MAX_ENTRIES_PER_SESSION:
                oldest = min(self._cache, key=lambda k: self._cache[k][0])
                del self._cache[oldest]
            self._cache[key] = (time.time(), result)
        logger.debug("[SessionRAG] Stored query hash=%s (%d chars)", key[:8], len(result))
        return result

    def clear(self) -> None:
        """Очистить кэш сессии."""
        with self._lock:
            self._cache.clear()

    @property
    def stats(self) -> dict:
        with self._lock:
            return {
                "session_id": self.session_id,
                "entries": len(self._cache),
                "ttl_s": self.ttl_s,
            }


# Глобальный реестр кэшей по session_id
_global_sessions: dict[str, SessionRAGCache] = {}
_global_lock = threading.Lock()


def get_session_rag_cache(
    session_id: str,
    ttl_s: float = DEFAULT_SESSION_TTL_S,
) -> SessionRAGCache:
    """Получить или создать RAG-кэш для сессии."""
    with _global_lock:
        if session_id not in _global_sessions:
            _global_sessions[session_id] = SessionRAGCache(session_id, ttl_s)
            logger.debug("[SessionRAG] Created cache for session=%s", session_id)
    return _global_sessions[session_id]


def clear_session_rag_cache(session_id: str) -> None:
    """Удалить кэш завершённой сессии."""
    with _global_lock:
        if session_id in _global_sessions:
            _global_sessions[session_id].clear()
            del _global_sessions[session_id]
