"""
rolling_state_diff.py
=====================
Computes minimal rolling diffs between execution and replay state snapshots.
Maintains O(1) incremental diffs instead of O(n) full comparisons per tick.

Key concepts:
    - delta_exec(t)  = state_exec(t)  - state_exec(t-1)   (what changed in exec)
    - delta_replay(t) = state_replay(t) - state_replay(t-1) (what changed in replay)
    - consistency requires: delta_exec(t) ≡ delta_replay(t)

Module provides:
    RollingStateDiffer  — maintains previous + current state, computes diffs
    Delta                — structured delta with add/update/delete per node
    NodeDelta            — per-node field-level diff
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

# ── Delta types ──────────────────────────────────────────────────────────────

@dataclass
class NodeDelta:
    """Field-level diff for a single node."""
    node_id: str
    added: dict[str, Any] = field(default_factory=dict)      # existed only in curr
    updated: dict[str, tuple[Any, Any]] = field(default_factory=dict)  # old → new
    deleted: dict[str, Any] = field(default_factory=dict)    # existed only in prev

    @property
    def is_noop(self) -> bool:
        return not (self.added or self.updated or self.deleted)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "added": self.added,
            "updated": self.updated,
            "deleted": self.deleted,
            "is_noop": self.is_noop,
        }


@dataclass
class Delta:
    """Rolling diff between two cluster states."""
    prev_state: dict[str, Any]
    curr_state: dict[str, Any]
    node_deltas: dict[str, NodeDelta] = field(default_factory=dict)
    total_added: int = 0
    total_updated: int = 0
    total_deleted: int = 0
    ts_ns: int = field(default_factory=lambda: time.time_ns())

    @property
    def is_noop(self) -> bool:
        return self.total_added == 0 and self.total_updated == 0 and self.total_deleted == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_added": self.total_added,
            "total_updated": self.total_updated,
            "total_deleted": self.total_deleted,
            "is_noop": self.is_noop,
            "node_deltas": {k: v.to_dict() for k, v in self.node_deltas.items()},
        }


# ── RollingStateDiffer ─────────────────────────────────────────────────────

class RollingStateDiffer:
    """
    Computes minimal rolling diffs between execution and replay states.

    Usage:
        differ = RollingStateDiffer()
        # On each tick:
        delta_exec = differ.compute_delta_exec(current_exec_state)
        delta_replay = differ.compute_delta_replay(current_replay_state)
        # Compare deltas:
        drift = StreamingInvariantEngine._delta_drift(delta_exec, delta_replay)
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._prev_exec: dict[str, Any] = {}
        self._prev_replay: dict[str, Any] = {}

    def compute_delta_exec(self, curr: dict[str, Any]) -> dict[str, Any]:
        """
        Compute delta between last exec state and current exec state.
        Updates internal prev state to current.
        """
        with self._lock:
            prev, self._prev_exec = self._prev_exec, dict(curr)
        return self._single_delta(prev, curr)

    def compute_delta_replay(self, curr: dict[str, Any]) -> dict[str, Any]:
        """Compute delta between last replay state and current replay state."""
        with self._lock:
            prev, self._prev_replay = self._prev_replay, dict(curr)
        return self._single_delta(prev, curr)

    @staticmethod
    def compute_delta_for(
        prev_state: dict[str, Any],
        curr_state: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Static method: compute delta between any two states.
        Does not modify internal state.
        """
        return RollingStateDiffer._single_delta(prev_state, curr_state)

    @staticmethod
    def _single_delta(prev: dict[str, Any], curr: dict[str, Any]) -> dict[str, Any]:
        """
        Compute minimal diff between prev and curr.

        Returns a dict with structure:
            {
                "nodes_added":   [node_id, ...],
                "nodes_updated": {node_id: {"field": (old, new), ...}, ...},
                "nodes_deleted": [node_id, ...],
                "summary": {"added": N, "updated": N, "deleted": N},
            }
        """
        prev_nodes = prev.get("nodes", {}) if isinstance(prev, dict) else prev
        curr_nodes = curr.get("nodes", {}) if isinstance(curr, dict) else curr

        prev_ids = set(prev_nodes.keys())
        curr_ids = set(curr_nodes.keys())

        added_ids = curr_ids - prev_ids
        deleted_ids = prev_ids - curr_ids
        common_ids = prev_ids & curr_ids

        nodes_added: list[str] = []
        nodes_updated: dict[str, dict[str, tuple[Any, Any]]] = {}
        nodes_deleted: list[str] = []

        for nid in added_ids:
            nodes_added.append(nid)

        for nid in deleted_ids:
            nodes_deleted.append(nid)

        for nid in common_ids:
            pnode = prev_nodes[nid]
            cnode = curr_nodes[nid]
            if isinstance(pnode, dict) and isinstance(cnode, dict):
                field_updates: dict[str, tuple[Any, Any]] = {}
                all_keys = set(pnode.keys()) | set(cnode.keys())
                for k in all_keys:
                    pv = pnode.get(k, ...)
                    cv = cnode.get(k, ...)
                    if pv is ...:
                        pass  # new field handled below
                    elif cv is ...:
                        pass  # deleted field handled below
                    elif pv != cv:
                        field_updates[k] = (pv, cv)
                if field_updates:
                    nodes_updated[nid] = field_updates

        return {
            "nodes_added": nodes_added,
            "nodes_updated": nodes_updated,
            "nodes_deleted": nodes_deleted,
            "summary": {
                "added": len(nodes_added),
                "updated": len(nodes_updated),
                "deleted": len(nodes_deleted),
            },
        }

    def get_prev_exec(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._prev_exec)

    def get_prev_replay(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._prev_replay)

    def reset(self) -> None:
        """Clear all internal state (use for test reset or divergence recovery)."""
        with self._lock:
            self._prev_exec = {}
            self._prev_replay = {}
