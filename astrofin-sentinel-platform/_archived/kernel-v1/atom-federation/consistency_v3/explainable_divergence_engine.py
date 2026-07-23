"""
explainable_divergence_engine.py
================================
v7.2 — ExplainableDivergenceEngine: maps fingerprint mismatch → causal root cause graph.

Problem this solves:
  fingerprint mismatch → "diverged" (opaque)
  causal_semantic_space → "diverged in axis X" (actionable)

This layer adds EXPLAINABILITY:
  - Root cause chain: which domain → which field → which causal dependency
  - Causal dependency graph (DAG) of divergence propagation
  - Mitigation hint per root cause
  - Severity scoring (0-10) based on divergence magnitude and propagation depth
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DivergenceRootCause:
    """One node in the causal root-cause graph."""

    domain: str
    field: str
    exec_value: Any = None
    replay_value: Any = None
    diff_magnitude: float = 0.0
    propagation_depth: int = 0
    severity_score: float = 0.0
    mitigation_hint: str = ""
    is_root: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "field": self.field,
            "exec_value": self.exec_value,
            "replay_value": self.replay_value,
            "diff_magnitude": self.diff_magnitude,
            "propagation_depth": self.propagation_depth,
            "severity_score": self.severity_score,
            "mitigation_hint": self.mitigation_hint,
            "is_root": self.is_root,
        }


@dataclass
class DivergenceRootCauseGraph:
    """
    DAG of divergence propagation across domains.

    Nodes: DivergenceRootCause entries
    Edges: propagation relationships (cause → affected domain/field)
    """

    nodes: dict[str, DivergenceRootCause] = field(default_factory=dict)
    edges: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    _node_order: list[str] = field(default_factory=list)

    def add_node(self, cause: DivergenceRootCause) -> None:
        key = f"{cause.domain}::{cause.field}"
        self.nodes[key] = cause
        if key not in self._node_order:
            self._node_order.append(key)

    def add_edge(self, from_key: str, to_key: str) -> None:
        if from_key not in self.nodes or to_key not in self.nodes:
            return
        self.edges[from_key].append(to_key)

    def topological_sort(self) -> list[str]:
        """Kahn's algorithm — returns node keys in propagation order."""
        in_degree = defaultdict(int)
        for key in self.nodes:
            in_degree[key]  # ensure all keys present
        for targets in self.edges.values():
            for t in targets:
                in_degree[t] += 1

        queue = [k for k in self.nodes if in_degree[k] == 0]
        sorted_keys = []
        while queue:
            k = queue.pop(0)
            sorted_keys.append(k)
            for nb in self.edges[k]:
                in_degree[nb] -= 1
                if in_degree[nb] == 0:
                    queue.append(nb)
        return sorted_keys

    def root_causes(self) -> list[DivergenceRootCause]:
        """Nodes with no incoming edges."""
        has_incoming = set()
        for targets in self.edges.values():
            for t in targets:
                has_incoming.add(t)
        roots = [self.nodes[k] for k in self.nodes if k not in has_incoming]
        for r in roots:
            r.is_root = True
        return roots

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": dict(self.edges),
            "root_causes": [v.to_dict() for v in self.root_causes()],
            "propagation_order": self.topological_sort(),
        }


