"""
AstroFin Sentinel v5 — Base Agent
RAG-first agent implementation with knowledge retrieval.
"""

from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

logger = logging.getLogger(__name__)


# ─── Standard degradation reason constants ───────────────────────────────────
# All machine-readable; agents must use these (or extend the list with a new
# constant) when calling self._degraded(...) so dashboards and the
# compliance linter can reason about it.

EPHEMERIS_UNAVAILABLE: str = "EPHEMERIS_UNAVAILABLE"
DATA_ROOM_TIMEOUT: str = "DATA_ROOM_TIMEOUT"
DATA_ROOM_ERROR: str = "DATA_ROOM_ERROR"
RAG_UNAVAILABLE: str = "RAG_UNAVAILABLE"
TIMEOUT: str = "TIMEOUT"
UNKNOWN: str = "UNKNOWN"

VALID_DEGRADATION_REASONS: frozenset[str] = frozenset(
    {
        EPHEMERIS_UNAVAILABLE,
        DATA_ROOM_TIMEOUT,
        DATA_ROOM_ERROR,
        RAG_UNAVAILABLE,
        TIMEOUT,
        UNKNOWN,
    }
)


class SignalDirection(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"
    AVOID = "AVOID"


@dataclass
class AgentResponse:
    """Стандартный ответ каждого агента."""

    agent_name: str
    signal: SignalDirection
    confidence: int  # 0 — 100
    reasoning: str
    sources: list[str] = field(default_factory=list)  # RAG chunk IDs
    metadata: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def __post_init__(self):
        if not (0 <= self.confidence <= 100):
            raise ValueError(f"confidence must be 0-100, got {self.confidence}")

    def to_dict(self) -> dict:
        # Handle both string signals (new) and enum signals (old)
        signal_value = (
            self.signal.value if hasattr(self.signal, "value") else self.signal
        )
        return {
            "agent_name": self.agent_name,
            "signal": signal_value,
            "confidence": int(self.confidence),
            "reasoning": self.reasoning,
            "sources": self.sources,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
        }


T = TypeVar("T", bound=AgentResponse)


class BaseAgent(ABC, Generic[T]):
    """
    Базовый класс для всех агентов v5.

    Каждый агент:
    1. Имеет instructions.md (загружается при инициализации)
    2. Может запрашивать RAG через self.retrieve()
    3. Возвращает AgentResponse

    Встроенные помощники:
        - self._degraded(reason, msg): стандартный «пониженный» AgentResponse.
          Используйте его в `run()`/`analyze()` на любом except, чтобы одна
          ошибка не вывела из строя весь оркестратор. Reasons — из
          `core.base_agent` (EPHEMERIS_UNAVAILABLE / DATA_ROOM_TIMEOUT / UNKNOWN / ...).
    """

    def __init__(
        self,
        name: str,
        instructions_path: str = None,
        domain: str = None,
        weight: float = 0.0,
    ):
        self.name = name
        self.weight = weight
        self.domain = domain
        self.instructions_md = ""
        # Start with a no-op degraded retriever; the real HybridRetriever
        # (pgvector + BM25) is constructed lazily on first await of
        # _get_retriever(). This keeps __init__ cheap and lets tests
        # patch.object(self._retriever, "retrieve") safely.
        self._retriever = _DegradedRetriever()

        if instructions_path:
            try:
                with open(instructions_path, encoding="utf-8") as f:
                    self.instructions_md = f.read()
            except FileNotFoundError:
                self.instructions_md = f"# {name}\n\nInstructions not found."

    def _degraded(self, reason: str, msg: str = "") -> "AgentResponse":
        """
        Build a uniform degraded AgentResponse.

        Args:
            reason: One of the standard constants
                    (EPHEMERIS_UNAVAILABLE, DATA_ROOM_TIMEOUT, UNKNOWN, ...).
            msg:    Human-readable detail (kept in reasoning, not metadata).

        Returns:
            AgentResponse(signal=NEUTRAL, confidence=0,
                          metadata={"degraded": True,
                                    "degradation_reason": reason}).

        Notes:
            Centralized in BaseAgent so every agent inherits it. Use from
            `run()` on any exception — never re-raise from the public entry
            point. If your failure is unusual, add a new constant to
            `core/base_agent.py` rather than passing a free-form string.
        """
        if reason not in VALID_DEGRADATION_REASONS:
            logger.warning(
                "agent_used_non_standard_degradation_reason",
                extra={"agent": self.name, "reason": reason},
            )
        return AgentResponse(
            agent_name=self.name,
            signal=SignalDirection.NEUTRAL,
            confidence=0,
            reasoning=f"Degraded: {reason}: {msg}" if msg else f"Degraded: {reason}",
            sources=[],
            metadata={"degraded": True, "degradation_reason": reason},
        )

    async def _get_retriever(self):
        """
        Lazy factory for the hybrid RAG retriever.

        Returns the cached HybridRetriever on subsequent calls. Falls back to
        a degraded stub (returning empty chunks) if the RAG stack cannot be
        initialised — agents stay runnable, just without knowledge.
        """
        if self._retriever is not None:
            return self._retriever

        try:
            from knowledge.hybrid_retriever import HybridRetriever

            self._retriever = HybridRetriever.create()
        except Exception as exc:  # noqa: BLE001 — degraded fallback
            logger.warning(
                "rag_retriever_init_failed",
                extra={"agent": self.name, "error": str(exc)},
            )
            self._retriever = _DegradedRetriever()
        return self._retriever

    async def retrieve(
        self,
        query: str,
        domain: str = None,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Запрос к RAG базе знаний (async, hybrid BM25+vector с RRF).

        Использовать когда:
        - Вопрос выходит за рамки instructions.md
        - Нужен факт из авторитетного источника
        - Требуется подтверждение перед выводом

        Returns an empty list on RAG failure; callers should treat that as
        «no knowledge» rather than raising.
        """
        try:
            retriever = await self._get_retriever()
            chunks = await retriever.retrieve(
                query=query,
                domain=domain or self.domain,
                top_k=top_k,
            )
            return chunks or []
        except Exception as exc:  # noqa: BLE001 — degraded fallback
            logger.warning(
                "rag_retrieve_failed",
                extra={"agent": self.name, "query": query[:80], "error": str(exc)},
            )
            return []

    def format_retrieval(self, chunks: list[dict]) -> str:
        """Форматировать результаты RAG для включения в ответ."""
        if not chunks:
            return "• RAG: нет релевантных источников"

        lines = ["• RAG источники:"]
        for i, chunk in enumerate(chunks, 1):
            lines.append(
                f"  [{i}] {chunk['source']} (релевантность: {chunk['relevance_score']:.0%})"
            )
            # Add first 100 chars of content as preview
            lines.append(f"      → {chunk['title']}")
            preview = chunk["content"][:100].replace("\n", " ")
            lines.append(f"      → {preview}...")

        return "\n".join(lines)

    @abstractmethod
    async def run(self, state: dict) -> AgentResponse:
        """
        Главный метод агента.

        Args:
            state: SentinelState из оркестратора

        Returns:
            AgentResponse с голосом агента
        """
        pass

    async def _build_prompt(
        self,
        user_task: str,
        extra_context: str = "",
        use_rag: bool = True,
    ) -> str:
        """
        Build system prompt for the agent.

        Includes:
        1. Instructions.md
        2. RAG chunks if enabled and domain is known
        3. Extra context
        """
        parts = [
            f"# Instructions for {self.name}\n\n{self.instructions_md}",
        ]

        if use_rag:
            try:
                chunks = await self.retrieve(user_task, top_k=5)
                if chunks:
                    parts.append(self.format_retrieval(chunks))
                else:
                    parts.append("• RAG: нет релевантных источников")
            except Exception:
                parts.append("• RAG currently unavailable (Ollama down)")

        if extra_context:
            parts.append(f"\n# Current Context\n\n{extra_context}")

        return "\n\n".join(parts)

    def generate(self, prompt: str, session_id: str | None = None) -> str:
        """
        RAG-first agent generation.

        1. Retrieve relevant knowledge via RAG index.
        2. Augment the prompt with retrieved context.
        3. Route the augmented prompt through LLM router.

        Args:
            prompt:     The user/agent prompt to route.
            session_id: Optional caching key for LLM routing decisions.

        Returns:
            LLM completion text.
        """
        from core.llm_router import route

        # === RAG retrieval ===
        try:
            from knowledge.rag_index import retrieve_context
            context = retrieve_context(prompt)
        except Exception:
            context = ""

        # Augment prompt with retrieved knowledge
        if context:
            augmented = f"Context:\n{context}\n\nQuestion: {prompt}"
        else:
            augmented = prompt

        sid = session_id or self.name[:8]
        return route(augmented, session_id=sid)

class _DegradedRetriever:
    """
    No-op retriever used when the real RAG stack is unavailable
    (e.g. pgvector pool cannot be created in CI).

    Returns an empty chunk list for any query; agents continue to function
    but without knowledge augmentation.
    """

    async def retrieve(
        self,
        query: str,
        domain: str | None = None,
        top_k: int = 5,
    ) -> list[dict]:
        return []
