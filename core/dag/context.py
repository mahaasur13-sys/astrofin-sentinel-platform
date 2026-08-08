"""DAG context — immutable state passed between nodes."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class NodeResult:
    """Стандартизированный выход узла DAG."""

    node_id: str
    output: Any
    duration_ms: float
    error: Optional[str] = None
    retry_count: int = 0

    @property
    def ok(self) -> bool:
        return self.error is None


@dataclass
class DAGContext:
    """Иммутабельный контекст, передаваемый между узлами."""

    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    state: dict = field(default_factory=dict)
    results: dict[str, NodeResult] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)

    def get(self, node_id: str, default: Any = None) -> NodeResult | None:
        return self.results.get(node_id, default)

    def set(self, node_id: str, result: NodeResult) -> None:
        self.results[node_id] = result

    @property
    def elapsed_ms(self) -> float:
        return (time.time() - self.start_time) * 1000
