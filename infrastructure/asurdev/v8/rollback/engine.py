#!/usr/bin/env python3
from enum import Enum
"""
Rollback Engine — state snapshot + restore.
Levels: L1 (policy revert) / L2 (optimizer reset) / L3 (full cluster state).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Callable
import copy


class RollbackLevel(Enum):
    L1 = "L1"   # policy revert
    L2 = "L2"   # optimizer reset
    L3 = "L3"   # full cluster state rollback


TRIGGERS = {
    "latency_spike",
    "failure_rate_jump",
    "constraint_violation",
    "drift_anomaly",
    "safety_kernel_reject",
    "manual_trigger",
}


@dataclass
class RollbackEvent:
    timestamp: datetime
    trigger: str
    level: RollbackLevel
    snapshot_id: str
    affected_nodes: list[str]
    pre_state_hash: str
    post_state_hash: str
    restored: bool = False


@dataclass
class ClusterSnapshot:
    snapshot_id: str
    timestamp: datetime
    cluster_state: dict
    policy_state: dict
    optimizer_state: dict
    state_hash: str


class RollbackEngine:
    """
    3-level rollback with snapshot persistence.
    
    Snapshot triggers:
        - Periodic: every N good cycles
        - Pre-decision: before major optimization
        - On incident: before recovery action
    
    Restore flow:
        1. load snapshot from state store
        2. apply to cluster
        3. verify restoration
    """

    def __init__(self, state_store, cluster_api: Callable):
        self.state_store = state_store
        self.cluster_api = cluster_api
        self._snapshots: list[ClusterSnapshot] = []
        self._events: list[RollbackEvent] = []
        self._last_good: Optional[ClusterSnapshot] = None
        self._rollback_handlers: dict[RollbackLevel, list[Callable]] = {
            RollbackLevel.L1: [],
            RollbackLevel.L2: [],
            RollbackLevel.L3: [],
        }

    def snapshot(self, label: str = "periodic") -> ClusterSnapshot:
        """Create a point-in-time snapshot."""
        state = self.cluster_api.get_full_state()
        snap = ClusterSnapshot(
            snapshot_id=f"snap_{datetime.utcnow().isoformat()}_{label}",
            timestamp=datetime.utcnow(),
            cluster_state=copy.deepcopy(state["cluster"]),
            policy_state=copy.deepcopy(state["policy"]),
            optimizer_state=copy.deepcopy(state["optimizer"]),
            state_hash=self._hash_state(state),
        )
        self._snapshots.append(snap)
        self._last_good = snap
        # Persist to state store
        self.state_store.save_snapshot(snap)
        return snap

    def rollback(self, event_trigger: str, level: RollbackLevel) -> RollbackEvent:
        """
        Execute rollback to last good state.
        Returns RollbackEvent with details.
        """
        if not self._last_good:
            raise RuntimeError("No snapshot available for rollback")

        target = self._last_good

        # STEP 1: capture post-incident state
        current = self.cluster_api.get_full_state()
        post_hash = self._hash_state(current)

        # STEP 2: build event
        rb_event = RollbackEvent(
            timestamp=datetime.utcnow(),
            trigger=event_trigger,
            level=level,
            snapshot_id=target.snapshot_id,
            affected_nodes=self._affected_nodes(level, target),
            pre_state_hash=target.state_hash,
            post_state_hash=post_hash,
        )

        # STEP 3: run level-specific handlers
        for handler in self._rollback_handlers[level]:
            handler(target)

        # STEP 4: restore cluster state
        self.cluster_api.restore_state(target.cluster_state)

        # STEP 5: verify
        restored_state = self.cluster_api.get_full_state()
        restored_hash = self._hash_state(restored_state)
        rb_event.restored = (restored_hash == target.state_hash)

        self._events.append(rb_event)
        return rb_event

    def rollback_l1(self, event_trigger: str) -> RollbackEvent:
        """L1: revert to previous policy version."""
        return self.rollback(event_trigger, RollbackLevel.L1)

    def rollback_l2(self, event_trigger: str) -> RollbackEvent:
        """L2: reset optimizer to last known good."""
        return self.rollback(event_trigger, RollbackLevel.L2)

    def rollback_l3(self, event_trigger: str) -> RollbackEvent:
        """L3: full cluster state restoration."""
        return self.rollback(event_trigger, RollbackLevel.L3)

    def register_handler(self, level: RollbackLevel, handler: Callable) -> None:
        self._rollback_handlers[level].append(handler)

    def get_last_good_snapshot(self) -> Optional[ClusterSnapshot]:
        return self._last_good

    def get_events(self) -> list[RollbackEvent]:
        return self._events

    def _affected_nodes(self, level: RollbackLevel, snap: ClusterSnapshot) -> list[str]:
        if level == RollbackLevel.L3:
            return list(snap.cluster_state.get("nodes", {}).keys())
        elif level == RollbackLevel.L2:
            return list(snap.optimizer_state.get("affected_nodes", []))
        return list(snap.policy_state.get("affected_policies", []))

    def _hash_state(self, state: dict) -> str:
        import hashlib, json
        s = json.dumps(state, sort_keys=True)
        return hashlib.sha256(s.encode()).hexdigest()[:16]
