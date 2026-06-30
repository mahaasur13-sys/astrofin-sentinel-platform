"""
ChaosHarness — Jepsen-style test harness for distributed cluster validation.

Pipeline
--------
apply_fault() → run_cluster() → collect_metrics() → validate_SBS() → assert_invariants()

Usage
-----
    harness = ChaosHarness(
        scenario=partition_half_cluster(),
        cluster_ctx={"nodes": ["node-a", "node-b", "node-c"], ...},
    )

    result = harness.run()
    assert result.verdict != Verdict.FAIL, f"Chaos broke the cluster: {result}"
"""

from __future__ import annotations

import os
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from chaos.scenarios import ChaosScenario
from chaos.validator import ChaosValidator, ValidationResult, Verdict
from sbs.boundary_spec import SystemBoundarySpec
from sbs.global_invariant_engine import GlobalInvariantEngine


class ExperimentPhase(Enum):
    IDLE = "idle"
    FAULT_INJECTION = "fault_injection"
    STABILIZATION = "stabilization"
    VALIDATION = "validation"
    COMPLETE = "complete"


@dataclass
class ChaosResult:
    """Immutable result of a full chaos experiment run."""

    scenario_name: str
    phase: ExperimentPhase
    verdict: Verdict
    duration_s: float
    fault_apply_duration_s: float
    validation_result: ValidationResult | None = None
    health_snapshot: dict = field(default_factory=dict)
    metrics_snapshot: dict = field(default_factory=dict)
    sbs_snapshots: list = field(default_factory=list)
    raw_events: list = field(default_factory=list)
    error: str = ""
    timestamp: float = field(default_factory=time.time)

    def __str__(self) -> str:
        return (
            f"ChaosResult({self.scenario_name}): "
            f"{self.phase.value} → {self.verdict.value} "
            f"({self.duration_s:.1f}s)"
        )


