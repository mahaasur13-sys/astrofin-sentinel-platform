"""
core.envelopes — ADR-001 Sprint 3: TaskEnvelope / ResultEnvelope

Типы для распределённой оркестрации агентов.

ADR-001 Risk fixes:
  Риск #1: state_snapshot — deepcopy при создании Envelope
  Риск #2: задача → run() — trace context через contextvars (P3-07)
  W3C Trace Context (P3-06): traceparent в metadata для Tempo/Jaeger
  Schema Versioning: schema_version = "1.0.0"
"""
from __future__ import annotations

import copy
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

SCHEMA_VERSION = "1.0.0"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    SKIPPED = "SKIPPED"


@dataclass
class TaskEnvelope:
    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "deadline_epoch": self.deadline_epoch,
            "state_snapshot": self.state_snapshot,
            "traceparent": self.traceparent,
            "priority": self.priority.value if hasattr(self.priority, "value") else self.priority,
            "schema_version": self.schema_version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TaskEnvelope":
        """Deserialize from dict (JSON round-trip)."""
        return cls(
            agent_name=data.get("agent_name", ""),
            state_snapshot=data.get("state_snapshot", {}),
            deadline_epoch=data.get("deadline_epoch", 0.0),
            priority=data.get("priority", "NORMAL"),
            metadata=data.get("metadata", {}),
        )

    """Конверт с задачей для агента.

    Отправляется оркестратором → агенту через MessageBroker.
    """

    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str = ""
    task_type: str = "analyze"
    state_snapshot: dict[str, Any] = field(default_factory=dict)
    deadline_epoch: float = 0.0
    schema_version: str = SCHEMA_VERSION
    metadata: dict[str, str] = field(default_factory=dict)
    created_at_epoch: float = field(default_factory=time.time)
    correlation_id: str = ""
    priority: int = 50
    retry_count: int = 0
    max_retries: int = 0

    def __post_init__(self):
        """Deep-copy state_snapshot — предотвращение мутаций (Риск #1)."""
        if self.state_snapshot:
            self.state_snapshot = copy.deepcopy(self.state_snapshot)

        if "traceparent" not in self.metadata:
            trace_id = uuid.uuid4().hex
            span_id = uuid.uuid4().hex[:16]
            self.metadata["traceparent"] = f"00-{trace_id}-{span_id}-01"

    @property
    def trace_id(self) -> str:
        tp = self.metadata.get("traceparent", "")
        if tp and "-" in tp:
            return tp.split("-")[1]
        return self.task_id

    @property
    def span_id(self) -> str:
        tp = self.metadata.get("traceparent", "")
        parts = tp.split("-")
        if len(parts) >= 3:
            return parts[2]
        return ""

    @property
    def traceparent(self) -> str:
        return self.metadata.get("traceparent", "")

    @property
    def is_expired(self) -> bool:
        return self.deadline_epoch > 0 and time.time() > self.deadline_epoch

    @property
    def remaining_ms(self) -> float:
        if self.deadline_epoch <= 0:
            return float("inf")
        return max(0, (self.deadline_epoch - time.time()) * 1000)

    def child_task(self, agent_name: str, state: dict | None = None) -> "TaskEnvelope":
        child = TaskEnvelope.new(
            agent_name=agent_name,
            state=state or copy.deepcopy(self.state_snapshot),
            task_type=self.task_type,
            deadline_seconds=max(0, self.deadline_epoch - time.time()) if self.deadline_epoch > 0 else 0,
            correlation_id=self.correlation_id,
            priority=self.priority,
            max_retries=self.max_retries,
        )
        child.metadata["traceparent"] = f"00-{self.trace_id}-{uuid.uuid4().hex[:16]}-01"
        return child

    def to_broker_payload(self) -> dict:
        return {
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "task_type": self.task_type,
            "state_snapshot": self.state_snapshot,
            "deadline_epoch": self.deadline_epoch,
            "schema_version": self.schema_version,
            "metadata": self.metadata,
            "created_at_epoch": self.created_at_epoch,
            "correlation_id": self.correlation_id,
            "priority": self.priority,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_broker_payload(cls, payload: dict) -> "TaskEnvelope":
        return cls(**{
            k: payload.get(k, v.default if hasattr(v, "default") else v.default_factory())
            if k != "state_snapshot" else payload.get(k, {})
            for k, v in cls.__dataclass_fields__.items()
        }) if False else cls(
            task_id=payload.get("task_id", str(uuid.uuid4())),
            agent_name=payload.get("agent_name", ""),
            task_type=payload.get("task_type", "analyze"),
            state_snapshot=payload.get("state_snapshot", {}),
            deadline_epoch=payload.get("deadline_epoch", 0.0),
            schema_version=payload.get("schema_version", SCHEMA_VERSION),
            metadata=payload.get("metadata", {}),
            created_at_epoch=payload.get("created_at_epoch", 0.0),
            correlation_id=payload.get("correlation_id", ""),
            priority=payload.get("priority", 50),
            retry_count=payload.get("retry_count", 0),
            max_retries=payload.get("max_retries", 0),
        )

    @classmethod
    def new(
        cls,
        agent_name: str,
        state: dict,
        task_type: str = "analyze",
        deadline_seconds: float = 0.0,
        correlation_id: str = "",
        priority: int = 50,
        max_retries: int = 0,
        metadata: dict[str, str] | None = None,
    ) -> "TaskEnvelope":
        deadline = time.time() + deadline_seconds if deadline_seconds > 0 else 0.0
        return cls(
            agent_name=agent_name,
            task_type=task_type,
            state_snapshot=state,
            deadline_epoch=deadline,
            correlation_id=correlation_id,
            priority=priority,
            max_retries=max_retries,
            metadata=metadata or {},
        )


@dataclass
class ResultEnvelope:
    """Конверт с результатом от агента.

    Отправляется агентом → оркестратору через MessageBroker.
    """

    task_id: str = ""
    agent_name: str = ""
    agent_type: str = ""
    trace_id: str = ""
    traceparent: str = ""
    status: TaskStatus = TaskStatus.COMPLETED
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    started_at_epoch: float | None = None
    completed_at_epoch: float | None = None
    execution_time_ms: float = 0.0
    schema_version: str = SCHEMA_VERSION
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if self.completed_at_epoch is None:
            self.completed_at_epoch = time.time()
        if not self.trace_id:
            self.trace_id = self.task_id

    @classmethod
    def from_envelope(
        cls,
        envelope: TaskEnvelope,
        status: TaskStatus,
        result: dict | None = None,
        error: str = "",
        execution_time_ms: float = 0.0,
        agent_name: str = "",
    ) -> "ResultEnvelope":
        return cls(
            task_id=envelope.task_id,
            agent_name=agent_name or envelope.agent_name,
            trace_id=envelope.trace_id,
            traceparent=envelope.traceparent,
            status=status,
            result=result or {},
            error=error,
            execution_time_ms=execution_time_ms,
            schema_version=envelope.schema_version,
            metadata=dict(envelope.metadata),
        )

    def to_broker_payload(self) -> dict:
        return {
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "trace_id": self.trace_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at_epoch": self.started_at_epoch,
            "completed_at_epoch": self.completed_at_epoch,
            "execution_time_ms": self.execution_time_ms,
            "schema_version": self.schema_version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_broker_payload(cls, payload: dict) -> "ResultEnvelope":
        return cls(
            task_id=payload.get("task_id", ""),
            agent_name=payload.get("agent_name", ""),
            trace_id=payload.get("trace_id", ""),
            status=TaskStatus(payload.get("status", "COMPLETED")),
            result=payload.get("result", {}),
            error=payload.get("error", ""),
            started_at_epoch=payload.get("started_at_epoch"),
            completed_at_epoch=payload.get("completed_at_epoch"),
            execution_time_ms=payload.get("execution_time_ms", 0.0),
            schema_version=payload.get("schema_version", SCHEMA_VERSION),
            metadata=payload.get("metadata", {}),
        )
