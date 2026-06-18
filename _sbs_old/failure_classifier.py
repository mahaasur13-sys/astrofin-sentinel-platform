"""
FailureClassifier — converts DRL failure events into SBS-level semantic categories.

Provides a strict taxonomy aligned with Jepsen fault model:
- NETWORK_PARTITION
- MESSAGE_LOSS
- BYZANTINE_BEHAVIOR
- TEMPORAL_DRIFT
- CONSENSUS_BREAK
- STATE_CORRUPTION
- QUORUM_VIOLATION

Each category maps to a Severity and recommended action.
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Any


class FailureCategory(Enum):
    """SBS-level failure taxonomy (Jepsen-aligned)."""

    NETWORK_PARTITION = "NETWORK_PARTITION"
    MESSAGE_LOSS = "MESSAGE_LOSS"
    DUPLICATE_MESSAGE = "DUPLICATE_MESSAGE"
    BYZANTINE_BEHAVIOR = "BYZANTINE_BEHAVIOR"
    TEMPORAL_DRIFT = "TEMPORAL_DRIFT"
    CONSENSUS_BREAK = "CONSENSUS_BREAK"
    STATE_CORRUPTION = "STATE_CORRUPTION"
    QUORUM_VIOLATION = "QUORUM_VIOLATION"
    LEADERSHIP_SPLIT = "LEADERSHIP_SPLIT"
    SEQUENCE_VIOLATION = "SEQUENCE_VIOLATION"
    UNKNOWN_FAILURE = "UNKNOWN_FAILURE"


class FailureSeverity(Enum):
    """Impact severity of a classified failure."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass(frozen=True)
class ClassifiedFailure:
    """Immutable result of failure classification."""

    category: FailureCategory
    severity: FailureSeverity
    description: str
    source_layer: str
    raw_event: dict[str, Any]

    def __str__(self) -> str:
        return (
            f"[{self.severity.value}] {self.category.value} "
            f"(from {self.source_layer}): {self.description}"
        )


# ── Severity matrix: category → default severity ────────────────────────────
_FAILURE_SEVERITY_MAP: dict[FailureCategory, FailureSeverity] = {
    FailureCategory.BYZANTINE_BEHAVIOR: FailureSeverity.CRITICAL,
    FailureCategory.STATE_CORRUPTION: FailureSeverity.CRITICAL,
    FailureCategory.CONSENSUS_BREAK: FailureSeverity.CRITICAL,
    FailureCategory.LEADERSHIP_SPLIT: FailureSeverity.CRITICAL,
    FailureCategory.QUORUM_VIOLATION: FailureSeverity.HIGH,
    FailureCategory.NETWORK_PARTITION: FailureSeverity.HIGH,
    FailureCategory.TEMPORAL_DRIFT: FailureSeverity.MEDIUM,
    FailureCategory.MESSAGE_LOSS: FailureSeverity.MEDIUM,
    FailureCategory.DUPLICATE_MESSAGE: FailureSeverity.LOW,
    FailureCategory.SEQUENCE_VIOLATION: FailureSeverity.MEDIUM,
    FailureCategory.UNKNOWN_FAILURE: FailureSeverity.HIGH,
}


class FailureClassifier:
    """
    Converts raw DRL/CCL/F2 failure events into SBS-level semantic categories.

    Maps from implementation-specific failure types to SBS taxonomy.
    """

    def classify(self, failure_event: dict[str, Any]) -> ClassifiedFailure:
        """
        Classify a single failure event.

        Parameters
        ----------
        failure_event : dict
            Raw failure event with at minimum:
            - type (str): failure type string
            - layer (str): source layer (DRL/CCL/F2/DESC)
            - description (str): human-readable description

        Returns
        -------
        ClassifiedFailure
            Immutable classified failure with category + severity.
        """
        raw_type = failure_event.get("type", "unknown")
        layer = failure_event.get("layer", "UNKNOWN")
        description = failure_event.get("description", str(failure_event))

        category = self._map_type_to_category(raw_type)
        severity = _FAILURE_SEVERITY_MAP.get(category, FailureSeverity.HIGH)

        return ClassifiedFailure(
            category=category,
            severity=severity,
            description=description,
            source_layer=layer,
            raw_event=failure_event,
        )

    def classify_batch(
        self, failure_events: list[dict[str, Any]]
    ) -> list[ClassifiedFailure]:
        """Classify multiple failure events."""
        return [self.classify(e) for e in failure_events]

    def _map_type_to_category(self, raw_type: str) -> FailureCategory:
        """Map implementation-specific type string to FailureCategory."""
        type_map: dict[str, FailureCategory] = {
            # Network
            "partition": FailureCategory.NETWORK_PARTITION,
            "net_partition": FailureCategory.NETWORK_PARTITION,
            "split_brain": FailureCategory.NETWORK_PARTITION,
            # Message
            "drop": FailureCategory.MESSAGE_LOSS,
            "msg_drop": FailureCategory.MESSAGE_LOSS,
            "timeout": FailureCategory.MESSAGE_LOSS,
            "duplicate": FailureCategory.DUPLICATE_MESSAGE,
            "dup_ack": FailureCategory.DUPLICATE_MESSAGE,
            "replay": FailureCategory.DUPLICATE_MESSAGE,
            # Byzantine
            "byzantine": FailureCategory.BYZANTINE_BEHAVIOR,
            "equivocate": FailureCategory.BYZANTINE_BEHAVIOR,
            "fork": FailureCategory.BYZANTINE_BEHAVIOR,
            # Temporal
            "clock_skew": FailureCategory.TEMPORAL_DRIFT,
            "clock_drift": FailureCategory.TEMPORAL_DRIFT,
            "temporal_drift": FailureCategory.TEMPORAL_DRIFT,
            # Consensus
            "consensus_violation": FailureCategory.CONSENSUS_BREAK,
            "term_mismatch": FailureCategory.CONSENSUS_BREAK,
            "vote_violation": FailureCategory.CONSENSUS_BREAK,
            # State
            "state_corruption": FailureCategory.STATE_CORRUPTION,
            "memory_corruption": FailureCategory.STATE_CORRUPTION,
            "checksum_fail": FailureCategory.STATE_CORRUPTION,
            # Quorum
            "quorum_violation": FailureCategory.QUORUM_VIOLATION,
            "quorum_split": FailureCategory.QUORUM_VIOLATION,
            "insufficient_votes": FailureCategory.QUORUM_VIOLATION,
            # Leadership
            "leadership_split": FailureCategory.LEADERSHIP_SPLIT,
            "multiple_leaders": FailureCategory.LEADERSHIP_SPLIT,
            "no_leader": FailureCategory.LEADERSHIP_SPLIT,
            # Sequence
            "sequence_violation": FailureCategory.SEQUENCE_VIOLATION,
            "event_reorder": FailureCategory.SEQUENCE_VIOLATION,
            "gap_detected": FailureCategory.SEQUENCE_VIOLATION,
        }
        return type_map.get(raw_type.lower(), FailureCategory.UNKNOWN_FAILURE)

    def get_severity_for(self, category: FailureCategory) -> FailureSeverity:
        """Return default severity for a failure category."""
        return _FAILURE_SEVERITY_MAP.get(category, FailureSeverity.HIGH)
