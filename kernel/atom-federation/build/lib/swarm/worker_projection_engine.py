# ATOMFEDERATION-OS - WorkerProjectionEngine
# Swarm layer — tick-based deterministic worker state projection
# =========================================================

import hashlib
import queue
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from orchestration.execution_gateway import ExecutionGateway


@dataclass
class WorkerProjection:
    tick: int
    worker_id: str
    projected_state: bytes
    confidence: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ProjectionResult:
    success: bool
    worker_id: str
    tick: int
    projection: WorkerProjection | None = None
    error: str | None = None


class AtomicQueue:
    # Thread-safe queue with deterministic ordering
    # Ensures no race conditions in concurrent worker updates

    def __init__(self):
        self._queue = queue.Queue()
        self._lock = threading.Lock()

    def put(self, item: Any) -> None:
        with self._lock:
            self._queue.put(item)

    def get_all(self) -> list[Any]:
        items = []
        with self._lock:
            while not self._queue.empty():
                items.append(self._queue.get_nowait())
        return items

    def is_empty(self) -> bool:
        with self._lock:
            return self._queue.empty()


class WorkerProjectionEngine:
    # =========================================================
    # WORKER PROJECTION ENGINE — Swarm Deterministic Projection
    # All projections flow through ExecutionGateway
    # =========================================================

    def __init__(self, gateway: ExecutionGateway):
        self._gateway = gateway
        self._projections: dict[str, WorkerProjection] = {}
        self._pending_queue = AtomicQueue()
        self._lock = threading.RLock()
        self._worker_fingerprint: dict[str, str] = {}

    @ExecutionGateway.requires_gateway
    def project_worker(
        self,
        tick: int,
        worker_id: str,
        raw_state: bytes
    ) -> ProjectionResult:
        with self._lock:
            if not self._gateway.is_safe():
                return ProjectionResult(
                    success=False,
                    worker_id=worker_id,
                    tick=tick,
                    error='Gateway safety check failed'
                )

            fingerprint = self._compute_fingerprint(worker_id, raw_state)
            self._worker_fingerprint[worker_id] = fingerprint

            projected_state = self._apply_projection(raw_state, tick)
            confidence = self._calculate_confidence(tick, worker_id)

            projection = WorkerProjection(
                tick=tick,
                worker_id=worker_id,
                projected_state=projected_state,
                confidence=confidence
            )

            self._projections[worker_id] = projection
            self._pending_queue.put((tick, worker_id, fingerprint))

            return ProjectionResult(
                success=True,
                worker_id=worker_id,
                tick=tick,
                projection=projection
            )

    @ExecutionGateway.requires_gateway
    def flush_pending(self) -> list[ProjectionResult]:
        results = []
        pending = self._pending_queue.get_all()

        for tick, worker_id, fingerprint in pending:
            if worker_id in self._projections:
                proj = self._projections[worker_id]
                results.append(ProjectionResult(
                    success=True,
                    worker_id=worker_id,
                    tick=tick,
                    projection=proj
                ))
            else:
                results.append(ProjectionResult(
                    success=False,
                    worker_id=worker_id,
                    tick=tick,
                    error='Projection not found after flush'
                ))

        return results

    def _compute_fingerprint(self, worker_id: str, state: bytes) -> str:
        combined = f'{worker_id}:{state.hex()[:32]}'.encode()
        return hashlib.sha256(combined).hexdigest()

    def _apply_projection(self, raw_state: bytes, tick: int) -> bytes:
        # Deterministic projection logic
        # In production: would apply smoothing, interpolation, etc.
        tick_marker = (tick % 256).to_bytes(1, 'big')
        return raw_state + tick_marker

    def _calculate_confidence(self, tick: int, worker_id: str) -> float:
        # Deterministic confidence based on tick and worker identity
        base_confidence = min(tick / 100.0, 1.0)
        worker_mod = int(hashlib.md5(worker_id.encode()).hexdigest()[:4], 16) % 100
        adjustment = worker_mod / 1000.0
        return min(base_confidence + adjustment, 1.0)

    def get_projection(self, worker_id: str) -> WorkerProjection | None:
        with self._lock:
            return self._projections.get(worker_id)

    def get_all_projections(self) -> dict[str, WorkerProjection]:
        with self._lock:
            return dict(self._projections)
