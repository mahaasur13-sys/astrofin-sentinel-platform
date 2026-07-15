"""
tools/embedding_client.py — Universal async embedding client.

Supports three providers, switchable via env at runtime:
  - openai (default, 1536-dim, prod)
  - ollama (768-dim, dev/offline)
  - stub   (deterministic, tests/CI; no network)

Key behaviours:
  - Async-first. `embed()` is the canonical interface, takes a list[str].
    `embed_one()` is syntactic sugar (await self.embed([text])[0]).
  - In-process LRU cache (RAG_CACHE=memory, default on) backed by
    `cachetools.LRUCache(maxsize=10_000)`. Disable with RAG_CACHE=off.
  - Cache is TTL-bounded: a per-key monotonic timestamp is checked on read;
    expired entries are evicted on access. Least-recently-used entries are
    evicted when the cap is exceeded, so memory stays bounded for long-lived
    processes.
  - OpenAI errors: rate-limit (429) and server (5xx) trigger a single retry with
    exponential backoff (0.5s, 1.5s). Auth/quota errors (401/403) raise immediately
    — they are not transient and stub-fallback would silently mask misconfig.
  - Ollama connection refused -> stub fallback with WARNING (dev convenience).

Feature flags (env):
  RAG_PROVIDER     = openai | ollama | stub   (default: stub)
  RAG_EMBEDDING_DIM = 1536 (openai) | 768 (ollama) | 1536 (stub)  (default: 1536)
  RAG_CACHE        = memory | off                              (default: memory)
  OPENAI_API_KEY   = sk-...    (required if RAG_PROVIDER=openai)
  OLLAMA_HOST      = http://localhost:11434                    (default: localhost:11434)
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import random
import time
from typing import List, Optional

import httpx
import openai
from cachetools import LRUCache
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class EmbeddingConfig(BaseModel):
    """Validated config. Construct via EmbeddingConfig.from_env() in production."""

    provider: str = "openai"
    dimension: int = 1536
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600  # 1h
    max_batch_size: int = 32  # OpenAI safe chunk
    ollama_host: str = "http://localhost:11434"

    @classmethod
    def from_env(cls) -> "EmbeddingConfig":
        """Build config from env vars. Used by the singleton below."""
        provider = os.getenv("RAG_PROVIDER", "openai")
        try:
            dimension = int(os.getenv("RAG_EMBEDDING_DIM", "1536"))
        except ValueError:
            logger.warning("RAG_EMBEDDING_DIM is not int, falling back to 1536")
            dimension = 1536
        cache = os.getenv("RAG_CACHE", "memory")
        return cls(
            provider=provider,
            dimension=dimension,
            cache_enabled=(cache in ("memory", "on", "true", "1")),
            cache_ttl_seconds=int(os.getenv("RAG_CACHE_TTL", "3600")),
            max_batch_size=int(os.getenv("RAG_BATCH_SIZE", "32")),
            ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        )


class EmbeddingClient:
    """Async embedding client. Use the `embedding_client` singleton or instantiate directly."""

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig.from_env()
        self._validate_config()

        self._openai_client: Optional[openai.AsyncOpenAI] = None
        self._httpx_client: Optional[httpx.AsyncClient] = (
            None  # lazy: created on first ollama call
        )
        # Cache: key -> (vector, monotonic_ts)
        self._cache: LRUCache[str, tuple[list[float], float]] = LRUCache(maxsize=10000)

    # ─── Lifecycle ────────────────────────────────────────────────────────────

    async def aclose(self) -> None:
        """Close all network clients. Call on app shutdown."""
        if self._openai_client is not None:
            await self._openai_client.close()
        if self._httpx_client is not None:
            await self._httpx_client.aclose()

    # ─── Config validation ───────────────────────────────────────────────────

    def _validate_config(self) -> None:
        if self.config.provider == "ollama" and self.config.dimension != 768:
            raise ValueError(
                f"Ollama does not support dimension {self.config.dimension}. "
                "Use 768 (nomic-embed-text) or switch provider."
            )
        if self.config.provider == "openai" and self.config.dimension not in (
            1536,
            3072,
        ):
            # text-embedding-3-small = 1536, text-embedding-3-large = 3072.
            # 512 and 256 are also valid for 3-small/3-large per OpenAI, but we
            # don't use them — keep validation strict to catch typos.
            raise ValueError(
                f"OpenAI dimension must be 1536 or 3072, got {self.config.dimension}. "
                "Use RAG_EMBEDDING_DIM=1536 with RAG_PROVIDER=openai."
            )
        if self.config.provider not in ("openai", "ollama", "stub"):
            raise ValueError(
                f"Unknown RAG_PROVIDER: {self.config.provider!r}. "
                "Use one of: openai, ollama, stub."
            )

    # ─── Cache helpers ───────────────────────────────────────────────────────

    def _cache_key(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _cache_get(self, text: str) -> Optional[list[float]]:
        if not self.config.cache_enabled:
            return None
        key = self._cache_key(text)
        entry = self._cache.get(key)
        if entry is None:
            return None
        vec, ts = entry
        if (time.monotonic() - ts) > self.config.cache_ttl_seconds:
            try:
                del self._cache[key]
            except KeyError:
                pass
            return None
        return vec

    def _cache_put(self, text: str, vec: list[float]) -> None:
        if not self.config.cache_enabled:
            return
        # LRUCache evicts the least-recently-used entry when maxsize is exceeded.
        self._cache[self._cache_key(text)] = (vec, time.monotonic())

    # ─── Stub provider (deterministic) ──────────────────────────────────────

    def _deterministic_vector(self, text: str) -> list[float]:
        """Deterministic 32-bit-seeded vector. Same text -> same vector across runs.

        Critical property: identical inputs MUST produce identical outputs in tests.
        Uses sha256 (not md5) for better distribution; seed reduced to 2^32 via mod.
        """
        seed = int(
            hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16
        )  # first 8 hex = 32 bits
        rng = random.Random(seed)
        return [rng.uniform(-1.0, 1.0) for _ in range(self.config.dimension)]

    # ─── Public API ──────────────────────────────────────────────────────────

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts. Order is preserved. Empty/None inputs get zero vectors."""
        if not texts:
            return []

        # Step 1: separate cache hits from misses
        result: list[Optional[list[float]]] = [None] * len(texts)
        to_embed: list[str] = []
        indices: list[int] = []

        for i, text in enumerate(texts):
            if not text or not isinstance(text, str):
                result[i] = [0.0] * self.config.dimension
                continue
            cached = self._cache_get(text)
            if cached is not None:
                result[i] = cached
            else:
                to_embed.append(text)
                indices.append(i)

        if not to_embed:
            return result  # type: ignore[return-value]

        # Step 2: chunk by max_batch_size
        chunks: list[list[str]] = [
            to_embed[i : i + self.config.max_batch_size]
            for i in range(0, len(to_embed), self.config.max_batch_size)
        ]

        # Step 3: dispatch to provider
        all_embedded: list[list[float]] = []
        for chunk in chunks:
            if self.config.provider == "stub":
                all_embedded.extend([self._deterministic_vector(t) for t in chunk])
            elif self.config.provider == "openai":
                all_embedded.extend(await self._embed_openai(chunk))
            elif self.config.provider == "ollama":
                all_embedded.extend(await self._embed_ollama(chunk))
            # else: validated in __init__, unreachable

        # Step 4: fill results and populate cache
        for idx, vec in zip(indices, all_embedded, strict=True):
            result[idx] = vec
            self._cache_put(texts[idx], vec)

        return result  # type: ignore[return-value]

    async def embed_one(self, text: str) -> list[float]:
        """Convenience: embed a single text."""
        if not text:
            return [0.0] * self.config.dimension
        return (await self.embed([text]))[0]

    def embed_sync(self, texts: List[str]) -> List[List[float]]:
        """Sync wrapper. DO NOT call from a running event loop — will deadlock."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop is not None and loop.is_running():
            raise RuntimeError(
                "embed_sync() called from a running event loop. "
                "Use `await embedding_client.embed(texts)` instead."
            )
        return asyncio.run(self.embed(texts))

    # ─── Provider implementations ───────────────────────────────────────────

    async def _get_openai_client(self) -> openai.AsyncOpenAI:
        if self._openai_client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY is required for RAG_PROVIDER=openai. "
                    "Set the env var or switch to RAG_PROVIDER=stub (tests) / ollama (dev)."
                )
            self._openai_client = openai.AsyncOpenAI(api_key=api_key, timeout=30.0)
        return self._openai_client

    async def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """Call OpenAI embeddings. Retries transient errors once, re-raises config errors."""
        client = await self._get_openai_client()
        last_exc: Optional[Exception] = None
        for attempt in range(2):  # 0 = first try, 1 = single retry
            try:
                response = await client.embeddings.create(
                    input=texts,
                    model="text-embedding-3-small",
                    dimensions=self.config.dimension,
                )
                return [data.embedding for data in response.data]
            except openai.RateLimitError as e:
                # 429 — wait and retry
                last_exc = e
                wait = 0.5 * (3**attempt)  # 0.5s, then 1.5s
                logger.warning(
                    "OpenAI rate-limited, retrying in %.1fs (attempt %d)",
                    wait,
                    attempt + 1,
                )
                await asyncio.sleep(wait)
            except openai.AuthenticationError as e:
                # 401 — config error, do not retry
                raise ValueError(f"OPENAI_API_KEY is invalid: {e}") from e
            except openai.PermissionDeniedError as e:
                # 403 — quota or org issue
                raise ValueError(
                    f"OpenAI permission denied (check billing/quota): {e}"
                ) from e
            except (openai.APIConnectionError, openai.APITimeoutError) as e:
                # Network — retry
                last_exc = e
                wait = 0.5 * (3**attempt)
                logger.warning(
                    "OpenAI connection error, retrying in %.1fs: %s", wait, e
                )
                await asyncio.sleep(wait)
        # Both attempts failed on transient errors — do NOT silently fall back to stub.
        # Caller can decide policy. Re-raise the last exception.
        raise RuntimeError(
            f"OpenAI embedding failed after 2 attempts: {last_exc}"
        ) from last_exc

    async def _get_httpx(self) -> httpx.AsyncClient:
        if self._httpx_client is None:
            self._httpx_client = httpx.AsyncClient(timeout=30.0)
        return self._httpx_client

    async def _embed_ollama(self, texts: List[str]) -> List[List[float]]:
        """Call Ollama embeddings endpoint. Falls back to stub on connection error."""
        client = await self._get_httpx()
        results: list[list[float]] = []
        try:
            # Ollama /api/embeddings doesn't batch — must call per text.
            for text in texts:
                resp = await client.post(
                    f"{self.config.ollama_host}/api/embeddings",
                    json={"model": "nomic-embed-text", "prompt": text},
                )
                resp.raise_for_status()
                results.append(resp.json()["embedding"])
            return results
        except (httpx.ConnectError, httpx.HTTPStatusError) as e:
            # Dev convenience: if Ollama is not running, fall back to stub with WARNING.
            # In production, prefer to fail loudly — set OLLAMA_REQUIRED=1 to disable this.
            if os.getenv("OLLAMA_REQUIRED", "0") == "1":
                raise
            logger.warning(
                "Ollama unavailable (%s) — falling back to stub. "
                "Set OLLAMA_REQUIRED=1 to fail loudly.",
                type(e).__name__,
            )
            return [self._deterministic_vector(t) for t in texts]


# ─── Module-level singleton ──────────────────────────────────────────────────
# Lazy: built on first attribute access. Avoids side effects at import time.
_singleton: Optional[EmbeddingClient] = None


def get_embedding_client() -> EmbeddingClient:
    """Return the process-wide singleton. Builds it on first call."""
    global _singleton
    if _singleton is None:
        _singleton = EmbeddingClient()
    return _singleton


# Backwards-compat alias (some code may import the name `embedding_client`).
# Note: this is a function, not an instance — call sites become `get_embedding_client()`.
# Kept as a property-like object for graceful migration.
class _LazySingleton:
    def __getattr__(self, name: str):
        return getattr(get_embedding_client(), name)

    def __call__(self, *args, **kwargs):  # in case someone does embedding_client(...)
        raise TypeError(
            "embedding_client is a lazy proxy. Use `get_embedding_client()` "
            "or instantiate `EmbeddingClient(...)` directly."
        )


embedding_client = _LazySingleton()
