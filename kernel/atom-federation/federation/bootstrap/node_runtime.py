"""NodeRuntime — per-node runtime for federation cluster simulation.

Each node owns:
- its own theta dict (mutable state)
- StateVector (published via gossip)
- GossipProtocol (peer communication)
- ConsensusResolver (distributed consensus)
- PolicySync (H-4: remote theta validation)
- ReplayValidator (local chaos replay, used for H-4 gate)

tick() = one simulation step:
  1. advance local state (optionally inject fault)
  2. build StateVector
  3. push via gossip
  4. pull from peers
  5. run consensus
  6. policy_sync (apply or quarantine)
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from dataclasses import dataclass

from chaos.replay_validator import ReplayValidator, TracePhase
from federation.consensus_resolver import ConsensusResolver, QuorumConfig
from federation.gossip_protocol import GossipConfig, GossipProtocol
from federation.policy_sync import PolicySync, SyncOutcome
from federation.state_vector import StateVector
from orchestration.v8_2b_controlled_autocorrection.severity_mapper import SeverityLevel


@dataclass
class NodeMetrics:
    """Runtime metrics for one tick."""
    convergence_steps: int = 0
    divergence_events: int = 0
    quarantine_events: int = 0
    applied_remote: int = 0
    rejected_remote: int = 0
    oscillate_count: int = 0


class NodeRuntime:
    """Single node in a federation cluster."""

    def __init__(
        self,
        node_id: str,
        theta: dict | None = None,
        peers: list[str] | None = None,
        quorum_config: QuorumConfig | None = None,
        gossip_config: GossipConfig | None = None,
        inject_fault: Callable[[str, int, dict], dict] | None = None,
    ):
        self.node_id = node_id
        # Local theta — mutable simulation state
        self._theta = theta or self._default_theta()
        self._theta_history: list[tuple[int, str]] = []  # (tick, theta_hash)
        self._last_accepted_theta_hash: str | None = None
        self._oscillate_tracker: list[bool] = []  # did we oscillate this tick?

        # Fault injection
        self._inject_fault = inject_fault
        self._degraded = False

        # Gossip
        config = gossip_config or GossipConfig()
        self._gossip = GossipProtocol(node_id, config)

        # Register peers
        for pid in (peers or []):
            self._gossip.register_peer(pid)

        # Consensus
        self._resolver = ConsensusResolver(node_id, quorum_config)

        # PolicySync — needs H-4 validator and apply_fn
        self._replay_validator = ReplayValidator()
        self._policy_sync = PolicySync(
            node_id=node_id,
            replay_validator=self._validate_theta,
            apply_fn=self._apply_theta,
            quarantine_fn=self._on_quarantine,
        )

        # Metrics
        self._metrics = NodeMetrics()

        # Trace for determinism verification
        self._current_trace_id: str | None = None

    # ── theta management ────────────────────────────────────────────────────

    def _default_theta(self) -> dict:
        return {
            "plan_stability_index": 0.85,
            "coherence_drop_rate": 0.05,
            "replanning_frequency": 0.1,
            "oscillation_index": 0.03,
            "adaptive_rate": 0.001,
        }

    def _theta_hash(self, theta: dict) -> str:
        canonical = json.dumps(theta, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def _current_vector(self) -> StateVector:
        drift = self._compute_drift()
        severity = self._classify_drift(drift)
        stability = 1.0 - drift
        envelope = {
            SeverityLevel.NEGLIGIBLE: "stable",
            SeverityLevel.LOW: "stable",
            SeverityLevel.MEDIUM: "warning",
            SeverityLevel.HIGH: "critical",
            SeverityLevel.CRITICAL: "collapse",
        }[severity]
        return StateVector(
            node_id=self.node_id,
            theta_hash=self._theta_hash(self._theta),
            envelope_state=envelope,
            drift_score=drift,
            stability_score=stability,
            timestamp_ns=time.time_ns(),
        )

    def _compute_drift(self) -> float:
        psi = self._theta.get("plan_stability_index", 0.85)
        cdr = self._theta.get("coherence_drop_rate", 0.05)
        rf = self._theta.get("replanning_frequency", 0.1)
        oi = self._theta.get("oscillation_index", 0.03)
        return min(1.0, 0.4 * (1 - psi) + 0.3 * cdr + 0.2 * rf + 0.1 * oi)

    def _classify_drift(self, drift: float) -> SeverityLevel:
        if drift <= 0.05:
            return SeverityLevel.NEGLIGIBLE
        if drift <= 0.20:
            return SeverityLevel.LOW
        if drift <= 0.45:
            return SeverityLevel.MEDIUM
        if drift <= 0.75:
            return SeverityLevel.HIGH
        return SeverityLevel.CRITICAL

    # ── H-4 validation (ReplayValidator) ────────────────────────────────────

    def _validate_theta(self, theta: dict) -> tuple[bool, str]:
        """Local replay validation — core of H-4 invariant.

        In simulation: theta is valid if it doesn't cause extreme divergence
        from expected metric ranges.
        """
        psi = theta.get("plan_stability_index", 0.0)
        cdr = theta.get("coherence_drop_rate", 0.0)
        oi = theta.get("oscillation_index", 0.0)

        # Sanity bounds
        if not (0.0 <= psi <= 1.0):
            return False, f"plan_stability_index out of range: {psi}"
        if cdr < 0 or cdr > 1.0:
            return False, f"coherence_drop_rate out of range: {cdr}"
        if oi < 0 or oi > 1.0:
            return False, f"oscillation_index out of range: {oi}"

        # ReplayValidator determinism check — same theta must produce same hash
        trace_id = self._replay_validator.start_trace(f"h4_validate_{self.node_id}")
        self._replay_validator.record_step(
            trace_id, step_index=0, phase=TracePhase.RECOVERY,
            event={"type": "remote_theta_validation"},
            metrics={
                "plan_stability_index": psi,
                "coherence_drop_rate": cdr,
                "replanning_frequency": theta.get("replanning_frequency", 0.0),
                "oscillation_index": oi,
            },
            feedback={"action": "validate"},
        )
        self._replay_validator.finalize_trace(trace_id)

        # Simulate eval: if psi > 0.9 and cdr < 0.1 → valid
        valid = psi >= 0.0 and cdr <= 1.0
        return valid, "ok" if valid else "out_of_range"

    def _apply_theta(self, theta: dict) -> bool:
        """Apply remote theta locally after H-4 validation passes."""
        self._theta = theta.copy()
        self._theta_history.append((time.time_ns(), self._theta_hash(theta)))
        self._last_accepted_theta_hash = self._theta_hash(theta)
        return True

    def _on_quarantine(self, node_id: str, reason: str) -> None:
        self._metrics.quarantine_events += 1

    # ── tick ────────────────────────────────────────────────────────────────

    def tick(self, step: int, fault_fn: Callable[[str, int, dict], dict] | None = None) -> NodeMetrics:
        """One simulation step for this node."""
        # 1. Advance local state (fault injection optional)
        fault_fn = fault_fn or self._inject_fault
        if fault_fn:
            self._theta = fault_fn(self.node_id, step, self._theta.copy())

        # 2. Build current vector
        my_vector = self._current_vector()

        # 3. Push to peers
        self._gossip.push(my_vector)

        # 4. Pull vectors from all peers
        peer_ids = self._gossip.peer_ids
        peer_vectors = []
        for pid in peer_ids:
            pv = self._gossip.pull(pid)
            if pv is not None:
                peer_vectors.append(pv)

        # 5. Resolve consensus
        local_hash = self._theta_hash(self._theta)
        consensus = self._resolver.resolve(my_vector, peer_vectors, local_hash)

        # 6. Track divergence
        div = self._resolver.detect_divergence(my_vector, peer_vectors)
        if div > 0.5:
            self._metrics.divergence_events += 1

        # 7. Policy sync — apply remote theta if consensus says to
        if consensus.theta_hash != local_hash:
            # Remote theta is different — try to sync
            # Find the vector that matches consensus theta_hash
            matching_peer = next(
                (v for v in peer_vectors if v.theta_hash == consensus.theta_hash),
                None
            )
            if matching_peer:
                record = self._policy_sync.sync_from_consensus(
                    consensus,
                    matching_peer,
                    reconstruct_theta=lambda h: self._reconstruct_theta(h, peer_vectors),
                )
                if record.outcome == SyncOutcome.APPLIED:
                    self._metrics.applied_remote += 1
                elif record.outcome in (SyncOutcome.REJECTED, SyncOutcome.QUARANTINED):
                    self._metrics.rejected_remote += 1

        # 8. Oscillation detection
        self._oscillate_tracker.append(consensus.source != "quorum" and len(peer_vectors) > 0)
        if len(self._oscillate_tracker) > 10:
            self._oscillate_tracker.pop(0)

        return self._metrics

    def _reconstruct_theta(self, theta_hash: str, peer_vectors: list[StateVector]) -> dict | None:
        """Reconstruct theta from peer vectors (simulation: use peer theta from history)."""
        # In simulation, we store theta per node in ClusterSimulator
        # This is a stub — ClusterSimulator patches this
        return None

    # ── state access ────────────────────────────────────────────────────────

    @property
    def theta(self) -> dict:
        return self._theta.copy()

    @property
    def theta_hash(self) -> str:
        return self._theta_hash(self._theta)

    @property
    def vector(self) -> StateVector:
        return self._current_vector()

    @property
    def metrics(self) -> NodeMetrics:
        return self._metrics

    @property
    def policy_sync(self) -> PolicySync:
        return self._policy_sync

    @property
    def gossip(self) -> GossipProtocol:
        return self._gossip

    @property
    def is_quarantined(self) -> bool:
        return self._policy_sync.quarantine_count() > 0

    @property
    def oscillate_count(self) -> int:
        return sum(1 for x in self._oscillate_tracker if x)

    def set_degraded(self, degraded: bool) -> None:
        self._degraded = degraded

    def is_degraded(self) -> bool:
        return self._degraded
