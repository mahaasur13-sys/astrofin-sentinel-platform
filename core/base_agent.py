"""
AstroFin Sentinel v5 — Base Agent
RAG-first agent implementation with knowledge retrieval.
"""

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Generic, TypeVar

from knowledge.rag_retriever import RAGRetriever

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
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def __post_init__(self):
        if not (0 <= self.confidence <= 100):
            raise ValueError(f"confidence must be 0-100, got {self.confidence}")

    def to_dict(self) -> dict:
        # Handle both string signals (new) and enum signals (old)
        signal_value = self.signal.value if hasattr(self.signal, "value") else self.signal
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
        self._rag = RAGRetriever()

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

    def retrieve(
        self,
        query: str,
        domain: str = None,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Запрос к RAG базе знаний.

        Использовать когда:
        - Вопрос выходит за рамки instructions.md
        - Нужен факт из авторитетного источника
        - Требуется подтверждение перед выводом
        """
        return self._rag.retrieve(
            query=query,
            domain=domain or self.domain,
            top_k=top_k,
        )

    def format_retrieval(self, chunks: list[dict]) -> str:
        """Форматировать результаты RAG для включения в ответ."""
        if not chunks:
            return "• RAG: нет релевантных источников"

        lines = ["• RAG источники:"]
        for i, chunk in enumerate(chunks, 1):
            lines.append(f"  [{i}] {chunk['source']} (релевантность: {chunk['relevance_score']:.0%})")
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

    def _build_prompt(
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
                chunks = self.retrieve(user_task, top_k=5)
                if chunks:
                    parts.append(self.format_retrieval(chunks))
                else:
                    parts.append("• RAG: нет релевантных источников")
            except Exception:
                parts.append("• RAG currently unavailable (Ollama down)")

        if extra_context:
            parts.append(f"\n# Current Context\n\n{extra_context}")

        return "\n\n".join(parts)
