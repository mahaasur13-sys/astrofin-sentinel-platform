"""DAG node — base class with retry policy."""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from core.dag.context import DAGContext, NodeResult

logger = logging.getLogger(__name__)


class DAGNode(ABC):
    """
    Базовый узел DAG-пайплайна.

    Каждый узел:
    - Имеет уникальный id (по умолчанию — имя класса)
    - Принимает DAGContext и возвращает NodeResult
    - Опционально: max_retries, backoff_base_s, fallback_node_id
    - Опционально: timeout_ms

    Дочерние классы реализуют только run().
    """

    max_retries: int = 1
    backoff_base_s: float = 1.0
    timeout_ms: float = 30_000
    fallback_node_id: Optional[str] = None

    @property
    def node_id(self) -> str:
        return type(self).__name__

    @abstractmethod
    async def run(self, ctx: DAGContext) -> Any:
        """
        Основная логика узла. Принимает весь контекст (может читать
        результаты зависимых узлов через ctx.results).
        Возвращает результат любого типа — будет обёрнут в NodeResult.
        """
        ...

    async def execute(self, ctx: DAGContext) -> NodeResult:
        """
        Выполнить узел с retry-логикой. Вызывается DAGPipeline'ом.
        Пользовательские узлы не переопределяют этот метод — только run().
        """
        last_error: Optional[str] = None
        t0 = time.time()

        for attempt in range(self.max_retries):
            try:
                output = await asyncio.wait_for(
                    self.run(ctx),
                    timeout=self.timeout_ms / 1000,
                )
                duration_ms = (time.time() - t0) * 1000
                nr = NodeResult(
                    node_id=self.node_id,
                    output=output,
                    duration_ms=duration_ms,
                    retry_count=attempt,
                )
                logger.debug(
                    "DAG node %s completed in %.0fms (attempt %d/%d)",
                    self.node_id,
                    duration_ms,
                    attempt + 1,
                    self.max_retries,
                )
                return nr
            except asyncio.TimeoutError:
                last_error = f"timeout after {self.timeout_ms}ms"
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"

            if attempt < self.max_retries - 1:
                backoff = self.backoff_base_s * (2**attempt)
                logger.warning(
                    "DAG node %s attempt %d/%d failed: %s — retrying in %.1fs",
                    self.node_id,
                    attempt + 1,
                    self.max_retries,
                    last_error,
                    backoff,
                )
                await asyncio.sleep(backoff)

        duration_ms = (time.time() - t0) * 1000
        nr = NodeResult(
            node_id=self.node_id,
            output=None,
            duration_ms=duration_ms,
            error=last_error or "max retries exceeded",
            retry_count=self.max_retries,
        )

        logger.error(
            "DAG node %s FAILED after %d attempts: %s",
            self.node_id,
            self.max_retries,
            last_error,
        )

        if self.fallback_node_id:
            logger.warning(
                "DAG node %s activating fallback → %s",
                self.node_id,
                self.fallback_node_id,
            )

        return nr