@dataclass
class ExplainableDivergenceEngine:
    """
    Converts fingerprint + state diff → human-readable divergence explanation.

    Pipeline:
      fingerprint_mismatch
        → field_diff(exec_state, replay_state)
        → causal_root_analysis(per_domain_causal_deps)
        → severity_scoring
        → DivergenceRootCauseGraph

    Provides: why diverge, where diverge, how severe, what to do.
    """

    # Known causal dependencies: domain → list of (field, depends_on_domain, depends_on_field)
    _causal_deps: dict[str, list[tuple[str, str | None, str | None]]] = field(
        default_factory=dict
    )

    _mitigation_hints: dict[str, str] = field(
        default_factory=lambda: {
            "state-level divergence": "Reconcile initial state bootstrap; check seed randomness.",
            "delta-rate divergence": "Investigate transition rate limits; check scheduler fairness.",
            "transition-frequency divergence": "Audit event emission frequency; look for dropped events.",
            "causal-structure divergence": "Re-run causal graph analysis; check for missed dependencies.",
            "temporal drift": "Synchronize clocks or add latency compensation; check network scheduling.",
            "default": "Re-execute both systems from last known good checkpoint.",
        }
    )

    def register_causal_dependency(
        self,
        domain: str,
        field: str,
        depends_on_domain: str | None = None,
        depends_on_field: str | None = None,
    ) -> None:
        """Register a known causal dependency for root-cause analysis."""
        if domain not in self._causal_deps:
            self._causal_deps[domain] = []
        self._causal_deps[domain].append((field, depends_on_domain, depends_on_field))

    def explain(
        self,
        exec_state: dict[str, Any],
        replay_state: dict[str, Any],
        fingerprint_exec: str,
        fingerprint_replay: str,
        semantic_distance: float,
        dominant_axis: int,
        causal_depth_exec: int = 0,
        causal_depth_replay: int = 0,
    ) -> DivergenceRootCauseGraph:
        """
        Main entry point: produce causal root-cause graph from divergence data.
        """
        graph = DivergenceRootCauseGraph()

        field_diffs = self._compute_field_diffs(exec_state, replay_state)

        # Add nodes for all diverged fields
        for (domain, field), diff_info in field_diffs.items():
            cause = self._build_cause(
                domain, field, diff_info, causal_depth_exec, causal_depth_replay
            )
            graph.add_node(cause)

        # Wire edges based on causal dependencies
        for (domain, field) in field_diffs:
            deps = self._causal_deps.get(domain, [])
            for fld, dep_dom, dep_fld in deps:
                cause_key = f"{domain}::{field}"
                if dep_dom and dep_fld:
                    dep_key = f"{dep_dom}::{dep_fld}"
                    graph.add_edge(dep_key, cause_key)

        # Propagate severity
        self._propagate_severity(graph, semantic_distance, dominant_axis)

        return graph

    def _compute_field_diffs(
        self, exec_state: dict[str, Any], replay_state: dict[str, Any]
    ) -> dict[tuple[str, str], dict[str, Any]]:
        """Field-level diff across all domains."""
        diffs = {}
        all_domains = set(exec_state.keys()) | set(replay_state.keys())
        for domain in all_domains:
            e_fields = exec_state.get(domain, {})
            r_fields = replay_state.get(domain, {})
            all_fields = set(e_fields.keys()) | set(r_fields.keys())
            for field in all_fields:
                ev = e_fields.get(field)
                rv = r_fields.get(field)
                if ev != rv:
                    diffs[(domain, field)] = {
                        "exec_value": ev,
                        "replay_value": rv,
                        "diff_magnitude": self._value_magnitude(ev, rv),
                    }
        return diffs

    def _value_magnitude(self, a: Any, b: Any) -> float:
        """Scalar magnitude of difference between two values."""
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return abs(float(a) - float(b))
        if isinstance(a, str) and isinstance(b, str):
            return float(len(a) + len(b))  # proxy for string diff magnitude
        return 1.0  # non-scalar diff defaults to 1.0

    def _build_cause(
        self,
        domain: str,
        field: str,
        diff_info: dict[str, Any],
        causal_depth_exec: int,
        causal_depth_replay: int,
    ) -> DivergenceRootCause:
        """Build a single DivergenceRootCause from diff info + causal depth."""
        severity = self._score_severity(
            diff_info["diff_magnitude"],
            causal_depth_exec,
            causal_depth_replay,
        )
        hint = self._mitigation_hint_for_field(domain, field)
        return DivergenceRootCause(
            domain=domain,
            field=field,
            exec_value=diff_info["exec_value"],
            replay_value=diff_info["replay_value"],
            diff_magnitude=diff_info["diff_magnitude"],
            propagation_depth=max(causal_depth_exec, causal_depth_replay),
            severity_score=severity,
            mitigation_hint=hint,
        )

    def _score_severity(
        self, diff_magnitude: float, c_exec: int, c_replay: int
    ) -> float:
        """
        Severity 0-10:
          base = diff_magnitude / (1 + max(c_exec, c_replay))
          clamp to 10
        """
        depth = max(c_exec, c_replay, 1)
        raw = diff_magnitude / depth
        return min(10.0, max(0.0, raw))

    def _mitigation_hint_for_field(self, domain: str, field: str) -> str:
        """Look up mitigation hint; fall back to default."""
        key = f"{domain}::{field}"
        hint = self._mitigation_hints.get(key)
        if not hint:
            hint = self._mitigation_hints.get("default")
        return hint or "Investigate manually."

    def _propagate_severity(
        self, graph: DivergenceRootCauseGraph, semantic_distance: float, dominant_axis: int
    ) -> None:
        """
        Propagate severity scores along the DAG.
        A node's severity = max(own severity, max(ancestor severities))
        """
        sorted_keys = graph.topological_sort()
        for key in sorted_keys:
            node = graph.nodes[key]
            incoming = [
                graph.nodes[parent]
                for parents in graph.edges.values()
                for parent in parents
                if parent == key
            ]
            if incoming:
                max_ancestor = max(n.severity_score for n in incoming)
                node.severity_score = max(node.severity_score, max_ancestor * 0.8)

        # Also boost severity based on semantic distance
        distance_boost = min(5.0, semantic_distance / 100.0)
        axis_map = {
            0: "state-level divergence",
            1: "delta-rate divergence",
            2: "transition-frequency divergence",
            3: "causal-structure divergence",
            4: "temporal drift",
        }
        dominant_class = axis_map.get(dominant_axis, "default")
        for node in graph.nodes.values():
            if node.mitigation_hint == self._mitigation_hints.get("default"):
                node.mitigation_hint = self._mitigation_hints.get(
                    dominant_class, self._mitigation_hints["default"]
                )
            node.severity_score = min(
                10.0, node.severity_score + distance_boost
            )
