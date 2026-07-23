"""
cross_layer_invariant_engine.py
==============================
Formal invariant verification engine that spans all ATOM layers.

Four core invariants verified:

    I1  cluster_state == replay_state     (StateReconstructor ↔ actual cluster)
    I2  causal_graph(execution) == causal_graph(replay)
    I3  SBS violations identical in both domains
    I4  drift_score(execution) == drift_score(replay)

References:
    - sbs/global_invariant_engine.py  — DRL/CCL/F2/DESC layer aggregation
    - failure_replay/replay_engine.py — StateReconstructor
    - consistency/execution_replay_bridge.py — bridge checks
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

# ── Invariant result types ──────────────────────────────────────────────────

@dataclass
class InvariantResult:
    """Result of a single invariant check."""
    invariant_id: str           # I1 | I2 | I3 | I4
    passed: bool
    exec_value: Any
    replay_value: Any
    drift: float                # numeric drift between exec and replay
    details: str
    ts_ns: int = field(default_factory=lambda: time.time_ns())


@dataclass
class CrossLayerReport:
    """Full cross-layer invariant verification report."""
    i1_cluster_vs_replay: InvariantResult
    i2_causal_dag_equivalence: InvariantResult
    i3_sbs_violation_equivalence: InvariantResult
    i4_drift_score_equivalence: InvariantResult
    all_passed: bool
    total_checks: int = 4
    passed_checks: int = 0
    ts_ns: int = field(default_factory=lambda: time.time_ns())
    duration_ns: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "i1": _inv_result(self.i1_cluster_vs_replay),
            "i2": _inv_result(self.i2_causal_dag_equivalence),
            "i3": _inv_result(self.i3_sbs_violation_equivalence),
            "i4": _inv_result(self.i4_drift_score_equivalence),
            "all_passed": self.all_passed,
            "total": self.total_checks,
            "passed": self.passed_checks,
            "duration_s": self.duration_ns / 1e9,
        }


def _inv_result(r: InvariantResult) -> dict[str, Any]:
    return {
        "invariant_id": r.invariant_id,
        "passed": r.passed,
        "drift": r.drift,
        "details": r.details,
    }


# ── Causal DAG ──────────────────────────────────────────────────────────────

@dataclass
class CausalDAG:
    """Lightweight causal ancestry graph for events."""
    nodes: dict[str, dict] = field(default_factory=dict)

    def add_event(
        self,
        event_id: str,
        causal_parents: list[str] | None = None,
        payload: dict | None = None,
    ) -> None:
        self.nodes[event_id] = {
            "parents": set(causal_parents) if causal_parents else set(),
            "payload": payload or {},
        }

    def ancestors(self, event_id: str, depth_limit: int = 50) -> set[str]:
        """Return all causal ancestors of an event (transitive closure)."""
        if event_id not in self.nodes:
            return set()
        result: set[str] = set()
        queue = list(self.nodes[event_id]["parents"])
        visited = 0
        while queue and visited < depth_limit:
            node = queue.pop()
            if node not in result:
                result.add(node)
                queue.extend(self.nodes.get(node, {}).get("parents", []))
                visited += 1
        return result

    def is_identical(self, other: CausalDAG) -> tuple[bool, str]:
        """
        Check if two DAGs are structurally identical.
        Returns (is_identical, reason).
        """
        ids_self = set(self.nodes.keys())
        ids_other = set(other.nodes.keys())

        if ids_self != ids_other:
            return False, f"node_ids differ: only_in_self={ids_self - ids_other}, only_in_other={ids_other - ids_self}"

        for eid in ids_self:
            parents_self = self.nodes[eid].get("parents", set())
            parents_other = other.nodes[eid].get("parents", set())
            if parents_self != parents_other:
                return False, f"causal_parents differ at {eid[:8]}: self={parents_self}, other={parents_other}"

        return True, "identical"


# ── CrossLayerInvariantEngine ───────────────────────────────────────────────

class CrossLayerInvariantEngine:
    """
    Verifies formal invariants I1–I4 across execution and replay domains.

    Usage:
        engine = CrossLayerInvariantEngine(
            cluster_state_fn=get_cluster_state,      # () -> dict
            replay_state_fn=state_reconstructor.get_state,  # () -> dict
        )
        report = engine.verify(exec_events, replay_events)
        assert report.all_passed, f"Invariant violations: {report.to_dict()}"
    """

    def __init__(
        self,
        cluster_state_fn: Callable[[], dict],
        replay_state_fn: Callable[[], dict],
        get_drift_score_fn: Callable[[str], float] | None = None,
        get_sbs_count_fn: Callable[[str], int] | None = None,
    ):
        """
        Args:
            cluster_state_fn:  fn() returning live cluster state dict
            replay_state_fn:   fn() returning StateReconstructor.get_state()
            get_drift_score_fn: fn(node_id) -> float, optional
            get_sbs_count_fn:   fn(node_id) -> int,   optional
        """
        self._cluster_fn = cluster_state_fn
        self._replay_fn = replay_state_fn
        self._drift_fn = get_drift_score_fn or (lambda _: 0.0)
        self._sbs_fn = get_sbs_count_fn or (lambda _: 0)
        self._lock = threading.Lock()
        self._last_report: CrossLayerReport | None = None

    # ── I1: cluster_state == replay_state ─────────────────────────────────

    def _check_i1(self) -> InvariantResult:
        """I1: ClusterState and StateReconstructor must produce identical results."""
        try:
            cluster = self._cluster_fn()
            replay = self._replay_fn()
        except Exception as e:
            return InvariantResult(
                invariant_id="I1",
                passed=False,
                exec_value=None,
                replay_value=None,
                drift=float("inf"),
                details=f"Failed to retrieve state: {e}",
            )

        # Compare node states (ignore ordering of independent keys)
        drift = self._dict_drift(cluster, replay)

        # Structural diff
        cluster_nodes = cluster.get("nodes", {})
        replay_nodes = replay.get("nodes", {})
        node_drift = len(set(cluster_nodes.keys()) ^ set(replay_nodes.keys()))

        passed = drift < 1e-9 and node_drift == 0

        return InvariantResult(
            invariant_id="I1",
            passed=passed,
            exec_value=cluster,
            replay_value=replay,
            drift=drift,
            details=(
                "I1_PASS" if passed
                else f"node_drift={node_drift}, state_drift={drift:.2e}"
            ),
        )

    # ── I2: causal_graph equivalence ──────────────────────────────────────

    def _check_i2(
        self,
        exec_events: list[Any],
        replay_events: list[Any],
    ) -> InvariantResult:
        """
        I2: Causal DAG from execution must be identical to causal DAG from replay.
        Both event sequences are walked to build parent-child relationships.
        """
        dag_exec = CausalDAG()
        dag_replay = CausalDAG()

        for ev in exec_events:
            parents = getattr(ev, "payload", {}).get("causal_parents", [])
            if isinstance(parents, str):
                parents = [parents] if parents else []
            dag_exec.add_event(
                event_id=getattr(ev, "event_id", str(getattr(ev, "ts", 0))),
                causal_parents=parents,
                payload=getattr(ev, "payload", {}),
            )

        for ev in replay_events:
            parents = getattr(ev, "payload", {}).get("causal_parents", [])
            if isinstance(parents, str):
                parents = [parents] if parents else []
            dag_replay.add_event(
                event_id=getattr(ev, "event_id", str(getattr(ev, "ts", 0))),
                causal_parents=parents,
                payload=getattr(ev, "payload", {}),
            )

        identical, reason = dag_exec.is_identical(dag_replay)

        return InvariantResult(
            invariant_id="I2",
            passed=identical,
            exec_value=len(dag_exec.nodes),
            replay_value=len(dag_replay.nodes),
            drift=0.0 if identical else 1.0,
            details=reason,
        )

    # ── I3: SBS violations identical ──────────────────────────────────────

    def _check_i3(self) -> InvariantResult:
        """
        I3: The set/count of SBS violations in cluster must match replay.
        Both domains must detect the same SBS events.
        """
        cluster = self._cluster_fn()
        replay = self._replay_fn()

        cluster_nodes = cluster.get("nodes", {})
        replay_nodes = replay.get("nodes", {})

        # Sum sbs_violations across all nodes
        def sum_sbs(nodes: dict) -> int:
            return sum(ns.get("sbs_violations", 0) for ns in nodes.values())

        exec_count = sum_sbs(cluster_nodes)
        replay_count = sum_sbs(replay_nodes)

        # Also compare violation types per node
        exec_violations = {
            nid: ns.get("last_violation_type", "unknown")
            for nid, ns in cluster_nodes.items()
            if ns.get("sbs_violations", 0) > 0
        }
        replay_violations = {
            nid: ns.get("last_violation_type", "unknown")
            for nid, ns in replay_nodes.items()
            if ns.get("sbs_violations", 0) > 0
        }

        count_drift = abs(exec_count - replay_count)
        type_drift = len(set(exec_violations.items()) ^ set(replay_violations.items()))
        passed = count_drift == 0 and type_drift == 0

        return InvariantResult(
            invariant_id="I3",
            passed=passed,
            exec_value=exec_count,
            replay_value=replay_count,
            drift=float(count_drift + type_drift),
            details=(
                "I3_PASS" if passed
                else f"count_drift={count_drift}, type_drift={type_drift}"
            ),
        )

    # ── I4: drift_score equivalence ───────────────────────────────────────

    def _check_i4(self) -> InvariantResult:
        """
        I4: Coherence drift score must be identical between execution and replay.
        Drift score per node must match across domains.
        """
        cluster = self._cluster_fn()
        replay = self._replay_fn()

        cluster_nodes = cluster.get("nodes", {})
        replay_nodes = replay.get("nodes", {})

        def drift_scores(nodes: dict) -> dict[str, float]:
            return {
                nid: ns.get("coherence_drift_score", 0.0)
                for nid, ns in nodes.items()
            }

        exec_scores = drift_scores(cluster_nodes)
        replay_scores = drift_scores(replay_nodes)

        all_ids = set(exec_scores) | set(replay_scores)
        max_drift = 0.0
        for nid in all_ids:
            e_score = exec_scores.get(nid, 0.0)
            r_score = replay_scores.get(nid, 0.0)
            max_drift = max(max_drift, abs(e_score - r_score))

        passed = max_drift < 1e-9

        return InvariantResult(
            invariant_id="I4",
            passed=passed,
            exec_value=exec_scores,
            replay_value=replay_scores,
            drift=max_drift,
            details=(
                "I4_PASS" if passed
                else f"max_drift_score={max_drift:.2e}"
            ),
        )

    # ── Full verification ─────────────────────────────────────────────────

    def verify(
        self,
        exec_events: list[Any],
        replay_events: list[Any],
    ) -> CrossLayerReport:
        """
        Run all four invariant checks and produce a CrossLayerReport.
        """
        start_ns = time.time_ns()

        i1 = self._check_i1()
        i2 = self._check_i2(exec_events, replay_events)
        i3 = self._check_i3()
        i4 = self._check_i4()

        duration_ns = time.time_ns() - start_ns
        passed = sum(1 for r in [i1, i2, i3, i4] if r.passed)

        report = CrossLayerReport(
            i1_cluster_vs_replay=i1,
            i2_causal_dag_equivalence=i2,
            i3_sbs_violation_equivalence=i3,
            i4_drift_score_equivalence=i4,
            all_passed=passed == 4,
            passed_checks=passed,
            duration_ns=duration_ns,
        )

        with self._lock:
            self._last_report = report

        return report

    def get_last_report(self) -> CrossLayerReport | None:
        with self._lock:
            return self._last_report

    # ── Utilities ───────────────────────────────────────────────────────────

    @staticmethod
    def _dict_drift(a: dict, b: dict, path: str = "") -> float:
        """
        Compute normalized float drift between two nested dicts.
        Returns 0.0 for identical, >0 for different (max 1.0).
        """
        drift = 0.0
        keys = set(a.keys()) | set(b.keys())
        if not keys:
            return 0.0

        for k in keys:
            new_path = f"{path}.{k}" if path else k
            if k not in a:
                drift += 1.0
                continue
            if k not in b:
                drift += 1.0
                continue
            va, vb = a[k], b[k]
            if isinstance(va, dict) and isinstance(vb, dict):
                drift += CrossLayerInvariantEngine._dict_drift(va, vb, new_path)
            elif isinstance(va, (int, float)) and isinstance(vb, (int, float)):
                max_val = max(abs(va), abs(vb), 1e-9)
                drift += abs(va - vb) / max_val
            else:
                if va != vb:
                    drift += 1.0

        return drift / len(keys)  # normalize by number of keys
