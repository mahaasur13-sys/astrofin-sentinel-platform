"""State-store and job-state protocols.

The two `StateStore` classes currently in the workspace have **incompatible
backends** (PostgreSQL thread-pool vs. event-sourcing KV) and **identical
names**. That's exactly the kind of cross-repo duplication S2 exists to fix.

This module exposes *only* the contract — the smallest surface both impls
already provide. Concrete repos will keep their full implementations but
must satisfy this protocol.

Two cross-repo Surprising Connections close here:
  * `StateStore → StateStore` (AsurDev/admission_controller ↔ roma-execution-bridge)
  * `StateStore → StateStore` (AsurDev/scheduler_v3 ↔ roma-execution-bridge)

See ADR-0002 for the full rationale.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Protocol, runtime_checkable


# ── Status enum ────────────────────────────────────────────────────────────


class JobStatus(str, Enum):
    """Common job lifecycle shared across schedulers.

    `PENDING` covers both `submitted` (ROMA) and `created` (home-cluster-iac);
    concrete impls may map to backend-specific labels in their adapters.
    """

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# ── Job-state DTO ──────────────────────────────────────────────────────────


@runtime_checkable
class JobStateProtocol(Protocol):
    """Common job-state DTO.

    Concrete backends (Postgres, event-sourced KV) have richer fields, but
    every consumer reads at least `job_id`, `status`, and `error_message`.
    """

    job_id: str
    status: JobStatus
    error_message: str | None
    slurm_job_id: int | None
    priority: int


# ── State store ────────────────────────────────────────────────────────────


@runtime_checkable
class StateStoreProtocol(Protocol):
    """Common surface for any StateStore implementation.

    Subset of the union of `home-cluster-iac/state_store/client.py:StateStore`
    and `roma-execution-bridge/durability/state_store.py:StateStore`.
    """

    def get_job_state(self, job_id: str) -> JobStateProtocol | None: ...

    def save_snapshot(self, key: str, payload: dict[str, Any]) -> None: ...

    def load_snapshot(self, key: str) -> dict[str, Any] | None: ...

    def compare_and_rollback(
        self,
        key: str,
        expected: dict[str, Any],
        replacement: dict[str, Any],
    ) -> bool: ...


__all__ = [
    "JobStatus",
    "JobStateProtocol",
    "StateStoreProtocol",
]


# Legacy alias.
StateStore = StateStoreProtocol     # type: ignore[misc, assignment]
