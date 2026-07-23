"""slashing_engine.py — atom-federation-os v9.0+P8 Cryptoeconomic Enforcement.

Hard slashing engine: every violation → economic penalty.

SLASHING CONDITIONS (strict priority):
  S1 — invalid_proof      : ProofVerifier rejected signature
  S2 — runtime_violation   : RuntimeExecutionGuard detected breach
  S3 — ast_env_mismatch   : P0.2/P0.3 snapshot mismatch
  S4 — fork_detected       : DistributedLedger found conflicting branches
  S5 — double_vote         : Consensus caught equivocation
  S6 — bypass_attempt      : ExecutionAlgebraValidator found bypass

SLASH SEVERITY:
  S1 (invalid_proof)       : 1.0  (maximum — proof is foundation)
  S2 (runtime_violation)   : 1.0  (maximum — integrity broken)
  S3 (ast_env_mismatch)    : 0.75 (tampering detected)
  S4 (fork_detected)       : 1.0  (maximum — consensus broken)
  S5 (double_vote)          : 0.80 (Byzantine behavior)
  S6 (bypass_attempt)      : 0.50 (protocol violation)

INVARIANT:
  Violation(event) → slash(node, severity)
  No exceptions, no warnings, no grace periods.
"""
from __future__ import annotations

import threading
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .stake_registry import (
    StakeRegistry,
    EconomicViolation,
    ZeroStakeParticipant,
    MIN_STAKE,
)


# ── Violation Types ──────────────────────────────────────────────────────────

class ViolationType(Enum):
    INVALID_PROOF = "invalid_proof"
    RUNTIME_VIOLATION = "runtime_violation"
    AST_ENV_MISMATCH = "ast_env_mismatch"
    FORK_DETECTED = "fork_detected"
    DOUBLE_VOTE = "double_vote"
    BYPASS_ATTEMPT = "bypass_attempt"
    STALE_VOTE = "stale_vote"
    QUORUM_BREAK = "quorum_break"


# ── Severity Matrix ───────────────────────────────────────────────────────────

_SEVERITY: dict[ViolationType, float] = {
    ViolationType.INVALID_PROOF: 1.0,
    ViolationType.RUNTIME_VIOLATION: 1.0,
    ViolationType.FORK_DETECTED: 1.0,
    ViolationType.DOUBLE_VOTE: 0.80,
    ViolationType.AST_ENV_MISMATCH: 0.75,
    ViolationType.BYPASS_ATTEMPT: 0.50,
    ViolationType.STALE_VOTE: 0.30,
    ViolationType.QUORUM_BREAK: 0.60,
}


# ── Slash Record ─────────────────────────────────────────────────────────────

@dataclass
class SlashRecord:
    slash_id: str
    node_id: str
    violation: ViolationType
    severity: float
    amount_slashed: float
    reason: str
    proof_ref: Optional[str]
    detected_at: float = field(default_factory=time.time)
    detected_by: str = ""


# ── Slashing Engine ──────────────────────────────────────────────────────────

