"""ClusterSimulator — simulates N-node federation cluster with fault injection.

Usage:
    sim = ClusterSimulator(nodes=3)
    sim.set_fault("node_c", fault_type="degrade")
    trace = sim.run(steps=50)

    # Check convergence
    assert trace.converged
    assert trace.oscillation_count == 0
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from federation.bootstrap.node_runtime import NodeRuntime
from federation.consensus_resolver import QuorumConfig
from federation.gossip_protocol import GossipConfig
from federation.state_vector import StateVector

# ── Fault injectors ────────────────────────────────────────────────────────────


def inject_degrade(node_id: str, step: int, theta: dict) -> dict:
    """Progressively degrade node: increase drift, lower stability."""
    t = theta.copy()
    t["plan_stability_index"] = max(0.1, t.get("plan_stability_index", 0.85) - 0.15)
    t["coherence_drop_rate"] = min(0.95, t.get("coherence_drop_rate", 0.05) + 0.20)
    t["replanning_frequency"] = min(0.9, t.get("replanning_frequency", 0.1) + 0.15)
    t["oscillation_index"] = min(0.8, t.get("oscillation_index", 0.03) + 0.10)
    return t


def inject_malicious_theta(node_id: str, step: int, theta: dict) -> dict:
    """Inject a deliberately bad theta that will fail H-4 validation."""
    t = theta.copy()
    t["plan_stability_index"] = 99.0   # out of range → replay fails
    t["coherence_drop_rate"] = -5.0    # invalid
    return t


def inject_partition(node_id: str, step: int, theta: dict) -> dict:
    """Node stops responding (simulated as no gossip push/pull)."""
    return theta  # no change — partition is simulated by removing node from peer list


# ── Scenario definition ───────────────────────────────────────────────────────


@dataclass
class Scenario:
    name: str
    nodes: list[str]  # node IDs participating
    fault_type: str | None = None  # degrade | malicious | partition | network_split
    fault_target: str | None = None  # which node gets the fault
    fault_step_start: int = 5
    fault_step_end: int | None = None  # None = stays degraded forever
    partition_groups: list[list[str]] | None = None  # for network_split: [[A,B], [C,D]]


@dataclass
class ClusterTrace:
    """Result of a cluster simulation run."""
    scenario_name: str
    total_steps: int
    converged: bool
    convergence_step: int | None  # first step where all live nodes agreed
    oscillation_count: int  # total ticks where consensus oscillated (non-quorum source)
    divergence_events: int
    quarantine_events: int
    applied_remote_count: int
    rejected_remote_count: int

    # Per-node snapshots at each step: list of dicts
    node_snapshots: dict[str, list[dict]] = field(default_factory=dict)

    # Theta hash history per node
    theta_history: dict[str, list[tuple[int, str]]] = field(default_factory=dict)

    # Key steps logged
    key_events: list[dict] = field(default_factory=list)

    def summary(self) -> str:
        status = "✅ CONVERGED" if self.converged else "❌ NOT CONVERGED"
        osc_warn = " ⚠️ OSCILLATION DETECTED" if self.oscillation_count > 0 else ""
        return (
            f"{status}\n"
            f"  Scenario:      {self.scenario_name}\n"
            f"  Total steps:   {self.total_steps}\n"
            f"  Converged at:  {self.convergence_step or 'N/A'}\n"
            f"  Oscillations: {self.oscillation_count}{osc_warn}\n"
            f"  Divergences:  {self.divergence_events}\n"
            f"  Quarantines:  {self.quarantine_events}\n"
            f"  Remote applied: {self.applied_remote_count}\n"
            f"  Remote rejected: {self.rejected_remote_count}\n"
        )


# ── ClusterSimulator ───────────────────────────────────────────────────────────


class ClusterSimulator:
    """N-node federation cluster with scenario-based fault injection."""

    def __init__(
        self,
        node_ids: list[str],
        quorum_config: QuorumConfig | None = None,
        gossip_config: GossipConfig | None = None,
    ):
        self.node_ids = node_ids
        self.nodes: dict[str, NodeRuntime] = {}
        self._quorum_config = quorum_config or QuorumConfig()
        self._gossip_config = gossip_config or GossipConfig(fanout=3)
        self._fault_state: dict[str, bool] = {n: False for n in node_ids}
        self._partition_state: dict[str, list[str]] = {}  # node → list of reachable peers

        self._build_nodes(node_ids)

    def _build_nodes(self, node_ids: list[str]) -> None:
        for nid in node_ids:
            peers = [p for p in node_ids if p != nid]
            self.nodes[nid] = NodeRuntime(
                node_id=nid,
                peers=peers,
                quorum_config=self._quorum_config,
                gossip_config=self._gossip_config,
            )
        # Initially all nodes can talk to all
        for nid in node_ids:
            self._partition_state[nid] = [p for p in node_ids if p != nid]

    def set_fault(self, node_id: str, fault_type: str) -> None:
        """Activate a fault on a specific node."""
        self._fault_state[node_id] = True

        if fault_type == "partition":
            # Simulate partition: node can only talk to itself (isolated)
            self._partition_state[node_id] = []

    def clear_fault(self, node_id: str) -> None:
        """Remove fault from a node (recovery scenario)."""
        self._fault_state[node_id] = False
        self._partition_state[node_id] = [p for p in self.node_ids if p != node_id]

    def apply_partition(self, groups: list[list[str]]) -> None:
        """Simulate network split: groups can't talk to each other."""
        self._partition_state = {}
        for group in groups:
            for node in group:
                self._partition_state[node] = [
                    p for p in group if p != node
                ]

    def merge_partitions(self) -> None:
        """Restore full connectivity."""
        for nid in self.node_ids:
            self._partition_state[nid] = [p for p in self.node_ids if p != nid]

    # ── core simulation ──────────────────────────────────────────────────────

    def _effective_peers(self, node_id: str) -> list[str]:
        """Return peers this node can reach (partition-aware)."""
        return self._partition_state.get(node_id, [])

    def _build_reconstruct_fn(self, node_id: str):
        """Build a reconstruct_theta function for a given node."""
        def reconstruct(theta_hash: str, peer_vectors: list[StateVector]) -> dict | None:
            # Try to find the theta from peer nodes' stored state
            for peer in peer_vectors:
                if peer.theta_hash == theta_hash and peer.node_id != node_id:
                    # In real system: fetch full theta from peer
                    # In simulation: reconstruct a plausible theta
                    return {
                        "plan_stability_index": 0.8 + random.uniform(-0.1, 0.1),
                        "coherence_drop_rate": 0.05 + random.uniform(-0.02, 0.02),
                        "replanning_frequency": 0.1 + random.uniform(-0.05, 0.05),
                        "oscillation_index": 0.03 + random.uniform(-0.01, 0.01),
                    }
            return None
        return reconstruct

    def run(
        self,
        steps: int = 50,
        scenario: Scenario | None = None,
    ) -> ClusterTrace:
        """Run simulation for `steps` ticks."""
        scenario_name = scenario.name if scenario else "default"
        total_steps = steps

        oscillation_count = 0
        divergence_events = 0
        quarantine_events = 0
        applied_remote_count = 0
        rejected_remote_count = 0
        convergence_step: int | None = None

        node_snapshots: dict[str, list[dict]] = {n: [] for n in self.node_ids}
        theta_history: dict[str, list[tuple[int, str]]] = {n: [] for n in self.node_ids}
        key_events: list[dict] = []

        # Active faults per node
        active_faults: dict[str, str | None] = {n: None for n in self.node_ids}

        for step in range(steps):
            # Inject scenario faults
            if scenario:
                self._apply_scenario_faults(step, scenario, active_faults)


            for nid in self.node_ids:
                node = self.nodes[nid]

                # Determine fault injector
                fault_type = active_faults.get(nid)
                if fault_type == "degrade":
                    fault_fn = inject_degrade
                elif fault_type == "malicious":
                    fault_fn = inject_malicious_theta
                elif fault_type == "partition":
                    fault_fn = inject_partition
                else:
                    fault_fn = None

                # Patch reconstruct_theta for this node
                node._reconstruct_theta = self._build_reconstruct_fn(nid)

                # Tick
                metrics = node.tick(step, fault_fn=fault_fn)

                # Update peer reachability based on partition
                effective_peers = self._effective_peers(nid)
                for pid in list(node.gossip.peer_ids):
                    if pid not in effective_peers:
                        node.gossip.unregister_peer(pid)
                for pid in effective_peers:
                    if pid not in node.gossip.peer_ids:
                        node.gossip.register_peer(pid)

                # Snapshot
                snapshot = {
                    "step": step,
                    "theta_hash": node.theta_hash,
                    "vector_envelope": node.vector.envelope_state,
                    "drift_score": node.vector.drift_score,
                    "stability_score": node.vector.stability_score,
                    "is_degraded": node.is_degraded,
                    "is_quarantined": node.is_quarantined,
                    "oscillate": node.oscillate_count,
                    "metrics": {
                        "applied_remote": metrics.applied_remote,
                        "rejected_remote": metrics.rejected_remote,
                    },
                }
                node_snapshots[nid].append(snapshot)
                theta_history[nid].append((step, node.theta_hash))

                # Aggregate
                divergence_events += metrics.divergence_events
                quarantine_events += metrics.quarantine_events
                applied_remote_count += metrics.applied_remote
                rejected_remote_count += metrics.rejected_remote

            # Check convergence: all live nodes have same theta_hash
            live_nodes = [
                n for n in self.node_ids
                if not self.nodes[n].is_degraded and self._partition_state.get(n, [])
            ]
            if live_nodes:
                hashes = [self.nodes[n].theta_hash for n in live_nodes]
                if len(set(hashes)) == 1 and convergence_step is None:
                    convergence_step = step
                    key_events.append({
                        "step": step,
                        "type": "convergence",
                        "node_count": len(live_nodes),
                        "theta_hash": hashes[0],
                    })

            # Check for oscillation after consensus
            non_quorum_ticks = sum(
                1 for n in self.node_ids
                if self.nodes[n].oscillate_count > 0
            )
            if non_quorum_ticks > len(self.node_ids) * 0.5:
                oscillation_count += 1

        converged = convergence_step is not None and oscillation_count == 0
        return ClusterTrace(
            scenario_name=scenario_name,
            total_steps=total_steps,
            converged=converged,
            convergence_step=convergence_step,
            oscillation_count=oscillation_count,
            divergence_events=divergence_events,
            quarantine_events=quarantine_events,
            applied_remote_count=applied_remote_count,
            rejected_remote_count=rejected_remote_count,
            node_snapshots=node_snapshots,
            theta_history=theta_history,
            key_events=key_events,
        )

    def _apply_scenario_faults(
        self,
        step: int,
        scenario: Scenario,
        active_faults: dict[str, str | None],
    ) -> None:
        """Apply scenario-based fault injection."""
        if scenario.fault_step_start <= step:
            if scenario.fault_target and scenario.fault_type:
                active_faults[scenario.fault_target] = scenario.fault_type

        if scenario.fault_step_end is not None and step >= scenario.fault_step_end:
            if scenario.fault_target:
                active_faults[scenario.fault_target] = None

        if scenario.fault_type == "network_split" and scenario.partition_groups:
            if step == scenario.fault_step_start:
                self.apply_partition(scenario.partition_groups)
                active_faults[scenario.fault_target or ""] = "partition"
            elif scenario.fault_step_end and step >= scenario.fault_step_end:
                self.merge_partitions()
                if scenario.fault_target:
                    active_faults[scenario.fault_target] = None


