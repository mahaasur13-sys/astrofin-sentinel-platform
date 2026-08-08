#!/usr/bin/env python3
"""AstroFin Prompt Cache — кэширование LLM-промптов и ответов.

P1 (Sprint G): LRU-кэш с TTL, эмбеддинг-сравнение для семантического кэширования.
Prometheus-метрики: dag_prompt_cache_hits_total, dag_prompt_cache_misses_total.

Levels:
  1. Exact match cache (хэш промпта + модель) — O(1), мгновенный hit.
  2. Semantic cache (cosine similarity > 0.95) — через sentence-transformers.
     Только для "дорогих" моделей (OpenRouter).

Usage:
    from core.cache.prompt_cache import PromptCache, get_prompt_cache

    cache = get_prompt_cache()

    # Exact match
    cached = cache.get_exact("What is BTC price?", model="openrouter/auto")
    if cached:
        return cached

    response = await call_llm(prompt)
    cache.set_exact("What is BTC price?", response, model="openrouter/auto")

    # Semantic (expensive)
    similar = cache.get_semantic("Bitcoin price now?", threshold=0.95)
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from collections import OrderedDict
from typing import Any

import numpy as np

try:
    from prometheus_client import Counter

    _PROMPT_CACHE_HITS = Counter(
        "dag_prompt_cache_hits_total",
        "Total prompt cache hits (exact + semantic)",
        ["cache_type"],
    )
    _PROMPT_CACHE_MISSES = Counter(
        "dag_prompt_cache_misses_total",
        "Total prompt cache misses (exact + semantic)",
        ["cache_type"],
    )
    _METRICS_ENABLED = True
except ImportError:
    _METRICS_ENABLED = False

def _record_cache_hit(cache_type: str) -> None:
    """Record a cache hit metric (safe no-op if prometheus_client unavailable)."""
    if _METRICS_ENABLED:
        _PROMPT_CACHE_HITS.labels(cache_type=cache_type).inc()

def _record_cache_miss(cache_type: str) -> None:
    """Record a cache miss metric (safe no-op if prometheus_client unavailable)."""
    if _METRICS_ENABLED:
        _PROMPT_CACHE_MISSES.labels(cache_type=cache_type).inc()

logger = logging.getLogger(__name__)

MAX_ENTRIES = int(os.getenv("PROMPT_CACHE_MAX_ENTRIES", "500"))
DEFAULT_TTL_S = float(os.getenv("PROMPT_CACHE_DEFAULT_TTL", "300"))  # 5 min
ASTRO_TTL_S = float(os.getenv("PROMPT_CACHE_ASTRO_TTL", "86400"))    # 24 hr
SEMANTIC_THRESHOLD = float(os.getenv("PROMPT_CACHE_SEMANTIC_THRESHOLD", "0.95"))


class PromptCache:
    """Двухуровневый кэш: exact match + semantic similarity."""

    def __init__(
        self,
        max_entries: int = MAX_ENTRIES,
        default_ttl: float = DEFAULT_TTL_S,
        enabled: bool = True,
    ) -> None:
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self.enabled = enabled
        self._exact_cache: OrderedDict[str, tuple[float, str]] = OrderedDict()
        self._semantic_embeddings: dict[str, np.ndarray] = {}
        self._semantic_responses: dict[str, str] = {}
        self._embedder = None
        self._hits = 0
        self._misses = 0

    def _key(self, prompt: str, model: str = "") -> str:
        raw = f"{prompt}|{model}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def get_exact(self, prompt: str, model: str = "", ttl: float | None = None) -> str | None:
        """Exact-match lookup by SHA-256 hash."""
        if not self.enabled:
            return None

        key = self._key(prompt, model)
        entry = self._exact_cache.get(key)
        if entry is None:
            self._misses += 1
            _record_cache_miss("exact")
            return None

        timestamp, response = entry
        effective_ttl = ttl if ttl is not None else self.default_ttl
        if time.time() - timestamp > effective_ttl:
            del self._exact_cache[key]
            self._misses += 1
            _record_cache_miss("exact")
            return None

        self._hits += 1
        _record_cache_hit("exact")
        logger.debug(f"[PromptCache] exact hit (model={model or 'default'})")
        return response

    def set_exact(self, prompt: str, response: str, model: str = "") -> None:
        """Сохранить в exact-match кэш."""
        if not self.enabled:
            return

        key = self._key(prompt, model)
        if key in self._exact_cache:
            self._exact_cache.move_to_end(key)
        self._exact_cache[key] = (time.time(), response)

        while len(self._exact_cache) > self.max_entries:
            self._exact_cache.popitem(last=False)

    def get_semantic(self, prompt: str, threshold: float = SEMANTIC_THRESHOLD, model: str = "") -> str | None:
        """Semantic similarity lookup через sentence-transformers."""
        if not self.enabled or not self._semantic_embeddings:
            self._misses += 1
            _record_cache_miss("semantic")
            return None

        emb = self._embed(prompt)
        if emb is None:
            self._misses += 1
            _record_cache_miss("semantic")
            return None

        best_key: str | None = None
        best_score = -1.0

        for cached_key, cached_emb in self._semantic_embeddings.items():
            score = float(np.dot(emb, cached_emb) / (np.linalg.norm(emb) * np.linalg.norm(cached_emb) + 1e-8))
            if score > best_score:
                best_score = score
                best_key = cached_key

        if best_key and best_score >= threshold:
            self._hits += 1
            _record_cache_hit("semantic")
            logger.debug(f"[PromptCache] semantic hit: score={best_score:.4f}, threshold={threshold}")
            return self._semantic_responses[best_key]

        self._misses += 1
        _record_cache_miss("semantic")
        return None

    def set_semantic(self, prompt: str, response: str) -> None:
        """Сохранить в semantic кэш."""
        if not self.enabled:
            return

        emb = self._embed(prompt)
        if emb is None:
            return

        key = hashlib.sha256(prompt.encode()).hexdigest()[:32]
        self._semantic_embeddings[key] = emb
        self._semantic_responses[key] = response

        if len(self._semantic_embeddings) > self.max_entries // 2:
            oldest = next(iter(self._semantic_embeddings))
            del self._semantic_embeddings[oldest]
            self._semantic_responses.pop(oldest, None)

    def _embed(self, text: str) -> np.ndarray | None:
        """Ленивая инициализация sentence-transformers."""
        try:
            if self._embedder is None:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
            return self._embedder.encode(text, convert_to_numpy=True)  # type: ignore[no-any-return]
        except Exception as e:
            logger.warning(f"[PromptCache] embedder init failed: {e}")
            return None

    def invalidate(self, prompt: str | None = None, model: str = "") -> int:
        """Инвалидировать записи. prompt=None → очистить всё."""
        removed = 0
        if prompt is None:
            removed = len(self._exact_cache) + len(self._semantic_embeddings)
            self._exact_cache.clear()
            self._semantic_embeddings.clear()
            self._semantic_responses.clear()
        else:
            key = self._key(prompt, model)
            if key in self._exact_cache:
                del self._exact_cache[key]
                removed += 1
        logger.info(f"[PromptCache] invalidated {removed} entries")
        return removed

    @property
    def stats(self) -> dict[str, Any]:
        total = self._hits + self._misses
        return {
            "enabled": self.enabled,
            "entries": len(self._exact_cache),
            "semantic_entries": len(self._semantic_embeddings),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / max(total, 1), 3),
            "max_entries": self.max_entries,
            "default_ttl_s": self.default_ttl,
        }

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / max(total, 1)


_global_cache: PromptCache | None = None


def get_prompt_cache() -> PromptCache:
    """Получить глобальный экземпляр PromptCache."""
    global _global_cache
    if _global_cache is None:
        _global_cache = PromptCache(
            enabled=os.getenv("PROMPT_CACHE_ENABLED", "true").lower() == "true",
            max_entries=MAX_ENTRIES,
            default_ttl=DEFAULT_TTL_S,
        )
    return _global_cache
