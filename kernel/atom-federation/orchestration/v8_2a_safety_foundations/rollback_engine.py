"""
rollback_engine.py — state recovery subsystem

v8.2a foundation #4
Checkpoint → snapshot full state (θ, metadata)
restore(checkpoint_id) → revert to that exact snapshot
revert(last_mutation_id) → undo the last applied mutation
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class Checkpoint:
    """
    Immutable snapshot of the full control surface state.

    Fields:
        checkpoint_id    — UUID4, primary key
        timestamp        — ISO8601 UTC
        theta            — full parameter vector
        metadata         — arbitrary context (health_score, plan_stability_index, ...)
        parent_mutation_id — mutation that triggered this checkpoint (if any)
    """
    checkpoint_id: str
    timestamp: str
    theta: list[float]
    metadata: dict[str, Any]
    parent_mutation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "timestamp": self.timestamp,
            "theta": self.theta,
            "metadata": self.metadata,
            "parent_mutation_id": self.parent_mutation_id,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Checkpoint:
        return cls(**d)


class RollbackEngine:
    """
    State recovery via checkpoints + mutation replay.

    Guarantees:
      - deterministic restore (same checkpoint_id → same state every time)
      - idempotent rollback (calling restore twice is safe)
      - checkpoints are immutable (never modified after creation)
      - rollback to mutation = restore to checkpoint created AFTER that mutation

    Usage:
        engine = RollbackEngine()

        # snapshot current state before a mutation
        cp = engine.checkpoint(
            theta=theta_current,
            metadata={"health_score": 0.72, "plan_stability_index": 0.88},
        )
        theta_mutated = mutate(theta_current)

        # if mutation violates safety → restore
        theta_restored = engine.restore(cp.checkpoint_id)
        np.testing.assert_allclose(theta_current, theta_restored, atol=1e-9)

        # revert last applied mutation (go back to pre-mutation state)
        # requires ledger integration
        success, theta_reverted = engine.revert(
            last_mutation_id=entry.mutation_id,
            ledger=ledger,
        )
    """

    def __init__(self, checkpoints: dict[str, Checkpoint] | None = None):
        self._checkpoints: dict[str, Checkpoint] = checkpoints or {}

    # ── Checkpoint management ─────────────────────────────────────────────

    def checkpoint(
        self,
        theta: np.ndarray,
        metadata: dict[str, Any] | None = None,
        parent_mutation_id: str | None = None,
    ) -> Checkpoint:
        """
        Create an immutable checkpoint of the current state.

        Args:
            theta: current parameter vector
            metadata: arbitrary context (health, PSI, etc.)
            parent_mutation_id: link to mutation that triggered this checkpoint

        Returns:
            Checkpoint — never modified after creation
        """
        arr = np.asarray(theta, dtype=np.float64).flatten()
        cp = Checkpoint(
            checkpoint_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(timespec="microseconds"),
            theta=arr.tolist(),
            metadata=metadata or {},
            parent_mutation_id=parent_mutation_id,
        )
        self._checkpoints[cp.checkpoint_id] = cp
        return cp

    def restore(self, checkpoint_id: str) -> np.ndarray:
        """
        Restore state to the checkpoint identified by checkpoint_id.

        Args:
            checkpoint_id: UUID of the target checkpoint

        Returns:
            np.ndarray — the θ vector at that checkpoint

        Raises:
            KeyError: if checkpoint_id is unknown
        """
        if checkpoint_id not in self._checkpoints:
            raise KeyError(f"unknown checkpoint_id: {checkpoint_id}")
        return np.array(self._checkpoints[checkpoint_id].theta, dtype=np.float64)

    def revert(self, last_mutation_id: str, ledger: Any) -> tuple[bool, np.ndarray | None]:
        """
        Revert the last applied mutation by finding the pre-mutation checkpoint.

        Args:
            last_mutation_id: mutation_id of the mutation to undo
            ledger: MutationLedger instance (v8.2a #3)

        Returns:
            (success, theta) — True if revert succeeded, theta is pre-mutation state
            (False, None) if mutation_id not in ledger
        """
        entry = ledger.get(last_mutation_id)
        if entry is None:
            return False, None

        # pre-mutation state is stored directly in the ledger entry
        return True, np.array(entry.before_state, dtype=np.float64)

    def get(self, checkpoint_id: str) -> Checkpoint | None:
        return self._checkpoints.get(checkpoint_id)

    def list_checkpoints(self) -> list[Checkpoint]:
        return sorted(self._checkpoints.values(), key=lambda c: c.timestamp)

    def latest(self) -> Checkpoint | None:
        if not self._checkpoints:
            return None
        return max(self._checkpoints.values(), key=lambda c: c.timestamp)

    def flush(self, path: str | Path) -> None:
        """Persist all checkpoints as JSON."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        data = [cp.to_dict() for cp in self._checkpoints.values()]
        with p.open("w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: str | Path) -> RollbackEngine:
        """Load checkpoints from JSON file."""
        p = Path(path)
        if not p.exists():
            return cls()
        with p.open("r") as f:
            data = json.load(f)
        checkpoints = {cp["checkpoint_id"]: Checkpoint.from_dict(cp) for cp in data}
        return cls(checkpoints)

    def __len__(self) -> int:
        return len(self._checkpoints)
