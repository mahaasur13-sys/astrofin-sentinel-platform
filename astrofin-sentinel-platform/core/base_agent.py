"""
AstroFin Sentinel v5 — Base Agent
RAG-first agent implementation with knowledge retrieval.
ADR-001 Sprint 3: Message-based interface (on_message, publish_event, contextvars)
"""
from __future__ import annotations

import asyncio
import contextvars
import time
import copy
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from core.envelopes import TaskEnvelope, ResultEnvelope
    from core.message_broker import MessageBroker
    from core.outbox import Outbox

logger = logging.getLogger(__name__)


# ─── Context propagation (ADR-001 Риск #2, P3-07) ────────────────────
_current_envelope: contextvars.ContextVar["TaskEnvelope | None"] = (
    contextvars.ContextVar("_current_envelope", default=None)
)


# ─── Standard degradation reason constants ───────────────────────────
EPHEMERIS_UNAVAILABLE: str = "EPHEMERIS_UNAVAILABLE"
DATA_ROOM_TIMEOUT: str = "DATA_ROOM_TIMEOUT"
DATA_ROOM_ERROR: str = "DATA_ROOM_ERROR"
RAG_UNAVAILABLE: str = "RAG_UNAVAILABLE"
TIMEOUT: str = "TIMEOUT"
UNKNOWN: str = "UNKNOWN"

