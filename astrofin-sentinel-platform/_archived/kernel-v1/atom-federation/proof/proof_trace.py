"""
Proof Trace DAG — decision record with rejected branches.
Each decision = directed acyclic graph:
  state → arbitration → gain normalization → conflict resolution → action
  ↘ rejected branches (with reason and dominance proof)
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeType(Enum):
    INPUT_STATE = "input_state"
    ARBITRATION = "arbitration"
    GAIN_NORMALIZATION = "gain_normalization"
    CONFLICT_RESOLUTION = "conflict_resolution"
    ACTION = "action"
    REJECTED = "rejected_branch"


class DominanceResult(Enum):
    STRICTLY_DOMINATES = "strictly_dominates"
    EQUIVALENT = "equivalent"
    INCOMPARABLE = "incomparable"


@dataclass
class ProofNode:
    node_type: NodeType
    label: str
    metadata: dict[str, Any] = field(default_factory=dict)
    children: list["ProofNode"] = field(default_factory=list)
    proof_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_type": self.node_type.value,
            "label": self.label,
            "metadata": self.metadata,
            "children": [c.to_dict() for c in self.children],
            "proof_id": self.proof_id,
        }


@dataclass
class RejectedBranch:
    source: str
    reason: str
    dominance: DominanceResult
    priority: float
    selected_priority: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "reason": self.reason,
            "dominance": self.dominance.value,
            "priority": self.priority,
            "selected_priority": self.selected_priority,
        }


@dataclass
class DecisionRecord:
    """
    Complete record of a single decision with full proof trace DAG.

    Attributes:
        decision_id: unique identifier (UUID)
        timestamp: epoch seconds
        input_state: snapshot of system state at decision time
        arbitration_node: ProofNode from ControlArbitrator.resolve()
        gain_node: ProofNode from SystemWideGainScheduler
        conflict_node: ProofNode from ConflictResolutionMatrix
        selected_action: winning action node
        rejected_branches: list of rejected alternatives with reasons
        proof_status: PASS / FAIL / INCONCLUSIVE
        validity_score: float in [0.0, 1.0]
        invariants_checked: list of invariant names that passed
    """
    decision_id: str
    timestamp: float
    input_state: dict[str, Any]
    arbitration_node: ProofNode | None = None
    gain_node: ProofNode | None = None
    conflict_node: ProofNode | None = None
    selected_action: ProofNode | None = None
    rejected_branches: list[RejectedBranch] = field(default_factory=list)
    proof_status: str = "PASS"
    validity_score: float = 1.0
    invariants_checked: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "timestamp": self.timestamp,
            "input_state": self.input_state,
            "arbitration_node": self.arbitration_node.to_dict() if self.arbitration_node else None,
            "gain_node": self.gain_node.to_dict() if self.gain_node else None,
            "conflict_node": self.conflict_node.to_dict() if self.conflict_node else None,
            "selected_action": self.selected_action.to_dict() if self.selected_action else None,
            "rejected_branches": [b.to_dict() for b in self.rejected_branches],
            "proof_status": self.proof_status,
            "validity_score": self.validity_score,
            "invariants_checked": self.invariants_checked,
        }

    def add_rejected(self, branch: RejectedBranch) -> None:
        self.rejected_branches.append(branch)


class ProofTrace:
    """
    DAG builder and exporter for decision proof traces.

    Usage:
        trace = ProofTrace()
        record = DecisionRecord(...)
        trace.add_stage(record, "arbitration", {"winner": "drl", "all_submitted": ["drl", "sbs"]})
        trace.add_rejected(record, RejectedBranch(...))
        trace.finalize(record)
        dag = trace.export_dag(record)
    """

    def __init__(self) -> None:
        self._next_id: int = 0

    def _make_node(
        self,
        node_type: NodeType,
        label: str,
        metadata: dict[str, Any] | None = None,
    ) -> ProofNode:
        node_id = f"proof_{self._next_id}"
        self._next_id += 1
        return ProofNode(
            node_type=node_type,
            label=label,
            metadata=metadata or {},
            proof_id=node_id,
        )

    def build_input_state(self, state_snapshot: dict[str, Any]) -> ProofNode:
        """Root node: the input state at decision time."""
        return self._make_node(NodeType.INPUT_STATE, "input_state", state_snapshot)

    def add_arbiter_stage(
        self,
        record: DecisionRecord,
        winner_source: str,
        winner_priority: float,
        all_submitted: list[dict[str, Any]],
    ) -> None:
        """Attach arbitration DAG segment."""
        arb_node = self._make_node(
            NodeType.ARBITRATION,
            f"arbitration:winner={winner_source}",
            {"winner": winner_source, "winner_priority": winner_priority},
        )
        for sig in all_submitted:
            src = sig.get("source", "?")
            is_winner = src == winner_source
            child_label = f"submitted:{src}"
            child_meta = {**sig, "winner": is_winner}
            child_node = self._make_node(
                NodeType.REJECTED if not is_winner else NodeType.ARBITRATION,
                child_label,
                child_meta,
            )
            arb_node.children.append(child_node)

        record.arbitration_node = arb_node

    def add_gain_stage(
        self,
        record: DecisionRecord,
        normalized_gains: dict[str, float],
        raw_gains: dict[str, float] | None = None,
    ) -> None:
        """Attach gain normalization DAG segment.

        The action node (which will be appended by finalize) is placed at
        children[0]; per-source gain sub-nodes follow at children[1:].
        This keeps the chain-link (action) accessible at children[0].
        """
        gain_node = self._make_node(
            NodeType.GAIN_NORMALIZATION,
            "gain_normalization",
            {"normalized": normalized_gains, "raw": raw_gains or {}},
        )
        # Action node (finalize chain) goes at children[0]
        # per-source gain entries follow at children[1:]
        record.gain_node = gain_node

    def add_conflict_stage(
        self,
        record: DecisionRecord,
        winner: str,
        candidates: list[str],
        matrix_entries: dict[tuple, float],
    ) -> None:
        """Attach conflict resolution DAG segment."""
        conflict_node = self._make_node(
            NodeType.CONFLICT_RESOLUTION,
            f"conflict_resolution:winner={winner}",
            {"winner": winner, "candidates": candidates},
        )
        for c in candidates:
            is_winner = c == winner
            child_meta = {
                "candidate": c,
                "winner": is_winner,
                "pairwise_vs_winner": matrix_entries.get((c, winner), 0.0),
            }
            child_node = self._make_node(
                NodeType.REJECTED if not is_winner else NodeType.CONFLICT_RESOLUTION,
                f"candidate:{c}",
                child_meta,
            )
            conflict_node.children.append(child_node)
        record.conflict_node = conflict_node

    def set_action(
        self,
        record: DecisionRecord,
        action_source: str,
        action_payload: dict[str, Any],
    ) -> None:
        """Set the final action node."""
        action_node = self._make_node(
            NodeType.ACTION,
            f"action:{action_source}",
            action_payload,
        )
        record.selected_action = action_node

    def add_rejected(
        self,
        record: DecisionRecord,
        source: str,
        reason: str,
        dominance: DominanceResult,
        priority: float,
        selected_priority: float,
    ) -> None:
        """Append a rejected branch to the record."""
        branch = RejectedBranch(
            source=source,
            reason=reason,
            dominance=dominance,
            priority=priority,
            selected_priority=selected_priority,
        )
        record.add_rejected(branch)

    def finalize(self, record: DecisionRecord) -> None:
        """Build DAG edges between stages (input → arbitration → gain → conflict → action).
        Stages are chained sequentially; signal-submitted children are preserved.
        """
        # Chain: arb_children + [gain_node] + [conflict_node] + [action_node]
        # where only the chain links are appended (no re-setting existing children).
        chain = list(filter(None, [
            record.arbitration_node,
            record.gain_node,
            record.conflict_node,
            record.selected_action,
        ]))
        for i in range(len(chain) - 1):
            # Prepend next node as final child; existing children (signal entries) kept
            chain[i].children.insert(0, chain[i + 1])

    def export_dag(self, record: DecisionRecord) -> dict[str, Any]:
        """Export full DAG as dict for serialization / visualization."""
        return record.to_dict()
