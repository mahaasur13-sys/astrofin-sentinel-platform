"""
mutation_ledger.py — immutable audit log of all control surface changes

v8.2a foundation #3
Append-only ledger: every mutation gets a UUID, timestamp, before/after snapshot, diff, and trigger source.
Mutation history is never deleted or modified — only extended.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np


class TriggerSource(Enum):
    """What triggered this mutation."""
    NONE = "none"
    DRIFT_RETUNE = "drift_retune"
    DRIFT_REWEIGHT = "drift_reweight"
    DRIFT_REPLAN = "drift_replan"
    MANUAL_OVERRIDE = "manual_override"
    SCHEDULED = "scheduled"
    ROLLBACK_REVERT = "rollback_revert"


@dataclass
class LedgerEntry:
    """
    Single immutable record of a mutation event.

    Fields:
        mutation_id      — UUID4, primary key
        timestamp        — ISO8601 UTC
        before_state     — θ₀ as list
        after_state      — θ₁ as list
        diff             — Δθ = θ₁ − θ₀ as list
        trigger_source   — what initiated this mutation
        trigger_metadata — drift_episode details, severity_score, etc.
        governor_decision — ALLOW/BLOCK at time of mutation
        invariants_passed — which invariants were validated before mutation
    """
    mutation_id: str
    timestamp: str
    before_state: list[float]
    after_state: list[float]
    diff: list[float]
    trigger_source: str
    trigger_metadata: dict[str, Any]
    governor_decision: str
    invariants_passed: list[str]
    diff_norm_l2: float = field(default=0.0)
    diff_norm_linf: float = field(default=0.0)

    def __post_init__(self):
        if self.diff_norm_l2 == 0.0 and len(self.diff) > 0:
            arr = np.array(self.diff)
            self.diff_norm_l2 = float(np.linalg.norm(arr, ord=2))
            self.diff_norm_linf = float(np.linalg.norm(arr, ord=np.inf))

    def to_dict(self) -> dict[str, Any]:
        return {
            "mutation_id": self.mutation_id,
            "timestamp": self.timestamp,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "diff": self.diff,
            "trigger_source": self.trigger_source,
            "trigger_metadata": self.trigger_metadata,
            "governor_decision": self.governor_decision,
            "invariants_passed": self.invariants_passed,
            "diff_norm_l2": self.diff_norm_l2,
            "diff_norm_linf": self.diff_norm_linf,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LedgerEntry:
        return cls(**d)


class MutationLedger:
    """
    Append-only audit log for all control surface mutations.

    Guarantees:
      - entries are never deleted or modified after creation
      - each mutation is assigned a UUID
      - diffs are computed at write time (not lazily)
      - can be persisted to disk as JSONL for durability

    Usage:
        ledger = MutationLedger()
        entry = ledger.record(
            theta_old=theta_0,
            theta_new=theta_1,
            trigger_source=TriggerSource.DRIFT_RETUNE,
            trigger_metadata={"drift_episode_id": ep_id, "severity_score": 0.62},
            governor_decision="ALLOW",
            invariants_passed=["param_drift", "gain_bound"],
        )
        assert ledger.last() == entry

        # persist
        ledger.flush(path="mutation_ledger.jsonl")

        # reload
        ledger2 = MutationLedger.load(path="mutation_ledger.jsonl")
    """

    def __init__(self, entries: list[LedgerEntry] | None = None):
        self._entries: list[LedgerEntry] = entries or []

    def record(
        self,
        theta_old: np.ndarray,
        theta_new: np.ndarray,
        trigger_source: TriggerSource,
        trigger_metadata: dict[str, Any] | None = None,
        governor_decision: str = "ALLOW",
        invariants_passed: list[str] | None = None,
    ) -> LedgerEntry:
        """Append a new mutation entry. Always appends; never modifies."""
        now = datetime.now(timezone.utc).isoformat(timespec="microseconds")
        arr_old = np.asarray(theta_old, dtype=np.float64).flatten()
        arr_new = np.asarray(theta_new, dtype=np.float64).flatten()
        diff = (arr_new - arr_old).tolist()

        entry = LedgerEntry(
            mutation_id=str(uuid.uuid4()),
            timestamp=now,
            before_state=arr_old.tolist(),
            after_state=arr_new.tolist(),
            diff=diff,
            trigger_source=trigger_source.value,
            trigger_metadata=trigger_metadata or {},
            governor_decision=governor_decision,
            invariants_passed=invariants_passed or [],
        )
        self._entries.append(entry)
        return entry

    def last(self) -> LedgerEntry | None:
        return self._entries[-1] if self._entries else None

    def get(self, mutation_id: str) -> LedgerEntry | None:
        return next((e for e in self._entries if e.mutation_id == mutation_id), None)

    def all(self) -> list[LedgerEntry]:
        return list(self._entries)

    def by_trigger(self, source: TriggerSource) -> list[LedgerEntry]:
        return [e for e in self._entries if e.trigger_source == source.value]

    def count(self) -> int:
        return len(self._entries)

    def rolling_density(self, window: int = 10) -> float:
        """Mutations per slot over last `window` entries."""
        if len(self._entries) == 0:
            return 0.0
        return len(self._entries[-window:]) / min(window, len(self._entries))

    def diff_stats(self) -> dict[str, float]:
        """Aggregate diff statistics across all entries."""
        if not self._entries:
            return {"mean_l2": 0.0, "max_l2": 0.0, "mean_linf": 0.0, "max_linf": 0.0}
        l2_norms = [e.diff_norm_l2 for e in self._entries]
        linf_norms = [e.diff_norm_linf for e in self._entries]
        return {
            "mean_l2": float(np.mean(l2_norms)),
            "max_l2": float(np.max(l2_norms)),
            "mean_linf": float(np.mean(linf_norms)),
            "max_linf": float(np.max(linf_norms)),
            "total_mutations": len(self._entries),
        }

    def flush(self, path: str | Path) -> None:
        """Persist ledger as JSONL (one JSON object per line)."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w") as f:
            for entry in self._entries:
                f.write(json.dumps(entry.to_dict()) + "\n")

    @classmethod
    def load(cls, path: str | Path) -> MutationLedger:
        """Load ledger from JSONL file."""
        p = Path(path)
        if not p.exists():
            return cls()
        entries = []
        with p.open("r") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(LedgerEntry.from_dict(json.loads(line)))
        return cls(entries)

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self):
        return iter(self._entries)