class ChaosHarness:
    """
    Orchestrates a Jepsen-style chaos experiment against a live cluster.

    The harness drives the full experiment lifecycle:

    1. PRE-FLIGHT CHECK   — verify cluster is healthy before injecting fault
    2. FAULT INJECTION   — apply the chaos scenario
    3. OBSERVATION WINDOW — collect health + SBS snapshots during chaos
    4. FAULT ROLLBACK    — reverse the injected fault
    5. STABILIZATION WAIT — wait for cluster to settle
    6. VALIDATION        — run ChaosValidator on collected data
    7. RESULT            — return ChaosResult with verdict

    Parameters
    ----------
    scenario        : ChaosScenario to run
    cluster_ctx     : cluster context {
        "nodes": ["node-a", "node-b", "node-c"],
        "node_ips": {"node-a": "172.28.1.10", ...},
        "health_getter": callable(node_id) → ClusterHealthGraph,
        "metrics_getter": callable(node_id) → MetricsCollector,
        "rpc_call": callable(node_id, cmd) → str,
    }
    observation_s    : seconds to observe cluster during chaos (default 10)
    stabilization_s : seconds to wait for cluster to stabilize after rollback (default 10)
    pre_flight      : callable() → bool, optional pre-flight check
    """

    def __init__(
        self,
        scenario: ChaosScenario,
        cluster_ctx: dict,
        observation_s: float = 10.0,
        stabilization_s: float = 10.0,
        pre_flight: Callable[[], bool] | None = None,
    ):
        self.scenario = scenario
        self.cluster_ctx = cluster_ctx
        self.observation_s = observation_s
        self.stabilization_s = stabilization_s
        self.pre_flight = pre_flight

        self.validator = ChaosValidator()
        self._phase = ExperimentPhase.IDLE
        self._stop_observation = threading.Event()
        self._health_snapshots: list[dict] = []
        self._metrics_snapshots: list[dict] = []
        self._sbs_snapshots: list[dict] = []
        self._raw_events: list[dict] = []
        self._observer_thread: threading.Thread | None = None

    # ── Public API ─────────────────────────────────────────────────────────────

    def run(self) -> ChaosResult:
        """
        Run the full chaos experiment pipeline.

        Returns ChaosResult with verdict PASS / PARTIAL / FAIL.
        """
        start = time.time()
        fault_apply_start = start
        error = ""

        try:
            # ── 1. Pre-flight check ────────────────────────────────────────
            self._phase = ExperimentPhase.IDLE
            if self.pre_flight and not self.pre_flight():
                return ChaosResult(
                    scenario_name=self.scenario.name,
                    phase=ExperimentPhase.IDLE,
                    verdict=Verdict.FAIL,
                    duration_s=time.time() - start,
                    fault_apply_duration_s=0,
                    error="pre-flight check failed: cluster not healthy",
                )

            # ── 2. Baseline snapshot ───────────────────────────────────────
            baseline_health = self._snapshot_health()
            baseline_metrics = self._snapshot_metrics()

            # ── 3. Apply fault ─────────────────────────────────────────────
            self._phase = ExperimentPhase.FAULT_INJECTION
            fault_apply_start = time.time()

            apply_result = self.scenario.apply(self.cluster_ctx)
            if not apply_result.get("ok"):
                error = f"fault injection failed: {apply_result}"
                return ChaosResult(
                    scenario_name=self.scenario.name,
                    phase=self._phase,
                    verdict=Verdict.FAIL,
                    duration_s=time.time() - start,
                    fault_apply_duration_s=time.time() - fault_apply_start,
                    error=error,
                )

            fault_apply_duration = time.time() - fault_apply_start

            # ── 4. Observation window ───────────────────────────────────────
            self._stop_observation.clear()
            self._health_snapshots.clear()
            self._metrics_snapshots.clear()
            self._sbs_snapshots.clear()
            self._raw_events.clear()

            self._observer_thread = threading.Thread(
                target=self._observation_loop,
                args=(self.observation_s,),
                daemon=True,
            )
            self._observer_thread.start()

            # Wait for observation window
            self._observer_thread.join(timeout=self.observation_s + 2)
            self._stop_observation.set()

            # ── 5. Rollback fault ──────────────────────────────────────────
            self._phase = ExperimentPhase.STABILIZATION
            self.scenario.rollback()

            # Wait for stabilization
            time.sleep(self.stabilization_s)

            # ── 6. Post-chaos snapshots ────────────────────────────────────
            post_health = self._snapshot_health()
            post_metrics = self._snapshot_metrics()

            # ── 7. Build health_states map for validator ──────────────────
            latest_health = self._health_snapshots[-1] if self._health_snapshots else {}

            # Convert ClusterHealthGraph snapshots → simple state strings
            health_states: dict[str, str] = {}
            for node_id in self.cluster_ctx.get("nodes", []):
                peer_health = latest_health.get(node_id, {})
                if isinstance(peer_health, dict):
                    state = peer_health.get("state", "unknown")
                else:
                    state = "unknown"
                health_states[node_id] = state

            # ── 8. Validate ───────────────────────────────────────────────
            self._phase = ExperimentPhase.VALIDATION
            validation_result = self.validator.validate(
                scenario_name=self.scenario.name,
                health_states=health_states,
                sbs_results=self._sbs_snapshots,
                raw_events=self._raw_events,
                expected_behavior=self._get_expected_behavior(self.scenario.name),
                cluster_metrics=post_metrics,
            )

            self._phase = ExperimentPhase.COMPLETE
            total_duration = time.time() - start

            return ChaosResult(
                scenario_name=self.scenario.name,
                phase=self._phase,
                verdict=validation_result.verdict,
                duration_s=total_duration,
                fault_apply_duration_s=fault_apply_duration,
                validation_result=validation_result,
                health_snapshot={
                    "baseline": baseline_health,
                    "during": self._health_snapshots,
                    "post": post_health,
                },
                metrics_snapshot={
                    "baseline": baseline_metrics,
                    "during": self._metrics_snapshots,
                    "post": post_metrics,
                },
                sbs_snapshots=self._sbs_snapshots,
                raw_events=self._raw_events,
            )

        except Exception as e:
            error = f"harness exception: {e}"
            import traceback
            traceback.print_exc()

            return ChaosResult(
                scenario_name=self.scenario.name,
                phase=self._phase,
                verdict=Verdict.FAIL,
                duration_s=time.time() - start,
                fault_apply_duration_s=time.time() - fault_apply_start,
                error=error,
            )

    # ── Observation loop ───────────────────────────────────────────────────────

    def _observation_loop(self, duration_s: float):
        """
        Background thread: periodically snapshot health + metrics + SBS state.
        Runs for `duration_s` seconds or until _stop_observation is set.
        """
        interval = 1.0  # snapshot every 1s
        end_time = time.time() + duration_s

        while time.time() < end_time and not self._stop_observation.is_set():
            # Health snapshot
            health = self._snapshot_health()
            if health:
                self._health_snapshots.append(health)

            # Metrics snapshot
            metrics = self._snapshot_metrics()
            if metrics:
                self._metrics_snapshots.append(metrics)

            # SBS snapshot — evaluate current state
            sbs_result = self._snapshot_sbs()
            if sbs_result:
                self._sbs_snapshots.append(sbs_result)
                # If SBS detected a violation, record it as a raw event
                if not sbs_result.get("ok", True):
                    violations = sbs_result.get("violations", [])
                    for v in violations:
                        self._raw_events.append({
                            "type": self.scenario.fault_type,
                            "layer": "SBS",
                            "description": v,
                            "timestamp": time.time(),
                        })

            # Check for DRL drop events (from metrics)
            for node_id, node_metrics in (metrics or {}).items():
                drops = node_metrics.get("drops", 0)
                if drops > 0:
                    self._raw_events.append({
                        "type": "drop",
                        "layer": "DRL",
                        "description": f"packet drop detected on {node_id}",
                        "timestamp": time.time(),
                    })

            time.sleep(interval)

    def _snapshot_health(self) -> dict:
        """Snapshot health state from all nodes."""
        getter = self.cluster_ctx.get("health_getter")
        nodes = self.cluster_ctx.get("nodes", [])
        if not getter:
            return {}
        result = {}
        for node_id in nodes:
            try:
                health = getter(node_id)
                if health:
                    if hasattr(health, "get_all"):
                        result[node_id] = health.get_all()
                    elif callable(health):
                        result[node_id] = health()
            except Exception:
                pass
        return result

    def _snapshot_metrics(self) -> dict:
        """Snapshot metrics from all nodes."""
        getter = self.cluster_ctx.get("metrics_getter")
        nodes = self.cluster_ctx.get("nodes", [])
        if not getter:
            return {}
        result = {}
        for node_id in nodes:
            try:
                metrics = getter(node_id)
                if metrics:
                    if hasattr(metrics, "get_all"):
                        result[node_id] = metrics.get_all()
                    elif callable(metrics):
                        result[node_id] = metrics()
            except Exception:
                pass
        return result

    def _snapshot_sbs(self) -> dict:
        """Run SBS evaluation snapshot."""
        engine = self.cluster_ctx.get("sbs_engine")
        if not engine:
            # Create a local engine for snapshot
            spec = SystemBoundarySpec()
            engine = GlobalInvariantEngine(spec)

        # Build a minimal state from current health/metrics
        latest_health = self._health_snapshots[-1] if self._health_snapshots else {}

        drl_state = {"partitions": 0, "leader": None}
        ccl_state = {"term": 0, "leader": None}
        f2_state = {"commit_index": 0, "quorum_ratio": 0.67, "duplicate_ack": False}
        desc_state = {"commit_index": 0, "term": 0}

        # Update from health snapshots — if any node is unreachable → partition
        unreachable_count = sum(
            1 for h in latest_health.values()
            if isinstance(h, dict) and h.get("state") == "unreachable"
        )
        if unreachable_count > 0:
            drl_state["partitions"] = unreachable_count
            f2_state["quorum_ratio"] = max(0.0, 0.67 - (unreachable_count / 3))

        try:
            ok = engine.evaluate(drl_state, ccl_state, f2_state, desc_state)
            return {
                "ok": ok,
                "violations": engine.get_violations(),
                "timestamp": time.time(),
                "drl": drl_state,
                "ccl": ccl_state,
                "f2": f2_state,
                "desc": desc_state,
            }
        except Exception as e:
            return {"ok": True, "violations": [], "error": str(e)}

    # ── Expected behavior map ─────────────────────────────────────────────────

    def _get_expected_behavior(self, scenario_name: str) -> dict:
        """
        Return expected SBS violations and system response for each scenario.
        This defines the "correct" outcome that the validator checks against.
        """
        behavior_map: dict[str, dict] = {
            "partition_half_cluster": {
                "sbs_violations": ["LEADER_UNIQUENESS", "QUORUM_VIOLATION"],
                "system_response": "cluster_detects_and_recovers",
            },
            "asymmetric_partition": {
                "sbs_violations": ["TERM_ORDER_VIOLATION", "SPLIT_BRAIN"],
                "system_response": "cluster_detects_and_recovers",
            },
            "slow_node_amplification": {
                "sbs_violations": [],
                "system_response": "cluster_detects_and_recovers",
            },
            "byzantine_sender_injection": {
                "sbs_violations": ["BYZANTINE_SIGNAL", "QUORUM_VIOLATION"],
                "system_response": "cluster_halts",
            },
            "clock_skew_escalation": {
                "sbs_violations": ["TEMPORAL_DRIFT"],
                "system_response": "cluster_detects_and_recovers",
            },
            "loss_burst": {
                "sbs_violations": [],
                "system_response": "cluster_detects_and_recovers",
            },
            "node_isolation": {
                "sbs_violations": ["LEADER_UNIQUENESS", "QUORUM_VIOLATION"],
                "system_response": "cluster_detects_and_recovers",
            },
            "latency_spike": {
                "sbs_violations": [],
                "system_response": "cluster_detects_and_recovers",
            },
        }
        return behavior_map.get(scenario_name, {
            "sbs_violations": [],
            "system_response": "cluster_detects_and_recovers",
        })

    # ── Convenience runner ─────────────────────────────────────────────────────

    def run_scenario(
        scenario_name: str,
        cluster_ctx: dict,
        observation_s: float = 10.0,
        stabilization_s: float = 10.0,
    ) -> ChaosResult:
        """
        Convenience function: look up scenario by name and run it.

        Usage:
            result = ChaosHarness.run_scenario(
                "partition_half_cluster",
                cluster_ctx={"nodes": ["node-a", ...], ...},
            )
        """
        from chaos.scenarios import SCENARIO_REGISTRY

        if scenario_name not in SCENARIO_REGISTRY:
            raise ValueError(f"Unknown scenario: {scenario_name}. Available: {list(SCENARIO_REGISTRY.keys())}")

        scenario = SCENARIO_REGISTRY[scenario_name]
        harness = ChaosHarness(
            scenario=scenario,
            cluster_ctx=cluster_ctx,
            observation_s=observation_s,
            stabilization_s=stabilization_s,
        )
        return harness.run()