class SlashingEngine:
    """
    Hard slashing engine for cryptoeconomic enforcement.

    Every detected violation → automatic slash.
    No exceptions, no warnings, no disable flags.

    Integration points:
      - ProofVerifier      → S1 (invalid_proof)
      - RuntimeExecutionGuard → S2 (runtime_violation)
      - runtime_guard.verify_ast_env() → S3 (ast_env_mismatch)
      - DistributedLedger  → S4 (fork_detected)
      - Consensus          → S5 (double_vote)
      - ExecutionAlgebraValidator → S6 (bypass_attempt)

    Usage:
        engine = SlashingEngine(registry)
        engine.slash("node-1", ViolationType.INVALID_PROOF, "signature mismatch")
    """

    def __init__(self, registry: Optional[StakeRegistry] = None) -> None:
        self._registry = registry or StakeRegistry()
        self._history: list[SlashRecord] = []
        self._lock = threading.Lock()
        self._slashed_nodes: set[str] = set()

    @property
    def registry(self) -> StakeRegistry:
        return self._registry

    # ── Core slashing ─────────────────────────────────────────────────────

    def slash(
        self,
        node_id: str,
        violation: ViolationType,
        reason: str,
        severity: Optional[float] = None,
        proof_ref: Optional[str] = None,
        detected_by: str = "",
    ) -> SlashRecord:
        """
        Slash `node_id` for `violation`.

        Severity is auto-computed from _SEVERITY unless overridden.
        Raises ZeroStakeParticipant silently (node already ejected).

        Returns SlashRecord with details.
        """
        sev = severity if severity is not None else _SEVERITY.get(violation, 0.50)

        record = SlashRecord(
            slash_id=self._make_id(),
            node_id=node_id,
            violation=violation,
            severity=sev,
            amount_slashed=0.0,
            reason=reason,
            proof_ref=proof_ref,
            detected_by=detected_by,
        )

        with self._lock:
            try:
                amount = self._registry.slash(
                    node_id,
                    reason=reason,
                    severity=sev,
                    proof_hash=proof_ref,
                )
                record.amount_slashed = amount
                self._slashed_nodes.add(node_id)
            except ZeroStakeParticipant:
                record.amount_slashed = 0.0

            self._history.append(record)

        return record

    def slash_batch(
        self,
        events: list[tuple[str, ViolationType, str, Optional[float]]],
    ) -> list[SlashRecord]:
        """Slash multiple nodes from a batch of violation events."""
        results = []
        for node_id, vtype, reason, sev in events:
            results.append(
                self.slash(node_id, vtype, reason, severity=sev)
            )
        return results

    # ── Integration hooks ─────────────────────────────────────────────────

    def on_invalid_proof(
        self,
        node_id: str,
        reason: str,
        proof_ref: Optional[str] = None,
    ) -> SlashRecord:
        """Hook: ProofVerifier rejected a proof."""
        return self.slash(
            node_id,
            ViolationType.INVALID_PROOF,
            reason=f"invalid_proof: {reason}",
            severity=_SEVERITY[ViolationType.INVALID_PROOF],
            proof_ref=proof_ref,
            detected_by="ProofVerifier",
        )

    def on_runtime_violation(
        self,
        node_id: str,
        violation_msg: str,
        stack: Optional[str] = None,
    ) -> SlashRecord:
        """Hook: RuntimeExecutionGuard detected a breach."""
        return self.slash(
            node_id,
            ViolationType.RUNTIME_VIOLATION,
            reason=f"runtime_violation: {violation_msg[:200]}",
            severity=_SEVERITY[ViolationType.RUNTIME_VIOLATION],
            detected_by="RuntimeExecutionGuard",
        )

    def on_ast_env_mismatch(
        self,
        node_id: str,
        expected_hash: str,
        actual_hash: str,
    ) -> SlashRecord:
        """Hook: P0.2/P0.3 detected snapshot mismatch."""
        return self.slash(
            node_id,
            ViolationType.AST_ENV_MISMATCH,
            reason=f"AST/ENV hash mismatch: expected={expected_hash[:16]} actual={actual_hash[:16]}",
            severity=_SEVERITY[ViolationType.AST_ENV_MISMATCH],
            detected_by="P0.2/P0.3",
        )

    def on_fork_detected(
        self,
        node_id: str,
        branch_a: str,
        branch_b: str,
    ) -> SlashRecord:
        """Hook: DistributedLedger detected a fork."""
        return self.slash(
            node_id,
            ViolationType.FORK_DETECTED,
            reason=f"fork detected: {branch_a[:8]} vs {branch_b[:8]}",
            severity=_SEVERITY[ViolationType.FORK_DETECTED],
            detected_by="DistributedLedger",
        )

    def on_double_vote(
        self,
        node_id: str,
        round_a: int,
        round_b: int,
    ) -> SlashRecord:
        """Hook: Consensus detected double voting (Byzantine)."""
        return self.slash(
            node_id,
            ViolationType.DOUBLE_VOTE,
            reason=f"double_vote: round {round_a} and {round_b}",
            severity=_SEVERITY[ViolationType.DOUBLE_VOTE],
            detected_by="Consensus",
        )

    def on_bypass_attempt(
        self,
        node_id: str,
        bypass_path: str,
    ) -> SlashRecord:
        """Hook: ExecutionAlgebraValidator detected bypass."""
        return self.slash(
            node_id,
            ViolationType.BYPASS_ATTEMPT,
            reason=f"bypass_attempt: {bypass_path}",
            severity=_SEVERITY[ViolationType.BYPASS_ATTEMPT],
            detected_by="ExecutionAlgebraValidator",
        )

    def on_stale_vote(
        self,
        node_id: str,
        vote_round: int,
        current_round: int,
    ) -> SlashRecord:
        """Hook: Consensus received vote from old round."""
        return self.slash(
            node_id,
            ViolationType.STALE_VOTE,
            reason=f"stale_vote: vote_round={vote_round} current_round={current_round}",
            severity=_SEVERITY[ViolationType.STALE_VOTE],
            detected_by="Consensus",
        )

    # ── Query ─────────────────────────────────────────────────────────────

    def get_history(
        self,
        limit: int = 100,
        node_id: Optional[str] = None,
    ) -> list[SlashRecord]:
        """Return slash history, optionally filtered by node."""
        history = self._history[-limit:]
        if node_id:
            return [r for r in history if r.node_id == node_id]
        return history

    @property
    def total_slashed(self) -> int:
        return len(self._history)

    @property
    def slashed_nodes(self) -> set[str]:
        return set(self._slashed_nodes)

    def is_slashed(self, node_id: str) -> bool:
        """True if node has been slashed at least once."""
        return node_id in self._slashed_nodes

    # ── Internal ─────────────────────────────────────────────────────────

    @staticmethod
    def _make_id() -> str:
        import uuid
        return uuid.uuid4().hex[:12]

    def summary(self) -> dict:
        return {
            "total_slashes": len(self._history),
            "slashed_nodes": len(self._slashed_nodes),
            "by_type": {
                v.value: sum(1 for r in self._history if r.violation == v)
                for v in ViolationType
            },
        }


# ── Singleton instance for cross-module access ──────────────────────────────

_ENGINE: Optional[SlashingEngine] = None
_ENGINE_LOCK = threading.Lock()


def get_slashing_engine() -> SlashingEngine:
    """Thread-safe singleton access to the global SlashingEngine."""
    global _ENGINE
    if _ENGINE is None:
        with _ENGINE_LOCK:
            if _ENGINE is None:
                _ENGINE = SlashingEngine()
    return _ENGINE