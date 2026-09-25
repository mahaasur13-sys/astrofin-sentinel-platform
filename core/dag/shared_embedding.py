"""
AstroFin Sentinel V5 — Shared Embedding Space (P2: Sprint G)

Общее векторное пространство агентов: каждый агент публикует embedding своего
выхода, а следующий анализ может найти топ-k наиболее релевантных агентов для
данного запроса вместо фиксированной топологии.

Принцип работы:
1. Agent публикует output → embedder кодирует в np.array[384]
2. Эмбеддинг сохраняется в FAISS-индекс с метаданными (agent_id, timestamp, confidence, trace_id)
3. При новом запросе: query embedding → FAISS.search(k) → топ-k релевантных агентов
4. Результат используется динамическим роутером для выбора активных агентов

Usage:
    from core.dag.shared_embedding import SharedEmbeddingSpace, get_shared_embedding

    ses = get_shared_embedding()
    ses.publish("MacroFlowAgent", macro_output, confidence=0.72)
    top_agents = ses.query("BTC price analysis", k=5)
    # → [("QuantAgent", 0.89), ("FundamentalAgent", 0.82), ...]
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional

import numpy as np

from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_DIM = 384  # all-MiniLM-L6-v2
MAX_INDEX_SIZE = int(
    __import__("os").environ.get("SHARED_EMBEDDING_MAX_SIZE", "1000")
)
QUERY_TOP_K = 10

_SHARED_EMBED_PUBLISH_TOTAL = Counter(
    "dag_shared_embed_publish_total",
    "Total publications to shared embedding space",
    ["agent_id"],
)
_SHARED_EMBED_QUERY_TOTAL = Counter(
    "dag_shared_embed_query_total",
    "Total queries to shared embedding space",
    ["pipeline"],
)
_SHARED_EMBED_SIZE_GAUGE = Gauge(
    "dag_shared_embed_size",
    "Current size of shared FAISS index",
)


class SharedEmbeddingSpace:
    """Общее векторное пространство агентов на базе FAISS."""

    def __init__(self, dimension: int = DEFAULT_EMBEDDING_DIM) -> None:
        self.dimension = dimension
        self._lock = threading.Lock()
        self._entries: list[dict] = []
        self._embedder = None
        self._index = None
        self._index_size = 0

    def _ensure_embedder(self) -> None:
        """Ленивая инициализация sentence-transformers."""
        if self._embedder is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("[SharedEmbed] embedder initialized: all-MiniLM-L6-v2")
        except Exception as e:
            logger.error("[SharedEmbed] embedder init failed: %s", e)
            raise RuntimeError(f"Failed to initialize embedder: {e}") from e

    def _ensure_index(self) -> None:
        """Ленивая инициализация FAISS-индекса."""
        if self._index is not None:
            return
        try:
            import faiss
            self._index = faiss.IndexFlatIP(self.dimension)
            logger.info("[SharedEmbed] FAISS IndexFlatIP(%d) initialized", self.dimension)
        except Exception as e:
            logger.error("[SharedEmbed] FAISS init failed: %s", e)
            raise RuntimeError(f"Failed to initialize FAISS: {e}") from e

    def _encode(self, text: str) -> np.ndarray:
        """Кодирование текста в embedding [1, dim] (L2-нормализованный)."""
        self._ensure_embedder()
        vec = self._embedder.encode(text, convert_to_numpy=True, normalize_embeddings=True)  # type: ignore[union-attr]
        if vec.ndim == 1:
            vec = vec.reshape(1, -1)
        return vec.astype(np.float32)

    def publish(
        self,
        agent_id: str,
        output: str,
        confidence: float = 0.5,
        trace_id: str = "",
    ) -> bool:
        """
        Опубликовать эмбеддинг выхода агента в общее пространство.

        Args:
            agent_id: идентификатор агента (напр. "MacroFlowAgent")
            output: текстовый выход агента
            confidence: уверенность агента [0..1]
            trace_id: сквозной trace_id для observability

        Returns:
            True если публикация успешна
        """
        if not output or not output.strip():
            logger.debug("[SharedEmbed] skip publish for %s (empty output)", agent_id)
            return False

        self._ensure_index()
        try:
            embedding = self._encode(output[:2048])
        except Exception as e:
            logger.warning("[SharedEmbed] encode failed for %s: %s", agent_id, e)
            return False

        with self._lock:
            if self._index_size >= MAX_INDEX_SIZE:
                oldest = self._entries.pop(0)
                try:
                    self._index.remove_ids(np.array([oldest["faiss_id"]], dtype=np.int64))
                except Exception:
                    pass
                self._index_size -= 1

            faiss_id = self._index_size
            self._index.add(embedding)
            self._index_size += 1

            self._entries.append({
                "agent_id": agent_id,
                "output_preview": output[:256],
                "confidence": confidence,
                "timestamp": time.time(),
                "trace_id": trace_id,
                "faiss_id": faiss_id,
            })

        _SHARED_EMBED_PUBLISH_TOTAL.labels(agent_id=agent_id).inc()
        _SHARED_EMBED_SIZE_GAUGE.set(self._index_size)
        logger.debug(
            "[SharedEmbed] published %s (confidence=%.2f, total=%d)",
            agent_id, confidence, self._index_size,
        )
        return True

    def query(
        self,
        query_text: str,
        k: int = QUERY_TOP_K,
        min_confidence: float = 0.0,
    ) -> list[tuple[str, float]]:
        """
        Найти топ-k наиболее релевантных агентов для запроса.

        Args:
            query_text: текст запроса
            k: количество результатов
            min_confidence: минимальная уверенность для включения в результат

        Returns:
            Список [(agent_id, relevance_score), ...] по убыванию релевантности
        """
        if self._index is None or self._index_size == 0:
            return []

        try:
            q_embed = self._encode(query_text)
        except Exception as e:
            logger.warning("[SharedEmbed] query encode failed: %s", e)
            return []

        k_effective = min(k, self._index_size)
        with self._lock:
            scores, ids = self._index.search(q_embed, k_effective)

        results: list[tuple[str, float]] = []
        seen: set[str] = set()

        for idx, score in zip(ids[0], scores[0]):
            if idx < 0 or idx >= len(self._entries):
                continue
            entry = self._entries[idx]
            agent_id = entry["agent_id"]
            conf = entry["confidence"]

            if agent_id in seen:
                continue
            if conf < min_confidence:
                continue

            seen.add(agent_id)
            results.append((agent_id, round(float(score), 4)))

        _SHARED_EMBED_QUERY_TOTAL.labels(pipeline="dynamic").inc()
        logger.debug(
            "[SharedEmbed] query '%s' → %d results (top score=%.4f)",
            query_text[:60], len(results),
            results[0][1] if results else 0.0,
        )
        return results

    def clear(self) -> None:
        """Очистить общее пространство."""
        with self._lock:
            self._entries.clear()
            self._index = None
            self._index_size = 0
            _SHARED_EMBED_SIZE_GAUGE.set(0)
        logger.info("[SharedEmbed] space cleared")

    @property
    def size(self) -> int:
        return self._index_size

    @property
    def stats(self) -> dict:
        with self._lock:
            agent_counts: dict[str, int] = {}
            for e in self._entries:
                agent_counts[e["agent_id"]] = agent_counts.get(e["agent_id"], 0) + 1
            return {
                "dimension": self.dimension,
                "total_entries": self._index_size,
                "max_size": MAX_INDEX_SIZE,
                "agent_distribution": agent_counts,
            }


_global_ses: Optional[SharedEmbeddingSpace] = None
_ses_lock = threading.Lock()


def get_shared_embedding() -> SharedEmbeddingSpace:
    """Получить глобальный singleton общего векторного пространства."""
    global _global_ses
    if _global_ses is None:
        with _ses_lock:
            if _global_ses is None:
                _global_ses = SharedEmbeddingSpace()
    return _global_ses
