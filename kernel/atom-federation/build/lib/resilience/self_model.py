"""
SelfModel v6.6 — Internal representation of ATOMFederationOS.

Problem:
  The system reacts to events but has no internal model of itself.
  It cannot predict its own future states or simulate actions.

Solution:
  SelfModel builds a causal graph of the cluster:
    - Node states (healthy / degraded / byzantine / evicted)
    - RPC dependency edges
    - Invariant relationships (which invariants depend on which nodes)
    - Failure propagation paths

Capabilities:
  1. build_model(snapshot)     — reconstruct internal state graph
  2. predict_next_state(action) — simulate what happens if action is taken
  3. forecast_stability(horizon_s) — project stability score N seconds ahead
  4. get_cascade_path(node)   — trace failure propagation chain

Usage:
    model = SelfModel()
    model.build_model(snapshot)
    predicted = model.predict_next_state(snapshot, PolicyAction.EVICT_NODE, target="node-b")
    forecast_30s = model.forecast_stability(snapshot, horizon_s=30.0)
    cascade = model.get_cascade_path("node-b")
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto

from resilience.metrics_engine import StabilitySnapshot
from resilience.policy_engine import PolicyAction

__all__ = ["CascadeNode", "NodeRole", "SelfModel", "SystemState"]


# ── Node roles in the causal graph ───────────────────────────────────────────

class NodeRole(Enum):
    HEALTHY = auto()
    DEGRADED = auto()
    BYZANTINE = auto()
    EVICTED = auto()
    UNKNOWN = auto()


@dataclass
class CascadeNode:
    node_id: str
    role: NodeRole
    depended_on_by: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    stability_contribution: float = 1.0  # how much this node affects cluster stability


# ── SystemState — internal model of cluster state ─────────────────────────────

@dataclass
class SystemState:
    """
    Internal causal model of the cluster.
    
    Maintains:
      - node_roles: current role of each node
      - dependency_graph: RPC call graph (who depends on whom)
      - stability_trend: recent stability trajectory for forecasting
      - invariant_dependencies: which invariants depend on which nodes
    """
    node_count_total: int
    node_count_healthy: int
    stability_score: float
    quorum_health: float
    leader_count: int = 1  # default to 1; not in snapshot, inferred
    leader_id: str | None = None  # not in snapshot
    node_roles: dict[str, NodeRole] = field(default_factory=dict)
    dependency_graph: dict[str, list[str]] = field(default_factory=dict)
    stability_trend: list[float] = field(default_factory=list)
    convergence_time_ms: float = 0.0
    rto_ms: float = 0.0
    recovery_rate: float = 1.0
    violation_count_60s: int = 0
    sbs_health: float = 1.0
    network_health: float = 1.0
    routing_health: float = 1.0
    ts: float = field(default_factory=time.monotonic)

    @classmethod
    def from_snapshot(cls, snap: StabilitySnapshot, peers: list[str]) -> SystemState:
        """Build SystemState from a StabilitySnapshot."""
        roles = {}
        for peer in peers:
            if snap.stability_score < 0.3:
                roles[peer] = NodeRole.DEGRADED
            elif snap.stability_score > 0.7:
                roles[peer] = NodeRole.HEALTHY
            else:
                roles[peer] = NodeRole.HEALTHY

        # Build dependency graph (simple: all nodes depend on each other)
        dep_graph = {peer: [p2 for p2 in peers if p2 != peer] for peer in peers}

        # Infer leader_count from quorum_health
        leader_count = 1
        if snap.quorum_health < 0.5:
            leader_count = 2  # possible split-brain

        return cls(
            node_count_total=snap.node_count_total,
            node_count_healthy=snap.node_count_healthy,
            stability_score=snap.stability_score,
            quorum_health=snap.quorum_health,
            leader_count=leader_count,
            leader_id=None,
            node_roles=roles,
            dependency_graph=dep_graph,
            stability_trend=[snap.stability_score],
            convergence_time_ms=snap.convergence_time_ms,
            rto_ms=snap.rto_ms,
            recovery_rate=snap.recovery_rate,
            violation_count_60s=snap.violation_count_60s,
            sbs_health=snap.sbs_health,
            network_health=snap.network_health,
            routing_health=getattr(snap, 'routing_health', 1.0),
        )

    def record_score(self, score: float) -> None:
        """Append to stability trend for time-series forecasting."""
        self.stability_trend.append(score)
        # Keep last 60 points (60 seconds at 1Hz)
        if len(self.stability_trend) > 60:
            self.stability_trend = self.stability_trend[-60:]

    def to_dict(self) -> dict:
        return {
            "node_count_total": self.node_count_total,
            "node_count_healthy": self.node_count_healthy,
            "stability_score": round(self.stability_score, 4),
            "leader_id": self.leader_id,
            "leader_count": self.leader_count,
            "node_roles": {k: v.name for k, v in self.node_roles.items()},
            "stability_trend_len": len(self.stability_trend),
            "convergence_time_ms": round(self.convergence_time_ms, 1),
            "rto_ms": round(self.rto_ms, 1),
            "recovery_rate": round(self.recovery_rate, 4),
            "violation_count_60s": self.violation_count_60s,
        }


# ── SelfModel ────────────────────────────────────────────────────────────────

class SelfModel:
    """
    Internal causal model of the ATOMFederationOS cluster.

    SelfModel maintains a probabilistic causal graph and uses it for:
      - What-if analysis (simulate action before taking it)
      - Time-series forecasting (predict future stability)
      - Failure cascade tracing (which nodes would fail if X fails)
    """

    def __init__(self) -> None:
        self._state: SystemState | None = None
        self._cascade_cache: dict[str, list[str]] = {}

    def build_model(self, snap: StabilitySnapshot) -> None:
        """Reconstruct internal model from current snapshot."""
        self._state = SystemState.from_snapshot(snap, peers=self._infer_peers(snap))
        if self._state.stability_trend and len(self._state.stability_trend) == 1:
            # Extend initial trend with current score repeated
            self._state.stability_trend = [snap.stability_score] * 5
        self._cascade_cache.clear()

    def get_state(self) -> dict | None:
        """Return serializable model state."""
        if self._state is None:
            return None
        return self._state.to_dict()

    # ── What-if: predict next state ──────────────────────────────────────────

    def predict_next_state(
        self,
        snap: StabilitySnapshot,
        action: PolicyAction,
        target: str | None = None,
    ) -> StabilitySnapshot:
        """
        Simulate what the cluster state would look like after taking `action`.

        Returns a modified StabilitySnapshot reflecting the predicted outcome.
        This is a conservative/upper-bound prediction (worst case).
        """
        if self._state is None:
            self.build_model(snap)

        s = self._state

        # Clone relevant fields from current snapshot
        predicted_healthy = s.node_count_healthy
        predicted_convergence = s.convergence_time_ms
        predicted_violations = s.violation_count_60s
        predicted_leader_count = s.leader_count
        predicted_sbs_health = s.sbs_health
        predicted_network_health = s.network_health

        if action == PolicyAction.EVICT_NODE:
            if target and target in s.node_roles:
                if s.node_roles[target] not in (NodeRole.EVICTED, NodeRole.BYZANTINE):
                    predicted_healthy = max(0, predicted_healthy - 1)
                    predicted_violations += 1
                    predicted_convergence = min(60_000, predicted_convergence * 1.5)
                    # SBS health drops when quorum-reachable drops
                    if predicted_healthy < (s.node_count_total + 1) // 2:
                        predicted_sbs_health *= 0.7

        elif action == PolicyAction.RESTORE_NODE:
            if target and target in s.node_roles:
                if s.node_roles[target] in (NodeRole.EVICTED, NodeRole.DEGRADED):
                    predicted_healthy = min(s.node_count_total, predicted_healthy + 1)
                    predicted_violations = max(0, predicted_violations - 1)
                    predicted_convergence *= 0.7
                    predicted_sbs_health = min(1.0, predicted_sbs_health * 1.1)

        elif action == PolicyAction.ISOLATE_BYZANTINE:
            if target and target in s.node_roles:
                predicted_healthy = max(0, predicted_healthy - 1)
                predicted_sbs_health *= 0.5  # byzantine is worst case
                predicted_violations += 2

        elif action == PolicyAction.TRIGGER_RE_ELECTION:
            # Re-election causes brief instability then stabilizes
            predicted_convergence = min(60_000, predicted_convergence + 5_000)
            predicted_violations += 1

        elif action == PolicyAction.RECONFIGURE_QUORUM:
            # Reconfiguration improves long-term stability but brief cost
            predicted_convergence = min(60_000, predicted_convergence * 0.8)
            predicted_violations = max(0, predicted_violations - 1)
            predicted_sbs_health = min(1.0, predicted_sbs_health * 1.05)

        # Compute predicted stability score
        # Conservative: score degrades when healthy count drops
        if s.node_count_total > 0:
            health_ratio = predicted_healthy / s.node_count_total
        else:
            health_ratio = 1.0
        predicted_score = (
            health_ratio * predicted_sbs_health * predicted_network_health
        )
        predicted_score = max(0.0, min(1.0, predicted_score))

        # Create predicted snapshot matching actual StabilitySnapshot fields
        from resilience.metrics_engine import StabilitySnapshot
        return StabilitySnapshot(
            ts=time.time(),
            stability_score=predicted_score,
            quorum_health=s.quorum_health,
            network_health=predicted_network_health,
            sbs_health=predicted_sbs_health,
            routing_health=getattr(snap, 'routing_health', 1.0),
            rto_ms=predicted_convergence,
            convergence_time_ms=predicted_convergence,
            recovery_rate=s.recovery_rate,
            violation_count_60s=predicted_violations,
            node_count_total=s.node_count_total,
            node_count_healthy=predicted_healthy,
            anomaly_count=getattr(snap, 'anomaly_count', 0),
        )

    # ── Time-series forecasting ───────────────────────────────────────────────

    def forecast_stability(
        self,
        snap: StabilitySnapshot,
        horizon_s: float = 30.0,
    ) -> float:
        """
        Forecast stability score `horizon_s` seconds ahead.

        Uses exponential moving average (EMA) projection:
          - If trend is stable (low variance) → score stays near current
          - If trend is falling fast → extrapolate fall
          - If trend is rising → project modest rise

        Returns float in [0.0, 1.0].
        """
        if self._state is None:
            self.build_model(snap)

        trend = self._state.stability_trend

        if len(trend) < 2:
            # Not enough data: assume current score persists
            return snap.stability_score

        # Compute recent trend direction
        recent = trend[-5:] if len(trend) >= 5 else trend
        older = trend[-10:-5] if len(trend) >= 10 else trend[:-5] if len(trend) > 1 else recent

        if len(older) == 0:
            older = recent

        # EMA of recent vs older
        avg_recent = sum(recent) / len(recent)
        avg_older = sum(older) / len(older) if older else avg_recent

        delta = avg_recent - avg_older
        # Variance of recent scores (stability of trend)
        import statistics
        variance = statistics.pstdev(recent) if len(recent) > 1 else 0.0

        # Project forward using exponential decay toward a steady state
        steady_state = 0.70  # assumed equilibrium
        decay = 0.95 ** horizon_s  # longer horizon → more regression to mean

        # If variance is high, confidence in forecast is lower
        uncertainty = min(1.0, variance * 5)

        projected = (
            snap.stability_score
            + delta * decay  # trend continuation
            - (snap.stability_score - steady_state) * (1 - decay)  # mean reversion
        )

        # Apply uncertainty discount
        projected = projected * (1.0 - uncertainty * 0.1)

        return max(0.0, min(1.0, projected))

    # ── Failure cascade tracing ────────────────────────────────────────────────

    def get_cascade_path(self, failure_node: str) -> list[str]:
        """
        Trace failure propagation from `failure_node`.

        Returns ordered list of nodes that would fail as a consequence,
        including `failure_node` itself.

        Algorithm:
          1. Mark failure_node as FAILED
          2. Find all nodes that depend on it (direct dependents)
          3. Recursively add their dependents
          4. Return causal chain
        """
        if self._state is None:
            return [failure_node]

        # Check cache
        if failure_node in self._cascade_cache:
            return self._cascade_cache[failure_node]

        cascade = [failure_node]
        visited = {failure_node}

        def _add_cascade(node: str) -> None:
            if node in visited:
                return
            visited.add(node)
            deps = self._state.dependency_graph.get(node, [])
            for dep in deps:
                if dep not in visited:
                    # Check if this dependency is critical
                    role = self._state.node_roles.get(dep, NodeRole.UNKNOWN)
                    if role in (NodeRole.HEALTHY, NodeRole.DEGRADED):
                        cascade.append(dep)
                        _add_cascade(dep)

        # Nodes that depend on failure_node
        for node, deps in self._state.dependency_graph.items():
            if failure_node in deps and node not in visited:
                cascade.append(node)
                _add_cascade(node)

        # Sort by role priority (byzantine > degraded > healthy)
        role_priority = {
            NodeRole.BYZANTINE: 0,
            NodeRole.DEGRADED: 1,
            NodeRole.UNKNOWN: 2,
            NodeRole.EVICTED: 3,
            NodeRole.HEALTHY: 4,
        }
        cascade.sort(key=lambda n: role_priority.get(
            self._state.node_roles.get(n, NodeRole.UNKNOWN), 5
        ))

        self._cascade_cache[failure_node] = cascade
        return cascade

    # ── Internal ───────────────────────────────────────────────────────────────

    def _infer_peers(self, snap: StabilitySnapshot) -> list[str]:
        """Infer peer list from snapshot."""
        # Default peers if we can't determine
        total = snap.node_count_total
        return [f"node-{chr(98+i)}" for i in range(max(0, total - 1))]  # node-b, node-c, ...

    def dump(self) -> dict:
        return {
            "has_state": self._state is not None,
            "cascade_cache_size": len(self._cascade_cache),
            "state": self._state.to_dict() if self._state else None,
        }