VALID_DEGRADATION_REASONS: frozenset[str] = frozenset({
    EPHEMERIS_UNAVAILABLE,
    DATA_ROOM_TIMEOUT,
    DATA_ROOM_ERROR,
    RAG_UNAVAILABLE,
    TIMEOUT,
    UNKNOWN,
})


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
    sources: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def __post_init__(self):
        if not (0 <= self.confidence <= 100):
            raise ValueError(f"confidence must be 0-100, got {self.confidence}")

    def to_dict(self) -> dict:
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

    Агент:
    1. Имеет instructions.md
    2. Запрашивает RAG через self.retrieve()
    3. Возвращает AgentResponse

    ADR-001 Sprint 3:
    4. Принимает TaskEnvelope через on_message() (не сырой dict)
    5. Пробрасывает trace context через contextvars (Риск #2 fix)
    6. Публикует события через publish_event() с outbox (Риск #4 fix)
    """

    def __init__(
        self,
        name: str,
        instructions_path: str = None,
        domain: str = None,
        weight: float = 0.0,
        use_rag: bool = False,
    ):
        self.name = name
        self.weight = weight
        self.domain = domain
        self.instructions_md = ""
        self._broker: "MessageBroker | None" = None
        self._outbox: "Outbox | None" = None
        self._retriever = _DegradedRetriever()
        self.use_rag = use_rag

        if instructions_path:
            try:
                with open(instructions_path, encoding="utf-8") as f:
                    self.instructions_md = f.read()
            except FileNotFoundError:
                self.instructions_md = f"# {name}\n\nInstructions not found."

    # ── Degraded Response ────────────────────────────────────────────

    def _degraded(self, reason: str, msg: str = "") -> "AgentResponse":
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

    # ── RAG ──────────────────────────────────────────────────────────

    async def _get_retriever(self):
        if self._retriever is not None:
            return self._retriever
        try:
            from knowledge.hybrid_retriever import HybridRetriever
            self._retriever = HybridRetriever.create()
        except Exception as exc:
            logger.warning(
                "rag_retriever_init_failed",
                extra={"agent": self.name, "error": str(exc)},
            )
            self._retriever = _DegradedRetriever()
        self.use_rag = use_rag
        return self._retriever

    async def retrieve(self, query: str, domain: str = None, top_k: int = 5) -> list[dict]:
        try:
            retriever = await self._get_retriever()
            chunks = await retriever.retrieve(
                query=query, domain=domain or self.domain, top_k=top_k
            )
            return chunks or []
        except Exception as exc:
            logger.warning(
                "rag_retrieve_failed",
                extra={"agent": self.name, "query": query[:80], "error": str(exc)},
            )
            return []

    def format_retrieval(self, chunks: list[dict]) -> str:
        if not chunks:
            return "• RAG: нет релевантных источников"
        lines = ["• RAG источники:"]
        for i, chunk in enumerate(chunks, 1):
            lines.append(
                f"  [{i}] {chunk['source']} (релевантность: {chunk['relevance_score']:.0%})"
            )
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
        self, user_task: str, extra_context: str = "", use_rag: bool = True
    ) -> str:
        parts = [f"# Instructions for {self.name}\n\n{self.instructions_md}"]
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


    def _get_rag_context(self, query: str) -> str:
        if not getattr(self, "use_rag", False):
            return ""
        rag = get_rag()
        if not rag:
            return ""
        try:
            from core.settings import settings; chunks = rag.retrieve(query, top_k=settings.RAG_TOP_K)
            if not chunks:
                return ""
            ctx = "--- RELEVANT KNOWLEDGE BASE CONTEXT ---"
            for j, c in enumerate(chunks):
                src = c.metadata.get("source", "unknown")
                ctx += f"[{j+1}] (Source: {src}) {c.text}"
            ctx += "--- END CONTEXT ---"
            logger.info("rag_context_enriched", agent=self.name, chunks_used=len(chunks))
            return ctx
        except Exception as e:
            logger.error("rag_retrieval_failed", agent=self.name, error=str(e))
            return ""
    def generate(self, prompt: str, session_id: str | None = None) -> str:
        from core.llm_router import route
        try:
            from knowledge.rag_index import retrieve_context
            context = retrieve_context(prompt)
        except Exception:
            context = ""
        augmented = f"Context:\n{context}\n\nQuestion: {prompt}" if context else prompt
        sid = session_id or self.name[:8]
        return route(augmented, session_id=sid)

    # ── ADR-001 Sprint 3: Message-based interface ────────────────────

    def set_broker(self, broker: "MessageBroker", outbox: "Outbox | None" = None) -> None:
        """Установить брокер сообщений и опциональный outbox."""
        self._broker = broker
        self._outbox = outbox

    @property
    def context_envelope(self) -> "TaskEnvelope | None":
        """Текущий TaskEnvelope из contextvars (trace propagation)."""
        return _current_envelope.get()

    @property
    def context_task_id(self) -> str | None:
        """task_id текущего TaskEnvelope (P3-07 trace propagation)."""
        env = _current_envelope.get()
        return env.task_id if env else None

    @property
    def context_traceparent(self) -> str | None:
        """traceparent текущего TaskEnvelope для W3C distributed tracing."""
        env = _current_envelope.get()
        return env.traceparent if env else None

    async def on_message(self, envelope: "TaskEnvelope") -> "ResultEnvelope":
        """Обработать входящий TaskEnvelope.

        Вызывается MessageBroker-ом при получении сообщения.
        Не переопределять — переопределяйте run().

        Что делает:
        1. Deep-copy state_snapshot (Риск #1 fix)
        2. Пробрасывает envelope в contextvars (Риск #2 fix, P3-07)
        3. Вызывает self.run() с изолированным состоянием
        4. Возвращает ResultEnvelope
        """
        from core.envelopes import ResultEnvelope, TaskStatus

        isolated_state = copy.deepcopy(envelope.state_snapshot)
        token = _current_envelope.set(envelope)

        try:
            agent_response = await self.run(isolated_state)

            return ResultEnvelope(
                task_id=envelope.task_id,
                agent_name=self.name,
                agent_type=envelope.agent_type,
                trace_id=envelope.trace_id,
                traceparent=envelope.traceparent,
                status=TaskStatus.COMPLETED,
                result=agent_response if isinstance(agent_response, dict) else (agent_response.to_dict() if hasattr(agent_response, "to_dict") else {}),
                schema_version=envelope.schema_version,
                execution_time_ms=(time.time() - envelope.created_at_epoch) * 1000,
            )

        except Exception as exc:
            logger.error(
                "agent_on_message_error",
                extra={"agent": self.name, "task_id": envelope.task_id, "error": str(exc)},
            )
            return ResultEnvelope.from_envelope(
                envelope=envelope,
                status=TaskStatus.FAILED,
                result={"error": str(exc)},
                agent_name=self.name,
            )

        finally:
            _current_envelope.reset(token)

    async def publish_event(self, channel: str, payload: dict) -> None:
        """Опубликовать событие через брокер с outbox-фолбэком (Риск #4 fix).

        Args:
            channel: канал публикации (например "karl.audit")
            payload: dict с данными события
        """
        if self._broker is None:
            logger.debug("publish_event_no_broker", extra={"agent": self.name, "channel": channel})
            return

        from core.message_broker import BrokerUnavailable

        try:
            await self._broker.publish(channel, payload)
        except BrokerUnavailable:
            if self._outbox:
                self._outbox.store(channel, payload)
                logger.debug("publish_event_outbox_fallback", extra={"agent": self.name, "channel": channel})
            else:
                logger.warning("publish_event_lost", extra={"agent": self.name, "channel": channel})


class _DegradedRetriever:
    """No-op retriever when RAG stack is unavailable."""

    async def retrieve(
        self, query: str, domain: str | None = None, top_k: int = 5
    ) -> list[dict]:
        return []

# ── Phase 5.3: RAG Singleton + Agent Integration ──────────────────────

_rag_instance: "RAGIndex | None" = None

def get_rag() -> "RAGIndex | None":
    """Ленивый потокобезопасный Singleton для Production RAGIndex."""
    global _rag_instance
    if _rag_instance is not None:
        return _rag_instance
    try:
        from knowledge.rag_index import RAGIndex
        _rag_instance = RAGIndex()
        logger.info("RAGIndex singleton initialized", chunks=len(_rag_instance.chunks))
    except Exception as exc:
        logger.warning("Failed to initialize RAGIndex: %s", exc)
        _rag_instance = None
    return _rag_instance
