"""
Formal Invariant Registry — I1, I2, ..., In.
Each invariant is a pure function: (decision_record) -> bool.
"""
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

from proof.proof_trace import DecisionRecord


class InvariantType(Enum):
    SAFETY = "safety"          # never violated (hard constraint)
    LIVENESS = "liveness"      # eventually holds (soft constraint)
    CONSISTENCY = "consistency"  # cross-layer coherence


@dataclass
class InvariantSpec:
    """Specification for a single formal invariant."""
    name: str
    type: InvariantType
    description: str
    check_fn: Callable[[DecisionRecord], bool]
    enabled: bool = True
    tags: list[str] = field(default_factory=list)


class InvariantRegistry:
    """
    Central registry for all formal invariants.

    Built-in invariants:
    - I1 (safety): Gain normalization total never exceeds max_global_gain
    - I2 (safety): Selected action priority ≥ all rejected priorities
    - I3 (safety): Pending count never negative
    - I4 (consistency): Winner source exists in submitted signals
    - I5 (liveness): Proof trace exists for every decision
    """

    def __init__(self) -> None:
        self._specs: dict[str, InvariantSpec] = {}
        self._enabled_set: set[str] = set()
        self._register_builtins()

    # ─── Built-in invariants ─────────────────────────────────────────────

    def _register_builtins(self) -> None:
        self.register(
            name="I1",
            inv_type=InvariantType.SAFETY,
            description="Total normalized gain ≤ max_global_gain",
            tags=["gain", "safety"],
            check_fn=lambda r: self._check_i1(r),
        )
        self.register(
            name="I2",
            inv_type=InvariantType.SAFETY,
            description="Winner priority ≥ all rejected priorities",
            tags=["priority", "safety"],
            check_fn=lambda r: self._check_i2(r),
        )
        self.register(
            name="I3",
            inv_type=InvariantType.SAFETY,
            description="Pending count ≥ 0",
            tags=["state", "safety"],
            check_fn=lambda r: self._check_i3(r),
        )
        self.register(
            name="I4",
            inv_type=InvariantType.CONSISTENCY,
            description="Winner source appears in submitted signals",
            tags=["consistency", "arbitration"],
            check_fn=lambda r: self._check_i4(r),
        )
        self.register(
            name="I5",
            inv_type=InvariantType.LIVENESS,
            description="Decision has proof trace DAG",
            tags=["proof", "liveness"],
            check_fn=lambda r: self._check_i5(r),
        )

    def _check_i1(self, record: DecisionRecord) -> bool:
        if record.gain_node is None:
            return True
        norm = record.gain_node.metadata.get("normalized", {})
        max_gain = record.input_state.get("_meta_max_global_gain", float("inf"))
        total = sum(abs(v) for v in norm.values())
        return total <= max_gain

    def _check_i2(self, record: DecisionRecord) -> bool:
        winner_priority = (
            record.selected_action.metadata.get("priority", 0.0)
            if record.selected_action else 0.0
        )
        return all(
            branch.priority <= winner_priority
            for branch in record.rejected_branches
        )

    def _check_i3(self, record: DecisionRecord) -> bool:
        pending = record.input_state.get("_meta_pending_count", 0)
        return pending >= 0

    def _check_i4(self, record: DecisionRecord) -> bool:
        if record.arbitration_node is None:
            return True
        arb_meta = record.arbitration_node.metadata
        winner = arb_meta.get("winner", "")
        all_sources = [
            c.metadata.get("source", "")
            for c in record.arbitration_node.children
        ]
        return winner in all_sources

    def _check_i5(self, record: DecisionRecord) -> bool:
        return (
            record.arbitration_node is not None
            or record.gain_node is not None
            or record.conflict_node is not None
        )

    # ─── Public API ───────────────────────────────────────────────────────

    def register(
        self,
        name: str,
        inv_type: InvariantType,
        description: str,
        check_fn: Callable[[DecisionRecord], bool],
        tags: list[str] | None = None,
    ) -> None:
        spec = InvariantSpec(
            name=name,
            type=inv_type,
            description=description,
            check_fn=check_fn,
            tags=tags or [],
        )
        self._specs[name] = spec
        self._enabled_set.add(name)

    def unregister(self, name: str) -> None:
        self._specs.pop(name, None)
        self._enabled_set.discard(name)

    def check(self, record: DecisionRecord) -> dict[str, bool]:
        """Run all enabled invariants against a DecisionRecord."""
        results: dict[str, bool] = {}
        for name in self._enabled_set:
            spec = self._specs[name]
            try:
                results[name] = spec.check_fn(record)
            except Exception:
                results[name] = False
        return results

    def check_with_details(
        self,
        record: DecisionRecord,
    ) -> list[dict[str, object]]:
        """Return per-invariant results with full metadata."""
        results: list[dict[str, object]] = []
        for name in self._enabled_set:
            spec = self._specs[name]
            try:
                passed = spec.check_fn(record)
            except Exception:
                passed = False
            results.append({
                "name": name,
                "type": spec.type.value,
                "description": spec.description,
                "passed": passed,
                "tags": spec.tags,
            })
        return results

    def list_all(self) -> list[dict[str, str]]:
        return [
            {
                "name": name,
                "type": spec.type.value,
                "description": spec.description,
                "enabled": name in self._enabled_set,
                "tags": spec.tags,
            }
            for name, spec in self._specs.items()
        ]

    def enable(self, name: str) -> None:
        self._enabled_set.add(name)

    def disable(self, name: str) -> None:
        self._enabled_set.discard(name)

    @property
    def enabled_count(self) -> int:
        return len(self._enabled_set)
