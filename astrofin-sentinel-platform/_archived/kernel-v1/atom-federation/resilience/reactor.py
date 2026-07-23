"""
Reactor v6.4 — Event-driven reaction engine.

Maps SBS/chaos events from ClusterNode health graph and SBS enforcer
into ResilienceReactor events, dispatches to PolicyEngine, executes actions.

Usage:
    reactor = ResilienceReactor(node_id="node-a", peers=["node-b", "node-c"])
    reactor.on_sbs_violation(violations=[...])
    reactor.on_node_unreachable("node-b", consecutive=3)
    reactor.on_partition_detected(partitioned_nodes=["node-a", "node-b"])
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto

from resilience.policy_engine import PolicyAction, PolicyEngine, ReactionTrigger

__all__ = ["ReactionAction", "ReactionTrigger", "ResilienceReactor"]


class ReactionAction:
    """
    Concrete action payload produced by ResilienceReactor.
    Carries everything the executor (healer, router, etc.) needs.
    """
    def __init__(
        self,
        action: PolicyAction,
        target: str | None = None,
        reason: str = "",
        metadata: dict | None = None,
    ) -> None:
        self.action = action
        self.target = target  # node_id or None
        self.reason = reason
        self.metadata = metadata or {}
        self.ts = time.monotonic()

    def __repr__(self) -> str:
        return (
            f"ReactionAction({self.action.name}"
            + (f", target={self.target}" if self.target else "")
            + f", reason={self.reason!r})"
        )


# ── Internal event types ────────────────────────────────────────────────────────

class _EventType(Enum):
    SBS_VIOLATION = auto()
    NODE_UNREACHABLE = auto()
    NODE_RECOVERED = auto()
    PARTITION = auto()
    BYZANTINE = auto()
    QUORUM_CHANGE = auto()
    DRL_SLO = auto()
    STABILITY = auto()


@dataclass
class _ReactorEvent:
    event_type: _EventType
    trigger: ReactionTrigger
    context: dict
    raw: dict  # original data for debugging


# ── ResilienceReactor ─────────────────────────────────────────────────────────

class ResilienceReactor:
    """
    Event-driven reaction engine.

    Subscribes to signals from:
      - ClusterNode health graph (node up/down)
      - SBS enforcer (invariant violations)
      - chaos harness (partition detected/healed)
      - DRL bridge (latency/loss SLOs)
      - stability metrics engine

    For each event, queries PolicyEngine and emits a ReactionAction.

    Callbacks can be registered for each PolicyAction so the rest of the
    system (healer, router) can react.
    """

    def __init__(
        self,
        node_id: str,
        peers: list[str],
        policy_engine: PolicyEngine | None = None,
    ) -> None:
        self.node_id = node_id
        self.peers = peers
        self._policy = policy_engine or PolicyEngine()
        self._running = False

        # Action callbacks: PolicyAction → list of callables
        self._callbacks: dict[PolicyAction, list[Callable]] = {
            action: [] for action in PolicyAction
        }

        # Internal event queue
        self._event_queue: list[_ReactorEvent] = []
        self._queue_lock = threading.Lock()

        # Event log
        self._log: list[dict] = []

        # Metrics
        self._reaction_count = 0

    # ── Subscribe ─────────────────────────────────────────────────────────

    def on_action(self, action: PolicyAction, cb: Callable[[ReactionAction], None]) -> None:
        """Register a callback to be called when `action` is triggered."""
        self._callbacks[action].append(cb)

    # ── Emit events ────────────────────────────────────────────────────────

    def on_sbs_violation(
        self,
        violations: list,
        stage: str = "",
        node_id: str | None = None,
        violation_type: str = "CRITICAL",
    ) -> ReactionAction | None:
        """Called when SBS detects invariant violation(s)."""
        is_critical = violation_type == "CRITICAL" or any(
            v.get("severity") == "CRITICAL" for v in violations
        )
        context = {
            "violations": violations,
            "stage": stage,
            "node_id": node_id or self.node_id,
            "violation_type": violation_type,
            "is_critical": is_critical,
        }
        return self._emit(
            _EventType.SBS_VIOLATION,
            ReactionTrigger.SBS_VIOLATION,
            context,
        )

    def on_leader_uniqueness_violation(
        self,
        leaders: list[str],
        term: int,
    ) -> ReactionAction | None:
        """Called when two nodes both believe they are leader (split-brain)."""
        context = {
            "leaders": leaders,
            "term": term,
            "violation_type": "CRITICAL",
        }
        return self._emit(
            _EventType.SBS_VIOLATION,
            ReactionTrigger.LEADER_UNIQUENESS_VIOLATION,
            context,
        )

    def on_node_unreachable(
        self,
        peer: str,
        consecutive_failures: int = 1,
        lag_ms: float = 0.0,
    ) -> ReactionAction | None:
        """Called when a health ping fails."""
        context = {
            "peer": peer,
            "consecutive_failures": consecutive_failures,
            "lag_ms": lag_ms,
        }
        return self._emit(
            _EventType.NODE_UNREACHABLE,
            ReactionTrigger.NODE_UNREACHABLE,
            context,
        )

    def on_node_recovered(self, peer: str) -> ReactionAction | None:
        """Called when a previously unreachable node responds again."""
        context = {"peer": peer}
        return self._emit(
            _EventType.NODE_RECOVERED,
            ReactionTrigger.NODE_RECOVERED,
            context,
        )

    def on_partition_detected(
        self,
        partitioned_nodes: list[str],
        partition_type: str = "bidirectional",
    ) -> ReactionAction | None:
        """Called when chaos harness or health graph detects partition."""
        context = {
            "partitioned_nodes": partitioned_nodes,
            "partition_type": partition_type,
        }
        return self._emit(
            _EventType.PARTITION,
            ReactionTrigger.PARTITION_DETECTED,
            context,
        )

    def on_partition_healed(self, healed_nodes: list[str]) -> ReactionAction | None:
        """Called when partition resolves."""
        context = {"healed_nodes": healed_nodes}
        return self._emit(
            _EventType.PARTITION,
            ReactionTrigger.PARTITION_HEALED,
            context,
        )

    def on_byzantine_signal(
        self,
        node_id: str,
        conflicting_states: list[dict],
        evidence: str = "",
    ) -> ReactionAction | None:
        """Called when SBS detects a byzantine node (conflicting state)."""
        context = {
            "node_id": node_id,
            "conflicting_states": conflicting_states,
            "evidence": evidence,
        }
        return self._emit(
            _EventType.BYZANTINE,
            ReactionTrigger.BYZANTINE_SIGNAL,
            context,
        )

    def on_quorum_degraded(
        self,
        current_ratio: float,
        required_ratio: float = 0.71,
        active_nodes: list[str] | None = None,
    ) -> ReactionAction | None:
        """Called when F2 quorum ratio drops below SLO."""
        context = {
            "current_ratio": current_ratio,
            "required_ratio": required_ratio,
            "active_nodes": active_nodes or self.peers,
            "degraded": current_ratio < required_ratio,
        }
        trigger = ReactionTrigger.QUORUM_LOST if current_ratio < required_ratio else ReactionTrigger.QUORUM_DEGRADED
        return self._emit(_EventType.QUORUM_CHANGE, trigger, context)

    def on_drl_latency_exceeded(
        self,
        peer: str,
        current_latency_ms: float,
        slo_ms: float = 100.0,
    ) -> ReactionAction | None:
        """Called when DRL RPC latency exceeds SLO."""
        context = {
            "peer": peer,
            "current_latency_ms": current_latency_ms,
            "slo_ms": slo_ms,
            "exceeded_by_ms": current_latency_ms - slo_ms,
        }
        return self._emit(
            _EventType.DRL_SLO,
            ReactionTrigger.DRL_LATENCY_EXCEEDED,
            context,
        )

    def on_drl_loss_exceeded(
        self,
        peer: str,
        loss_rate: float,
        slo_rate: float = 0.05,
    ) -> ReactionAction | None:
        """Called when DRL packet loss exceeds SLO."""
        context = {
            "peer": peer,
            "loss_rate": loss_rate,
            "slo_rate": slo_rate,
            "exceeded": loss_rate > slo_rate,
        }
        return self._emit(
            _EventType.DRL_SLO,
            ReactionTrigger.DRL_LOSS_EXCEEDED,
            context,
        )

    def on_stability_score_low(
        self,
        score: float,
        threshold: float = 0.7,
        components: dict | None = None,
    ) -> ReactionAction | None:
        """Called when overall stability score drops below threshold."""
        context = {
            "score": score,
            "threshold": threshold,
            "components": components or {},
        }
        return self._emit(
            _EventType.STABILITY,
            ReactionTrigger.STABILITY_SCORE_LOW,
            context,
        )

    def on_node_evicted(self, evicted_node: str, reason: str = "") -> ReactionAction | None:
        context = {"evicted_node": evicted_node, "reason": reason}
        return self._emit(
            _EventType.NODE_UNREACHABLE,
            ReactionTrigger.NODE_EVICTED,
            context,
        )

    def on_node_joined(self, new_node: str) -> ReactionAction | None:
        context = {"new_node": new_node}
        return self._emit(
            _EventType.NODE_RECOVERED,
            ReactionTrigger.NODE_JOINED,
            context,
        )

    def on_recovery_complete(
        self,
        action: PolicyAction,
        target: str | None = None,
        duration_ms: float = 0.0,
    ) -> ReactionAction | None:
        context = {
            "recovery_action": action.name,
            "target": target,
            "duration_ms": duration_ms,
        }
        return self._emit(
            _EventType.QUORUM_CHANGE,
            ReactionTrigger.RECOVERY_COMPLETE,
            context,
        )

    # ── Core dispatch ─────────────────────────────────────────────────────

    def _emit(
        self,
        event_type: _EventType,
        trigger: ReactionTrigger,
        context: dict,
    ) -> ReactionAction | None:
        """
        Core event pipeline:

            event → PolicyEngine.decide() → ReactionAction
                                          → callbacks
                                          → log
        """
        self._reaction_count += 1
        now = time.monotonic()

        # Build event
        event = _ReactorEvent(
            event_type=event_type,
            trigger=trigger,
            context=dict(context),
            raw={"event_type": event_type.name},
        )

        # Enqueue
        with self._queue_lock:
            self._event_queue.append(event)

        # Query policy
        policy_action = self._policy.decide(trigger, context)

        # Build reaction
        reaction = ReactionAction(
            action=policy_action,
            target=context.get("peer") or context.get("node_id"),
            reason=f"{trigger.name} → {policy_action.name}",
            metadata={
                "trigger": trigger.name,
                "event_type": event_type.name,
                "context_keys": list(context.keys()),
                "reaction_count": self._reaction_count,
            },
        )

        # Log
        self._log.append({
            "ts": now,
            "reaction_n": self._reaction_count,
            "event_type": event_type.name,
            "trigger": trigger.name,
            "policy_action": policy_action.name,
            "reaction": repr(reaction),
            "context": context,
        })

        # Dispatch to callbacks
        for cb in self._callbacks.get(policy_action, []):
            try:
                cb(reaction)
            except Exception as exc:
                self._log.append({
                    "ts": now,
                    "reaction_n": self._reaction_count,
                    "callback_error": str(exc),
                })

        return reaction

    # ── Introspection ──────────────────────────────────────────────────────

    def get_reaction_log(self, last_n: int | None = None) -> list[dict]:
        log = list(reversed(self._log))
        return log[:last_n] if last_n is not None else log

    def get_policy(self) -> PolicyEngine:
        return self._policy

    def reaction_count(self) -> int:
        return self._reaction_count

    def dump(self) -> dict:
        return {
            "node_id": self.node_id,
            "reaction_count": self._reaction_count,
            "policy": self._policy.dump(),
            "callbacks": {
                action.name: len(cbs)
                for action, cbs in self._callbacks.items()
                if cbs
            },
        }
