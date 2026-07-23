"""
Metrics Schema v7.0 — Core metrics contract for ATOMFederationOS.

These metrics are the OBSERVABLE CONTRACT between all OS subsystems.
Every node emits them; the cluster-level metrics are aggregations.

Naming convention:
  atom_<subsystem>_<metric_type>_<unit>

Types:
  gauge       — instantaneous value (node-level)
  counter     — monotonically increasing (node-level)
  histogram   — latency/interval distributions (node-level)
  derived     — cluster-level aggregations (Prometheus recording rules)

Labels (always present):
  node_id     — originating node
  subsystem   — sbs | lattice | coherence | healer | quorum | rpc
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class Subsystem(Enum):
    SBS = "sbs"
    LATTICE = "lattice"
    COHERENCE = "coherence"
    HEALER = "healer"
    QUORUM = "quorum"
    RPC = "rpc"
    CLUSTER = "cluster"


class MetricType(Enum):
    GAUGE = "gauge"
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    DERIVED = "derived"


# ── Core Metrics Definitions ────────────────────────────────────────────────────

METRICS_SCHEMA: dict[str, dict] = {

    # ── SBS ──────────────────────────────────────────────────────────────────
    "atom_sbs_violations_total": {
        "type": "counter",
        "subsystem": "sbs",
        "unit": "violations",
        "description": "Total SBS boundary violations detected",
        "labels": ["node_id", "violation_type"],  # violation_type: boundary | consistency | timing
        "must_have": True,
    },
    "atom_sbs_check_duration_seconds": {
        "type": "histogram",
        "subsystem": "sbs",
        "unit": "seconds",
        "description": "Time to execute one SBS consistency check cycle",
        "labels": ["node_id"],
        "buckets": [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
        "must_have": True,
    },
    "atom_sbs_invariant_count": {
        "type": "gauge",
        "subsystem": "sbs",
        "unit": "invariants",
        "description": "Number of active SBS invariants being monitored",
        "labels": ["node_id"],
        "must_have": True,
    },

    # ── Coherence ─────────────────────────────────────────────────────────────
    "atom_coherence_drift_score": {
        "type": "gauge",
        "subsystem": "coherence",
        "unit": "score",
        "description": "Self-model vs ground-truth divergence (0.0=perfect, 1.0=degraded)",
        "labels": ["node_id"],
        "range": [0.0, 1.0],
        "SLO_threshold": 0.1,
        "must_have": True,
    },
    "atom_self_model_error": {
        "type": "gauge",
        "subsystem": "coherence",
        "unit": "errors",
        "description": "Count of self-model assertions that failed",
        "labels": ["node_id"],
        "must_have": True,
    },
    "atom_coherence_check_duration_seconds": {
        "type": "histogram",
        "subsystem": "coherence",
        "unit": "seconds",
        "description": "Time to compute coherence check",
        "labels": ["node_id"],
        "buckets": [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
        "must_have": True,
    },

    # ── Lattice ───────────────────────────────────────────────────────────────
    "atom_lattice_decisions_total": {
        "type": "counter",
        "subsystem": "lattice",
        "unit": "decisions",
        "description": "Total routing/placement decisions made by lattice",
        "labels": ["node_id", "decision_type"],  # decision_type: routing | placement | failover
        "must_have": True,
    },
    "atom_lattice_decision_duration_seconds": {
        "type": "histogram",
        "subsystem": "lattice",
        "unit": "seconds",
        "description": "Time for lattice to reach a decision",
        "labels": ["node_id"],
        "buckets": [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
        "must_have": True,
    },
    "atom_lattice_active_nodes": {
        "type": "gauge",
        "subsystem": "lattice",
        "unit": "nodes",
        "description": "Number of nodes currently in the lattice",
        "labels": ["node_id"],
        "must_have": True,
    },

    # ── Healer ───────────────────────────────────────────────────────────────
    "atom_healer_repair_total": {
        "type": "counter",
        "subsystem": "healer",
        "unit": "repairs",
        "description": "Total repair actions performed by healer",
        "labels": ["node_id", "repair_type"],  # repair_type: sbs_fix | quorum_heal | split_brain | state_reconcile
        "must_have": True,
    },
    "atom_healer_repair_duration_seconds": {
        "type": "histogram",
        "subsystem": "healer",
        "unit": "seconds",
        "description": "Repair action duration",
        "labels": ["node_id", "repair_type"],
        "buckets": [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
        "SLO_threshold": 5.0,  # repair should complete within 5s
        "must_have": True,
    },
    "atom_healer_queue_depth": {
        "type": "gauge",
        "subsystem": "healer",
        "unit": "items",
        "description": "Number of pending repair tasks in healer queue",
        "labels": ["node_id"],
        "must_have": True,
    },

    # ── Quorum ────────────────────────────────────────────────────────────────
    "atom_quorum_health": {
        "type": "gauge",
        "subsystem": "quorum",
        "unit": "score",
        "description": "Quorum health score (0.0=lost, 1.0=full)",
        "labels": ["node_id"],
        "range": [0.0, 1.0],
        "SLO_threshold": 0.67,  # >2/3 nodes required for quorum
        "must_have": True,
    },
    "atom_quorum_members": {
        "type": "gauge",
        "subsystem": "quorum",
        "unit": "nodes",
        "description": "Current number of quorum members",
        "labels": ["node_id"],
        "must_have": True,
    },
    "atom_quorum_vote_requests_total": {
        "type": "counter",
        "subsystem": "quorum",
        "unit": "requests",
        "description": "Total vote requests received",
        "labels": ["node_id"],
        "must_have": True,
    },

    # ── RPC ────────────────────────────────────────────────────────────────────
    "atom_rpc_requests_total": {
        "type": "counter",
        "subsystem": "rpc",
        "unit": "requests",
        "description": "Total RPC requests sent",
        "labels": ["node_id", "peer_id", "method"],
        "must_have": True,
    },
    "atom_rpc_errors_total": {
        "type": "counter",
        "subsystem": "rpc",
        "unit": "errors",
        "description": "Total RPC errors",
        "labels": ["node_id", "peer_id", "method", "error_type"],
        "must_have": True,
    },
    "atom_rpc_latency_seconds": {
        "type": "histogram",
        "subsystem": "rpc",
        "unit": "seconds",
        "description": "RPC roundtrip latency",
        "labels": ["node_id", "peer_id", "method"],
        "buckets": [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
        "SLO_threshold": 0.5,  # P99 < 500ms
        "must_have": True,
    },
    "atom_rpc_latency_p99_seconds": {
        "type": "derived",
        "subsystem": "rpc",
        "unit": "seconds",
        "description": "P99 RPC latency (cluster-level, Prometheus recording rule)",
        "labels": ["node_id", "peer_id"],
        "SLO_threshold": 0.5,
        "must_have": False,  # derived, not directly emitted
    },

    # ── Cluster-level (derived) ──────────────────────────────────────────────
    "atom_cluster_healthy_nodes": {
        "type": "derived",
        "subsystem": "cluster",
        "unit": "nodes",
        "description": "Number of currently healthy nodes",
        "labels": [],
        "aggregation": "sum",
        "SLO_threshold": 0.99,  # 99% availability
        "must_have": True,
    },
    "atom_cluster_total_nodes": {
        "type": "derived",
        "subsystem": "cluster",
        "unit": "nodes",
        "description": "Total configured nodes",
        "labels": [],
        "aggregation": "max",
        "must_have": True,
    },
    "atom_cluster_availability": {
        "type": "derived",
        "subsystem": "cluster",
        "unit": "ratio",
        "description": "Cluster availability ratio",
        "labels": [],
        "formula": "atom_cluster_healthy_nodes / atom_cluster_total_nodes",
        "SLO_threshold": 0.99,
        "must_have": True,
    },
    "atom_cluster_coherence_drift_score_avg": {
        "type": "derived",
        "subsystem": "cluster",
        "unit": "score",
        "description": "Average coherence drift across cluster",
        "labels": [],
        "aggregation": "avg",
        "SLO_threshold": 0.1,
        "must_have": True,
    },

    # ── Replay ─────────────────────────────────────────────────────────────────
    "atom_replay_events_applied_total": {
        "type": "counter",
        "subsystem": "replay",
        "unit": "events",
        "description": "Total replay events applied by ReplayEngine",
        "labels": ["replayed_event_type"],
        "must_have": True,
    },
    "atom_replay_lag_ms": {
        "type": "histogram",
        "subsystem": "replay",
        "unit": "milliseconds",
        "description": "Replay lag: real elapsed time vs event timeline elapsed time",
        "labels": ["replayed_event_type"],
        "buckets": [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 50.0, 100.0],
        "must_have": True,
    },
}


@dataclass
class MetricDef:
    name: str
    type: Literal["gauge", "counter", "histogram", "derived"]
    subsystem: str
    unit: str
    description: str
    labels: list[str] = field(default_factory=list)
    buckets: list[float] = field(default_factory=list)
    range: tuple[float, float] | None = None
    SLO_threshold: float | None = None
    must_have: bool = True
    aggregation: str | None = None
    formula: str | None = None


def get_metric_def(name: str) -> MetricDef | None:
    raw = METRICS_SCHEMA.get(name)
    if raw is None:
        return None
    return MetricDef(name=name, **raw)


def get_mandatory_metrics() -> list[str]:
    """Return list of all must_have=True metric names."""
    return [n for n, d in METRICS_SCHEMA.items() if d.get("must_have")]


def validate_metric_labels(name: str, labels: dict) -> list[str]:
    """
    Validate that a metric emission has correct labels.
    Returns list of errors (empty = valid).
    """
    defn = METRICS_SCHEMA.get(name)
    if defn is None:
        return [f"Unknown metric: {name}"]
    errors = []
    required = set(defn.get("labels", []))
    provided = set(labels.keys())
    missing = required - provided
    extra = provided - required
    if missing:
        errors.append(f"Missing required labels for {name}: {missing}")
    if extra:
        errors.append(f"Unexpected labels for {name}: {extra}")
    return errors
