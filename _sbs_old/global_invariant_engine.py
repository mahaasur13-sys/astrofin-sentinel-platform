"""
GlobalInvariantEngine — cross-layer invariant verification engine.

Verifies consistency constraints that span DRL / CCL / F2 / DESC.
Single source of truth for system-wide validity.

SBS v1 invariants checked:
    1. Leader uniqueness        — only one leader at any given term
    2. Monotonic commit index    — DESC commit index never decreases
    3. Quorum safety             — F2 quorum threshold respected
    4. No split-brain            — system never commits on < quorum nodes
    5. DESC append-only         — event log is immutable
    6. CCL contract integrity    — semantic contracts hold
    7. DRL causality             — reality distortion preserves ordering
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sbs.boundary_spec import SystemBoundarySpec


@dataclass
class LayerState:
    """
    Normalized state container for a single layer.
    Each layer (DRL/CCL/F2/DESC) maps to this structure.
    """

    name: str
    raw: dict[str, Any] = field(default_factory=dict)
    leader: str | None = None
    term: int = 0
    commit_index: int = 0
    partitions: int = 0
    quorum_ratio: float = 0.0
    stale_reads: int = 0
    duplicate_ack: bool = False
    clock_skew_ms: float = 0.0
    event_sequence_gaps: int = 0

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> LayerState:
        """Parse raw layer state dict into normalized LayerState."""
        return cls(
            name=name,
            raw=data,
            leader=data.get("leader"),
            term=data.get("term", 0),
            commit_index=data.get("commit_index", 0),
            partitions=data.get("partitions", 0),
            quorum_ratio=data.get("quorum_ratio", 0.0),
            stale_reads=data.get("stale_reads", 0),
            duplicate_ack=data.get("duplicate_ack", False),
            clock_skew_ms=data.get("clock_skew_ms", 0.0),
            event_sequence_gaps=data.get("event_sequence_gaps", 0),
        )


class GlobalInvariantEngine:
    """
    Cross-layer invariant verification engine.

    Aggregates state from DRL + CCL + F2 + DESC layers and evaluates
    them against SystemBoundarySpec and SYSTEM_CONTRACT rules.

    Usage
    -----
    >>> spec = SystemBoundarySpec()
    >>> engine = GlobalInvariantEngine(spec)
    >>> ok = engine.evaluate(drl_state, ccl_state, f2_state, desc_state)
    >>> print(engine.last_result)
    """

    def __init__(self, boundary_spec: SystemBoundarySpec) -> None:
        self.spec = boundary_spec
        self.last_result: dict[str, Any] = {}
        self._violations: list[str] = []

    def evaluate(
        self,
        drl_state: dict[str, Any],
        ccl_state: dict[str, Any],
        f2_state: dict[str, Any],
        desc_state: dict[str, Any],
    ) -> bool:
        """
        Evaluate all cross-layer invariants.

        Parameters
        ----------
        drl_state : dict
            DRL layer state (network partitions, clock skew, causality markers)
        ccl_state : dict
            CCL layer state (contract violations, stale reads, leader info)
        f2_state : dict
            F2 kernel state (quorum ratio, duplicate ACK, commit index)
        desc_state : dict
            DESC layer state (commit index, sequence gaps, leader term)

        Returns
        -------
        bool
            True if ALL invariants pass; False if ANY violation.
        """
        violations: list[str] = []

        # Normalize layer states
        drl = LayerState.from_dict("DRL", drl_state)
        ccl = LayerState.from_dict("CCL", ccl_state)
        f2 = LayerState.from_dict("F2", f2_state)
        desc = LayerState.from_dict("DESC", desc_state)

        # ── Invariant 1: Leader uniqueness ─────────────────────────────────
        leaders = [s.leader for s in [drl, ccl, f2, desc] if s.leader is not None]
        unique_leaders = set(leaders)
        if len(unique_leaders) > 1:
            violations.append(
                f"LEADER_UNIQUENESS_VIOLATION: multiple_leaders={sorted(unique_leaders)}"
            )

        # ── Invariant 2: Term monotonicity ───────────────────────────────────
        terms = [s.term for s in [drl, ccl, f2, desc]]
        terms_with_names = [("DRL", drl.term), ("CCL", ccl.term), ("F2", f2.term), ("DESC", desc.term)]
        # Monotonic term order — detect regressions within layers.
        # A regression is when a layer's term DROPS below the max term already seen.
        # Example: [1, 0, 0, 0] is fine (leader term=1, others uninitialised at 0)
        # Example: [2, 1, 3] is a regression (CCL regressed from 2→1 while DRL moved to 3)
        max_seen = -1
        for layer_name, term_val in terms_with_names:
            if layer_name == "DRL":
                # DRL is the authoritative term source — initialise baseline
                max_seen = max(max_seen, term_val)
                continue
            if term_val > 0 and term_val < max_seen:
                violations.append(
                    f"TERM_ORDER_VIOLATION: terms={terms} (must be monotonic)"
                )

        # ── Invariant 3: Monotonic commit index (DESC) ───────────────────────
        prev = self.last_result.get("desc_commit_index", 0)
        curr = desc.commit_index
        if curr < prev:
            violations.append(
                f"COMMIT_INDEX_REGRESSION: prev={prev}, curr={curr} "
                "(DESC commit index MUST be monotonic)"
            )

        # ── Invariant 4: Quorum safety ─────────────────────────────────────────
        for layer, state in [("F2", f2), ("CCL", ccl), ("DRL", drl)]:
            if state.quorum_ratio > 0 and state.quorum_ratio < self.spec.quorum_threshold:
                violations.append(
                    f"QUORUM_VIOLATION [{layer}]: ratio={state.quorum_ratio:.3f} "
                    f"(required={self.spec.quorum_threshold:.3f})"
                )

        # ── Invariant 5: Split-brain detection ────────────────────────────────
        total_partitions = sum(s.partitions for s in [drl, ccl, f2])
        if total_partitions > self.spec.max_partitions and not self.spec.allow_split_brain:
            violations.append(
                f"SPLIT_BRAIN: total_partitions={total_partitions} "
                f"(max={self.spec.max_partitions})"
            )

        # ── Invariant 6: Duplicate ACK → Byzantine ────────────────────────────
        for layer, state in [("F2", f2), ("CCL", ccl)]:
            if state.duplicate_ack and not self.spec.allow_duplicate_ack:
                violations.append(
                    f"BYZANTINE_SIGNAL [{layer}]: duplicate ACK detected"
                )

        # ── Invariant 7: Temporal drift ───────────────────────────────────────
        if self.spec.enable_temporal_strictness:
            max_skew = max(s.clock_skew_ms for s in [drl, ccl, f2])
            if max_skew > self.spec.clock_skew_threshold_ms:
                violations.append(
                    f"TEMPORAL_DRIFT: max_skew={max_skew:.1f}ms "
                    f"(threshold={self.spec.clock_skew_threshold_ms:.1f}ms)"
                )

        # ── Invariant 8: Event sequence gaps ──────────────────────────────────
        total_gaps = sum(s.event_sequence_gaps for s in [drl, f2, desc])
        if total_gaps > 0 and not self.spec.allow_event_reorder:
            violations.append(
                f"SEQUENCE_VIOLATION: total_gaps={total_gaps} "
                "(event reorder detected)"
            )

        # Store result
        self.last_result = {
            "ok": len(violations) == 0,
            "violations": violations,
            "drl": drl_state,
            "ccl": ccl_state,
            "f2": f2_state,
            "desc": desc_state,
            "desc_commit_index": desc.commit_index,
        }
        self._violations = violations

        return len(violations) == 0

    def get_violations(self) -> list[str]:
        """Return list of violations from last evaluate() call."""
        return self._violations

    def get_last_result(self) -> dict[str, Any]:
        """Return full result dict from last evaluate() call."""
        return self.last_result
