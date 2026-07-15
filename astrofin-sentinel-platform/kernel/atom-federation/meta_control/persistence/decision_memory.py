"""
decision_memory.py
~~~~~~~~~~~~~~~~~~~
Stores past decisions paired with their outcomes for long-horizon learning.

Provides:
  - append(decision, outcome) — record a decision + result
  - recent(n) — last N decisions
  - find_similar(decision, k) — k nearest decisions by payload similarity
  - outcome_stats() — aggregate statistics over recorded decisions

Used by proof_feedback_controller to correlate proof verdicts with real outcomes,
and by plan_graph/replanner to bias future decisions against bad historical patterns.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DecisionRecord:
    decision_id: int
    source: str
    priority: float
    payload: dict[str, Any]
    proof_verdict: bool
    temporal_confidence: float
    outcome: float | None = None          # None until observed
    outcome_timestamp: float | None = None
    decision_timestamp: float = field(default_factory=time.time)


class DecisionMemory:
    """
    Append-only store of decision + outcome pairs.
    Bounded by max_memory to avoid unbounded growth.
    """

    def __init__(self, max_memory: int = 1000) -> None:
        self._max_memory = max_memory
        self._deque: deque[DecisionRecord] = deque(maxlen=max_memory)
        self._id_counter = 0

    # ─── core interface ───────────────────────────────────────────────────────

    def append(
        self,
        source: str,
        priority: float,
        payload: dict[str, Any],
        proof_verdict: bool,
        temporal_confidence: float,
        outcome: float | None = None,
    ) -> int:
        """Record a decision and optionally its outcome. Returns decision_id."""
        self._id_counter += 1
        record = DecisionRecord(
            decision_id=self._id_counter,
            source=source,
            priority=priority,
            payload=payload,
            proof_verdict=proof_verdict,
            temporal_confidence=temporal_confidence,
            outcome=outcome,
            outcome_timestamp=time.time() if outcome is not None else None,
        )
        self._deque.append(record)
        return self._id_counter

    def record_outcome(self, decision_id: int, outcome: float) -> bool:
        """Backfill outcome for a recorded decision. Returns False if not found."""
        for rec in self._deque:
            if rec.decision_id == decision_id:
                rec.outcome = outcome
                rec.outcome_timestamp = time.time()
                return True
        return False

    def get(self, decision_id: int) -> DecisionRecord | None:
        for rec in self._deque:
            if rec.decision_id == decision_id:
                return rec
        return None

    def recent(self, n: int = 10) -> list[DecisionRecord]:
        """Last N records, newest last."""
        return list(self._deque)[-n:]

    def all(self) -> list[DecisionRecord]:
        return list(self._deque)

    # ─── similarity search ────────────────────────────────────────────────────

    def find_similar(
        self, payload: dict[str, Any], k: int = 5
    ) -> list[tuple[DecisionRecord, float]]:
        """
        Find k decisions with payloads most similar to `payload`.
        Similarity = fraction of shared keys with equal values.
        Returns list of (record, similarity_score).
        """
        scored: list[tuple[DecisionRecord, float]] = []
        for rec in self._deque:
            score = self._similarity(rec.payload, payload)
            scored.append((rec, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]

    @staticmethod
    def _similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
        if not a or not b:
            return 0.0
        shared_keys = set(a.keys()) & set(b.keys())
        if not shared_keys:
            return 0.0
        matches = sum(1 for k in shared_keys if a[k] == b[k])
        return matches / len(shared_keys)

    # ─── aggregate stats ─────────────────────────────────────────────────────

    def outcome_stats(self) -> dict[str, float]:
        """
        Compute aggregate statistics over all records with recorded outcomes.
        Returns dict with count, mean, min, max.
        """
        outcomes = [r.outcome for r in self._deque if r.outcome is not None]
        if not outcomes:
            return {"count": 0, "mean": 0.0, "min": 0.0, "max": 0.0}
        return {
            "count": len(outcomes),
            "mean": sum(outcomes) / len(outcomes),
            "min": min(outcomes),
            "max": max(outcomes),
        }

    def proof_reliability(self) -> float:
        """
        Fraction of decisions where proof_verdict matched a positive outcome.
        Useful for calibrating proof_kernel threshold.
        """
        matched = [
            r for r in self._deque
            if r.outcome is not None and r.proof_verdict == (r.outcome > 0.5)
        ]
        total = [r for r in self._deque if r.outcome is not None]
        return len(matched) / len(total) if total else 1.0

    @property
    def count(self) -> int:
        return len(self._deque)

    @property
    def latest(self) -> DecisionRecord | None:
        return self._deque[-1] if self._deque else None
