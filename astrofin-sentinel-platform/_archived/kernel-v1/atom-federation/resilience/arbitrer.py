"""
GlobalControlArbiter v6.5 — Conflict resolution across all subsystems.

Problem:
  PolicyEngine, Healer, AdaptiveRouter, and StabilityMetricsEngine are
  independent decision engines. They can issue conflicting directives:
    - PolicyEngine says EVICT_NODE → Healer hasn't finished RESTORE_NODE
    - PolicyEngine says RESTORE_NODE → AdaptiveRouter already removed peer
    - MetricsEngine says score<0.3 → PolicyEngine says RESTORE_NODE (conflict)

Solution:
  GlobalControlArbiter is the SINGLE arbitration point for all decisions.
  All subsystems submit their desired actions; the arbiter produces a
  single, deterministic, conflict-free ActionVector.

Usage:
    arbiter = GlobalControlArbiter()
    decision = arbiter.arbitrate(
        policy_decision=PolicyAction.EVICT_NODE,
        healer_busy=True,
        healer_pending=[HealingAction.RESTORE_NODE],
        healer_evicted={"node-b"},
        router_violating={"node-b"},
        stability_score=0.25,
        sbs_violations=[{"type": "CRITICAL", "node": "node-b"}],
        partition_active=False,
        consecutive_failures={"node-b": 5},
        clock_skew_ms=200.0,
        node_recovered=None,
    )
    # decision.action is the resolved PolicyAction
    # decision.conflicts lists any conflicts detected
    # decision.resolution_reason explains the resolution
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto

from resilience.healer import HealingAction
from resilience.policy_engine import PolicyAction

__all__ = ["ArbitrationDecision", "ConflictType", "GlobalControlArbiter"]


# ── Priority lattice ──────────────────────────────────────────────────────────
# Higher priority = wins in conflict

class Priority(Enum):
    BYZANTINE             = 1000
    QUORUM_LOST           = 900
    SBS_CRITICAL          = 850
    PARTITION_ACTIVE      = 800
    NODE_EVICTED          = 700
    CONSECUTIVE_FAILURES  = 600
    STABILITY_CRITICAL    = 550
    STABILITY_LOW         = 500
    NODE_RECOVERED        = 400
    SLO_VIOLATION         = 300
    OBSERVATION           = 100
    NOOP                  = 0


class ConflictType(Enum):
    NONE                  = auto()
    POLICY_VS_HEALER      = auto()
    POLICY_VS_ROUTER      = auto()
    HEALER_VS_ROUTER      = auto()
    ROUTER_VS_SBS         = auto()
    STABILITY_CONFLICT    = auto()
    EVICT_RESTORE_FLAP    = auto()
    MULTIPLE_LEADERS      = auto()


@dataclass
class ArbitrationDecision:
    action: PolicyAction
    target: str | None
    healing_action: HealingAction | None
    confidence: float           # 0.0 → 1.0
    conflicts: list[ConflictType]
    resolution_reason: str
    priority_used: int
    stability_context: str      # "critical" | "degraded" | "healthy"
    tick_ts: float = field(default_factory=time.monotonic)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    @property
    def is_safe_to_act(self) -> bool:
        return (
            self.confidence >= 0.7
            and ConflictType.QUORUM_LOST not in self.conflicts
            and ConflictType.MULTIPLE_LEADERS not in self.conflicts
            and ConflictType.EVICT_RESTORE_FLAP not in self.conflicts
        )

    def to_dict(self) -> dict:
        return {
            "action": self.action.name,
            "target": self.target,
            "healing_action": (self.healing_action.name if self.healing_action else None),
            "confidence": round(self.confidence, 3),
            "conflicts": [c.name for c in self.conflicts],
            "resolution_reason": self.resolution_reason,
            "priority_used": self.priority_used,
            "stability_context": self.stability_context,
            "is_safe_to_act": self.is_safe_to_act,
        }


# ── Anti-flapping tracker ─────────────────────────────────────────────────────

class FlappingTracker:
    MAX_FLAPS: int = 2
    WINDOW_S: float = 60.0

    def __init__(self) -> None:
        self._state: dict[str, list[float]] = {}

    def record(self, node_id: str, action: str) -> bool:
        now = time.monotonic()
        if node_id not in self._state:
            self._state[node_id] = []
        cutoff = now - self.WINDOW_S
        self._state[node_id] = [t for t in self._state[node_id] if t > cutoff]
        self._state[node_id].append(now)
        return len(self._state[node_id]) <= self.MAX_FLAPS

    def is_flapping(self, node_id: str) -> bool:
        if node_id not in self._state:
            return False
        cutoff = time.monotonic() - self.WINDOW_S
        return len([t for t in self._state[node_id] if t > cutoff]) > self.MAX_FLAPS

    def clear(self, node_id: str) -> None:
        self._state.pop(node_id, None)


# ── GlobalControlArbiter ──────────────────────────────────────────────────────

class GlobalControlArbiter:
    """
    Single arbitration point for all resilience subsystem decisions.

    Arbitration: collect → detect conflicts → priority lattice → anti-flapping → emit
    """

    STABILITY_CRITICAL_THRESHOLD = 0.30
    STABILITY_LOW_THRESHOLD = 0.70

    def __init__(self) -> None:
        self._flapping = FlappingTracker()
        self._log: list[dict] = []

    def arbitrate(
        self,
        policy_decision: PolicyAction,
        healer_busy: bool,
        healer_pending: list[HealingAction],
        healer_evicted: set[str],
        router_violating: set[str],
        stability_score: float,
        sbs_violations: list[dict],
        partition_active: bool,
        consecutive_failures: dict[str, int],
        clock_skew_ms: float,
        node_recovered: str | None,
        router_excluded: set[str] | None = None,
        leader_uniqueness_violated: bool = False,
        quorum_lost: bool = False,
    ) -> ArbitrationDecision:
        router_excluded = router_excluded or set()
        conflicts: list[ConflictType] = []
        reason_parts: list[str] = []
        stability_ctx = self._stability_context(stability_score)

        has_critical_sbs = any(v.get("type") == "CRITICAL" for v in sbs_violations)
        critical_sbs_nodes = {v.get("node") for v in sbs_violations if v.get("type") == "CRITICAL" and v.get("node")}
        byzantine_nodes = {v.get("node") for v in sbs_violations if v.get("type") == "BYZANTINE" and v.get("node")}

        # Priority cascade
        action: PolicyAction = policy_decision
        healing_action: HealingAction | None = None
        target: str | None = None
        priority_used: int = Priority.NOOP.value
        confidence: float = 0.5

        # BYZANTINE — preemptive
        if byzantine_nodes:
            node = next(iter(byzantine_nodes))
            action, healing_action, target = PolicyAction.ISOLATE_BYZANTINE, HealingAction.ISOLATE_BYZANTINE, node
            priority_used, confidence = Priority.BYZANTINE.value, 1.0
            reason_parts.append(f"BYZANTINE node {node} — preemptive isolation")

        # QUORUM_LOST
        elif quorum_lost:
            action, priority_used, confidence = PolicyAction.ALERT_OPS, Priority.QUORUM_LOST.value, 1.0
            reason_parts.append("QUORUM_LOST — alerting ops")

        # SPLIT_BRAIN
        elif leader_uniqueness_violated:
            action, healing_action = PolicyAction.TRIGGER_RE_ELECTION, HealingAction.TRIGGER_RE_ELECTION
            priority_used, confidence = Priority.MULTIPLE_LEADERS.value, 1.0
            reason_parts.append("SPLIT_BRAIN detected — triggering re-election")

        # CRITICAL SBS
        elif has_critical_sbs:
            node = next(iter(critical_sbs_nodes))
            if node in healer_evicted:
                conflicts.append(ConflictType.POLICY_VS_HEALER)
                action, priority_used = PolicyAction.NOOP, Priority.NODE_EVICTED.value
                reason_parts.append(f"Node {node} already evicted; skipping duplicate EVICT")
            elif self._flapping.is_flapping(node):
                conflicts.append(ConflictType.EVICT_RESTORE_FLAP)
                action, priority_used, confidence = PolicyAction.LOG_ONLY, Priority.STABLE.value, 0.3
                reason_parts.append(f"Node {node} is flapping — deferring EVICT")
            else:
                action, healing_action, target = PolicyAction.EVICT_NODE, HealingAction.EVICT_NODE, node
                priority_used, confidence = Priority.SBS_CRITICAL.value, 0.95
                reason_parts.append(f"SBS_CRITICAL on {node} — evicting")
                self._flapping.record(node, "EVICT")

        # PARTITION
        elif partition_active:
            action, healing_action = PolicyAction.TRIGGER_SELF_HEAL, HealingAction.RECONFIGURE_QUORUM
            priority_used, confidence = Priority.PARTITION_ACTIVE.value, 0.9
            reason_parts.append("PARTITION active — triggering self-heal")

        # STABILITY CRITICAL
        elif stability_score < self.STABILITY_CRITICAL_THRESHOLD:
            action, priority_used, confidence = PolicyAction.ALERT_OPS, Priority.STABILITY_CRITICAL.value, 0.9
            reason_parts.append(f"Stability {stability_score:.2f} < {self.STABILITY_CRITICAL_THRESHOLD} — alerting")

        # NODE RECOVERED
        elif node_recovered is not None:
            if node_recovered in healer_evicted and not healer_busy:
                action, healing_action, target = PolicyAction.RESTORE_NODE, HealingAction.RESTORE_NODE, node_recovered
                priority_used, confidence = Priority.NODE_RECOVERED.value, 0.95
                reason_parts.append(f"Node {node_recovered} recovered — restoring")
                self._flapping.record(node_recovered, "RESTORE")
            elif node_recovered in router_violating or node_recovered in router_excluded:
                conflicts.append(ConflictType.HEALER_VS_ROUTER)
                action, priority_used, confidence = PolicyAction.NOOP, Priority.SLO_VIOLATION.value, 0.5
                reason_parts.append(f"Node {node_recovered} recovered but still excluded — waiting")
            else:
                action, healing_action, target = PolicyAction.RECONFIGURE_QUORUM, HealingAction.RECONFIGURE_QUORUM, node_recovered
                priority_used, confidence = Priority.NODE_RECOVERED.value, 0.8
                reason_parts.append(f"Node {node_recovered} recovered — reconfiguring quorum")

        # POLICY_VS_HEALER conflict
        elif healer_busy and healer_pending:
            active = healer_pending[0]
            if active in (HealingAction.RESTORE_NODE, HealingAction.RECONFIGURE_QUORUM):
                if policy_decision in (PolicyAction.EVICT_NODE, PolicyAction.ISOLATE_BYZANTINE):
                    conflicts.append(ConflictType.POLICY_VS_HEALER)
                    action, priority_used, confidence = PolicyAction.LOG_ONLY, Priority.NODE_RECOVERED.value, 0.4
                    reason_parts.append(f"Policy wants {policy_decision.name} but Healer busy with {active.name}")

        # CLOCK SKEW
        elif clock_skew_ms > 5000.0:
            action, priority_used, confidence = PolicyAction.ALERT_OPS, Priority.SLO_VIOLATION.value, 0.8
            reason_parts.append(f"Clock skew {clock_skew_ms:.0f}ms > 5000ms — alerting")

        # Default
        else:
            action, priority_used, confidence = policy_decision, Priority.OBSERVATION.value, 0.6
            reason_parts.append(f"Default: policy decision {policy_decision.name}")

        # Post-process router conflicts
        if router_violating and target and target in router_violating:
            conflicts.append(ConflictType.POLICY_VS_ROUTER)

        resolution_reason = "; ".join(reason_parts) if reason_parts else "No action needed"

        decision = ArbitrationDecision(
            action=action, target=target, healing_action=healing_action,
            confidence=confidence, conflicts=conflicts,
            resolution_reason=resolution_reason, priority_used=priority_used,
            stability_context=stability_ctx,
        )
        self._log.append({
            "ts": time.monotonic(), "policy_decision": policy_decision.name,
            "decision": decision.to_dict(),
        })
        return decision

    def _stability_context(self, score: float) -> str:
        if score < self.STABILITY_CRITICAL_THRESHOLD:
            return "critical"
        elif score < self.STABILITY_LOW_THRESHOLD:
            return "degraded"
        return "healthy"

    def get_log(self, last_n: int | None = None) -> list[dict]:
        log = list(reversed(self._log))
        return log[:last_n] if last_n else log

    def dump(self) -> dict:
        return {
            "log_count": len(self._log),
            "flapping_nodes": list(self._flapping._state.keys()),
        }
