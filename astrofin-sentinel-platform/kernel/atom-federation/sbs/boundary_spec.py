"""
SystemBoundarySpec — hard boundary validation gate.

Defines what states the system MAY and MAY NOT enter.
All validation is strict: no soft defaults, no silent bypass.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SystemBoundarySpec:
    """
    Immutable specification of system hard boundaries.

    These flags define the UNSAFE states that the system must
    never enter regardless of runtime behavior.

    Attributes
    ----------
    allow_split_brain : bool
        If False, any detected split-brain partition is a hard failure.
    allow_event_reorder : bool
        If False, events arriving out-of-order are treated as corruption.
    allow_duplicate_ack : bool
        If False, duplicate ACKs indicate Byzantine behavior.
    allow_uncommitted_read : bool
        If False, reading uncommitted state is prohibited.
    quorum_threshold : float
        Minimum quorum ratio (0.0–1.0) required for commit.
        Default 0.67 = 2/3 majority.
    max_partitions : int
        Maximum allowed network partitions before system halts.
    enable_temporal_strictness : bool
        If True, clock skew beyond threshold is classified as TEMPORAL_DRIFT.
    clock_skew_threshold_ms : float
        Maximum allowed clock drift between nodes (ms).
    """

    allow_split_brain: bool = False
    allow_event_reorder: bool = True
    allow_duplicate_ack: bool = False
    allow_uncommitted_read: bool = False
    quorum_threshold: float = 0.67
    max_partitions: int = 1
    enable_temporal_strictness: bool = False
    clock_skew_threshold_ms: float = 100.0

    # Internal violation registry — populated during validate()
    _violations: tuple[str, ...] = field(default_factory=tuple, repr=False, compare=False)

    def validate(self, system_state: dict[str, Any]) -> bool:
        """
        Hard boundary validation gate.

        Evaluates the full system state against all boundary rules.
        Returns True ONLY if the system is within the defined safe envelope.

        Any violation populates self._violations for audit.

        Parameters
        ----------
        system_state : dict
            Must contain keys from DRL / CCL / F2 / DESC layers:
            - partitions (int): number of detected network partitions
            - quorum_ratio (float): achieved quorum as ratio (0.0–1.0)
            - uncommitted_reads (int): count of stale/uncommitted reads
            - duplicate_ack (bool): duplicate ACK detected
            - clock_skew_ms (float): max observed clock skew (ms)
            - event_sequence_gaps (int): number of sequence gaps in log

        Returns
        -------
        bool
            True if system is within boundary; False if any violation.
        """
        violations: list[str] = []

        # 1. Split-brain check
        if not self.allow_split_brain:
            # Read from nested layer state (drl / f2) where collect_state() puts them
            partition_count = (
                system_state.get("drl", {}).get("partitions", 0)
                or system_state.get("f2", {}).get("partitions", 0)
                or system_state.get("partitions", 0)
            )
            if partition_count > self.max_partitions:
                violations.append(
                    f"SPLIT_BRAIN: partitions={partition_count} "
                    f"(max={self.max_partitions})"
                )

        # 2. Quorum safety
        # Read from nested layer state where collect_state() places them
        quorum_ratio = (
            system_state.get("f2", {}).get("quorum_ratio", 0.0)
            or system_state.get("drl", {}).get("quorum_ratio", 0.0)
            or system_state.get("quorum_ratio", 0.0)
        )
        if quorum_ratio < self.quorum_threshold:
            violations.append(
                f"QUORUM_VIOLATION: ratio={quorum_ratio:.3f} "
                f"(required={self.quorum_threshold:.3f})"
            )

        # 3. Uncommitted read check
        uncommitted_reads = system_state.get("uncommitted_reads", 0)
        if uncommitted_reads > 0 and not self.allow_uncommitted_read:
            violations.append(
                f"UNCOMMITTED_READ: count={uncommitted_reads} "
                "(reads from uncommitted state are prohibited)"
            )

        # 4. Duplicate ACK / Byzantine signal
        if system_state.get("duplicate_ack", False) and not self.allow_duplicate_ack:
            violations.append("BYZANTINE_SIGNAL: duplicate ACK detected")

        # 5. Temporal drift
        if self.enable_temporal_strictness:
            clock_skew_ms = system_state.get("clock_skew_ms", 0.0)
            if clock_skew_ms > self.clock_skew_threshold_ms:
                violations.append(
                    f"TEMPORAL_DRIFT: skew={clock_skew_ms:.1f}ms "
                    f"(threshold={self.clock_skew_threshold_ms:.1f}ms)"
                )

        # 6. Event sequence integrity
        if not self.allow_event_reorder:
            gaps = system_state.get("event_sequence_gaps", 0)
            if gaps > 0:
                violations.append(
                    f"SEQUENCE_VIOLATION: gaps={gaps} "
                    "(reorder detected in event log)"
                )

        # Mutate frozen object's non-comparable field via object.__setattr__
        object.__setattr__(self, "_violations", tuple(violations))

        return len(violations) == 0

    def get_violations(self) -> tuple[str, ...]:
        """Return last recorded violations from validate()."""
        return self._violations
