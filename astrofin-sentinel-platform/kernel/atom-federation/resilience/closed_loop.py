"""
ClosedLoopResilienceController v6.4 — Integrates all resilience components.

Wires together:
  Reactor → PolicyEngine → HealingAction → SelfHealingControlPlane
         ↘ AdaptiveRouter (routing updates)
         ↘ StabilityMetricsEngine (score feedback)

Usage:
    ctrl = ClosedLoopResilienceController(
        node_id="node-a",
        peers=["node-b", "node-c"],
    )
    ctrl.start()

    # Events flow automatically:
    ctrl.on_sbs_violation([...])
    ctrl.on_node_unreachable("node-b", consecutive=3)

    # Or query state:
    score = ctrl.stability_score()
    log.info(ctrl.dump())
"""

from __future__ import annotations

import threading
import time

from resilience.adaptive_router import AdaptiveRouter
from resilience.healer import HealingAction, HealingResult, SelfHealingControlPlane
from resilience.metrics_engine import StabilityMetricsEngine, StabilitySnapshot
from resilience.policy_engine import PolicyAction, PolicyEngine
from resilience.reactor import ReactionAction, ResilienceReactor

import logging
log = logging.getLogger(__name__)


__all__ = ["ClosedLoopResilienceController"]


class ClosedLoopResilienceController:
    """
    Single unified resilience controller for ATOMFederationOS v6.4.

    This is the ONLY public API the rest of the system (ClusterNode, gRPC layer)
    needs to talk to for all resilience concerns.

    Closed feedback loop:
        ClusterNode
          ↓ (events)
        ResilienceReactor
          ↓ (PolicyEngine.decide)
        PolicyAction
          ├→ SelfHealingControlPlane.execute()  [heals]
          ├→ AdaptiveRouter.update()            [routes]
          └→ StabilityMetricsEngine.record()    [measures]
          ↓
        StabilitySnapshot (fed back into next decision)
    """

    def __init__(
        self,
        node_id: str,
        peers: list[str],
        stability_threshold: float = 0.7,
        critical_threshold: float = 0.3,
    ) -> None:
        self.node_id = node_id
        self.peers = list(peers)
        self._stability_threshold = stability_threshold
        self._critical_threshold = critical_threshold

        # ── Core components ────────────────────────────────────────────────
        self.policy = PolicyEngine()
        self.reactor = ResilienceReactor(node_id, peers, self.policy)
        self.healer = SelfHealingControlPlane(node_id, peers)
        self.router = AdaptiveRouter(node_id, peers)
        self.metrics = StabilityMetricsEngine(node_count=len(peers) + 1)

        # ── Wiring ────────────────────────────────────────────────────────
        self._wire_callbacks()
        self._running = False
        self._闭环 = True  # closed-loop enabled by default

        # Metrics snapshot cache
        self._snapshot_cache: StabilitySnapshot | None = None
        self._snapshot_lock = threading.Lock()

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def start(self) -> None:
        self.healer.start()
        self._running = True

    def stop(self) -> None:
        self._running = False
        self.healer.stop()

    # ── Event ingress (called by ClusterNode / gRPC layer) ────────────────

    def on_sbs_violation(
        self,
        violations: list,
        stage: str = "",
        node_id: str | None = None,
        violation_type: str = "CRITICAL",
    ) -> ReactionAction:
        self.metrics.record_violation("sbs", severity=violation_type.lower())
        self.metrics.record_anomaly("sbs_violation")
        return self.reactor.on_sbs_violation(
            violations, stage, node_id, violation_type
        )

    def on_leader_uniqueness_violation(
        self,
        leaders: list[str],
        term: int,
    ) -> ReactionAction:
        self.metrics.record_violation("sbs", severity="critical")
        self.metrics.record_anomaly("split_brain")
        return self.reactor.on_leader_uniqueness_violation(leaders, term)

    def on_node_unreachable(
        self,
        peer: str,
        consecutive_failures: int = 1,
        lag_ms: float = 0.0,
    ) -> ReactionAction:
        self.metrics.record_node_down(peer)
        self.router.update_peer_metrics(peer, latency_ms=lag_ms, success=False)
        return self.reactor.on_node_unreachable(peer, consecutive_failures, lag_ms)

    def on_node_recovered(self, peer: str, lag_ms: float = 0.0) -> ReactionAction:
        self.metrics.record_node_up(peer)
        self.router.update_peer_metrics(peer, latency_ms=lag_ms, success=True)
        return self.reactor.on_node_recovered(peer)

    def on_partition_detected(
        self,
        partitioned_nodes: list[str],
        partition_type: str = "bidirectional",
    ) -> ReactionAction:
        for node in partitioned_nodes:
            self.metrics.record_violation("network", severity="critical")
        self.metrics.record_anomaly(f"partition_{partition_type}")
        return self.reactor.on_partition_detected(partitioned_nodes, partition_type)

    def on_partition_healed(self, healed_nodes: list[str]) -> ReactionAction:
        for node in healed_nodes:
            self.metrics.record_recovery(node)
        return self.reactor.on_partition_healed(healed_nodes)

    def on_byzantine_signal(
        self,
        node_id: str,
        conflicting_states: list[dict],
        evidence: str = "",
    ) -> ReactionAction:
        self.metrics.record_violation("sbs", severity="critical")
        self.metrics.record_anomaly("byzantine_node")
        return self.reactor.on_byzantine_signal(node_id, conflicting_states, evidence)

    def on_drl_latency(
        self,
        peer: str,
        latency_ms: float,
        slo_ms: float = 100.0,
        success: bool = True,
    ) -> None:
        self.router.update_peer_metrics(peer, latency_ms=latency_ms, success=success)
        if latency_ms > slo_ms:
            self.metrics.record_violation("network", severity="warning")
            self.reactor.on_drl_latency_exceeded(peer, latency_ms, slo_ms)

    def on_drl_loss(
        self,
        peer: str,
        loss_rate: float,
        slo_rate: float = 0.05,
    ) -> None:
        self.router.update_peer_metrics(peer, loss_rate=loss_rate, success=loss_rate < slo_rate)
        if loss_rate > slo_rate:
            self.metrics.record_violation("network", severity="warning")
            self.reactor.on_drl_loss_exceeded(peer, loss_rate, slo_rate)

    def on_rpc_result(
        self,
        peer: str,
        latency_ms: float,
        success: bool,
        loss_observed: float = 0.0,
    ) -> None:
        """Convenience: called after each RPC to feed router + metrics."""
        self.router.update_peer_metrics(
            peer,
            latency_ms=latency_ms,
            loss_rate=loss_observed,
            success=success,
        )
        if success:
            self.metrics.record_op_success()
        else:
            self.metrics.record_op_failure()
            self.metrics.record_node_down(peer)

    # ── Routing interface ────────────────────────────────────────────────

    def get_route(self) -> str:
        """Get best peer for routing."""
        route = self.router.route()
        return route.chosen_peer or ""

    def get_all_routes(self) -> dict:
        """Get full routing state."""
        return self.router.get_slo_status()

    def get_healthy_peers(self) -> list[str]:
        """Get list of currently healthy (non-violating) peers."""
        return [
            p for p, s in self.router.get_slo_status().items()
            if not s.get("violating_slo", True)
        ]

    # ── Stability / metrics ─────────────────────────────────────────────

    def stability_score(self) -> float:
        snap = self.get_snapshot()
        return snap.stability_score

    def get_snapshot(self) -> StabilitySnapshot:
        with self._snapshot_lock:
            snap = self.metrics.get_snapshot()
            self._snapshot_cache = snap
            return snap

    def is_stable(self) -> bool:
        return self.metrics.is_stable(self._stability_threshold)

    def is_critical(self) -> bool:
        return self.metrics.is_critical(self._critical_threshold)

    # ── Healing interface ────────────────────────────────────────────────

    def heal_sync(
        self,
        action: HealingAction,
        target: str | None = None,
    ) -> HealingResult:
        """Synchronous healing for critical paths."""
        return self.healer.heal_sync(action, target)

    def heal_async(
        self,
        action: HealingAction,
        target: str | None = None,
    ) -> None:
        self.healer.heal(action, target)

    # ── Introspection ───────────────────────────────────────────────────

    def dump(self) -> dict:
        snap = self.get_snapshot()
        return {
            "node_id": self.node_id,
            "闭环_enabled": self._闭环,
            "stability": {
                "score": round(snap.stability_score, 4),
                "is_healthy": snap.is_healthy(self._stability_threshold),
                "is_critical": snap.stability_score < self._critical_threshold,
                "rto_ms": round(snap.rto_ms, 1),
                "convergence_ms": round(snap.convergence_time_ms, 1),
                "recovery_rate": round(snap.recovery_rate, 4),
                "violations_60s": snap.violation_count_60s,
            },
            "router": {
                "best_peer": self.get_route(),
                "healthy_peers": self.get_healthy_peers(),
                "violating": self.router.get_violating_peers(),
                "route_count": self.router.route_count(),
            },
            "healer": {
                "heal_count": self.healer.heal_count(),
                "quorum_members": self.healer.get_quorum_members(),
                "is_quorate": self.healer.is_quorate(),
                "evicted": list(self.healer.get_evicted()),
                "byzantine": list(self.healer.get_byzantine()),
            },
            "reactor": {
                "reaction_count": self.reactor.reaction_count(),
            },
            "policy_rules_count": len(self.policy.list_rules()),
        }

    # ── Internal wiring ─────────────────────────────────────────────────

    def _wire_callbacks(self) -> None:
        """
        Wire PolicyAction callbacks to actual executors.
        This is where the closed loop closes:
        PolicyEngine decision → real system action.
        """

        def _handle_evict(reaction: ReactionAction) -> None:
            if reaction.target:
                self.healer.heal(HealingAction.EVICT_NODE, reaction.target)
                self.router.remove_peer_from_rotation(reaction.target)
                self.metrics.record_violation("sbs", severity="critical")

        def _handle_observe(reaction: ReactionAction) -> None:
            if reaction.target:
                # Mark degraded but don't remove from cluster
                self.metrics.record_violation("sbs", severity="warning")

        def _handle_reconfigure(reaction: ReactionAction) -> None:
            self.healer.heal(HealingAction.RECONFIGURE_QUORUM)

        def _handle_re_election(reaction: ReactionAction) -> None:
            self.healer.heal(HealingAction.TRIGGER_RE_ELECTION)

        def _handle_byzantine(reaction: ReactionAction) -> None:
            if reaction.target:
                self.healer.heal(HealingAction.ISOLATE_BYZANTINE, reaction.target)
                self.router.remove_peer_from_rotation(reaction.target)
                self.metrics.record_violation("sbs", severity="critical")

        def _handle_restore(reaction: ReactionAction) -> None:
            if reaction.target:
                self.healer.heal(HealingAction.RESTORE_NODE, reaction.target)
                self.router.restore_peer_to_rotation(reaction.target)
                self.metrics.record_recovery(reaction.target)

        def _handle_self_heal(reaction: ReactionAction) -> None:
            start = time.monotonic()
            self.healer.heal(HealingAction.RECONFIGURE_QUORUM)
            for peer in self.get_healthy_peers():
                self.healer.heal(HealingAction.RESTORE_NODE, peer)
            self.metrics.record_convergence((time.monotonic() - start) * 1000)

        def _handle_alert(reaction: ReactionAction) -> None:
            self.metrics.record_anomaly("ops_alert")

        def _handle_drain(reaction: ReactionAction) -> None:
            if reaction.target:
                self.healer.heal(HealingAction.DRAIN_NODE, reaction.target)
                self.router.remove_peer_from_rotation(reaction.target)

        self.reactor.on_action(PolicyAction.EVICT_NODE, _handle_evict)
        self.reactor.on_action(PolicyAction.ADD_OBSERVATION, _handle_observe)
        self.reactor.on_action(PolicyAction.RECONFIGURE_QUORUM, _handle_reconfigure)
        self.reactor.on_action(PolicyAction.TRIGGER_RE_ELECTION, _handle_re_election)
        self.reactor.on_action(PolicyAction.ISOLATE_BYZANTINE, _handle_byzantine)
        self.reactor.on_action(PolicyAction.RESTORE_NODE, _handle_restore)
        self.reactor.on_action(PolicyAction.TRIGGER_SELF_HEAL, _handle_self_heal)
        self.reactor.on_action(PolicyAction.ALERT_OPS, _handle_alert)
        self.reactor.on_action(PolicyAction.DRAIN_NODE, _handle_drain)
        self.reactor.on_action(PolicyAction.LOG_ONLY, lambda r: None)
        self.reactor.on_action(PolicyAction.NOOP, lambda r: None)

        # Healing results feed back into metrics
        def _healing_result_cb(result: HealingResult) -> None:
            self.metrics.record_recovery(
                result.target or "",
                duration_ms=result.duration_ms,
            )
            self.metrics.record_anomaly(f"healing.{result.action.name}")

        self.healer.on_result(_healing_result_cb)