# ── Scenario runner ─────────────────────────────────────────────────────────────


class ScenarioRunner:
    """Runs a suite of federation scenarios and produces a report."""

    def __init__(self, cluster: ClusterSimulator):
        self.cluster = cluster

    def run_scenario(
        self,
        scenario: Scenario,
        steps: int = 50,
    ) -> ClusterTrace:
        # Reset cluster state
        for nid in self.cluster.node_ids:
            self.cluster.nodes[nid]._degraded = False
            self.cluster._fault_state[nid] = False
        self.cluster.merge_partitions()

        return self.cluster.run(steps=steps, scenario=scenario)

    def run_all(self) -> dict[str, ClusterTrace]:
        scenarios = [
            Scenario(
                name="degradation_recovery",
                nodes=["node_a", "node_b", "node_c"],
                fault_type="degrade",
                fault_target="node_c",
                fault_step_start=5,
                fault_step_end=20,
            ),
            Scenario(
                name="split_brain_3v1",
                nodes=["node_a", "node_b", "node_c", "node_d"],
                fault_type="network_split",
                fault_target="node_d",
                fault_step_start=5,
                fault_step_end=25,
                partition_groups=[["node_a", "node_b", "node_c"], ["node_d"]],
            ),
            Scenario(
                name="malicious_theta_rejection",
                nodes=["node_a", "node_b", "node_c"],
                fault_type="malicious",
                fault_target="node_c",
                fault_step_start=8,
                fault_step_end=None,
            ),
        ]

        results = {}
        for s in scenarios:
            print(f"Running scenario: {s.name}...")
            trace = self.run_scenario(s, steps=50)
            results[s.name] = trace
            print(trace.summary())

        return results

    def print_report(self, results: dict[str, ClusterTrace]) -> None:
        print("\n" + "=" * 60)
        print("FEDERATION BOOTSTRAP — SCENARIO REPORT")
        print("=" * 60)

        all_passed = True
        for name, trace in results.items():
            status = "PASS" if trace.converged else "FAIL"
            if not trace.converged:
                all_passed = False
            osc = " ⚠️" if trace.oscillation_count > 0 else ""
            print(f"  [{status}] {name}{osc}")
            print(f"         converge_step={trace.convergence_step}  osc={trace.oscillation_count}"
                  f"  div={trace.divergence_events}  quar={trace.quarantine_events}")

        print("-" * 60)
        print(f"Overall: {'✅ ALL PASSED' if all_passed else '❌ FAILURES DETECTED'}")
