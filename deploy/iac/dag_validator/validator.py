#!/usr/bin/env python3
"""
DAG Validator — L11 Formal Verification
I1: acyclicity, I2: dependency closure, I3: deterministic ordering, I4: side-effect isolation
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ViolationType(Enum):
    I1_CYCLE = "I1_CYCLE"
    I2_MISSING_INPUT = "I2_MISSING_INPUT"
    I3_NONDETERMINISTIC = "I3_NONDETERMINISTIC"
    I4_SIDE_EFFECT = "I4_SIDE_EFFECT"
    VERSION_CONFLICT = "VERSION_CONFLICT"


@dataclass
class Violation:
    type: ViolationType
    node_id: str | None
    details: str
    severity: str = "ERROR"


@dataclass
class ValidationResult:
    valid: bool
    violations: list[Violation] = field(default_factory=list)
    dag_hash: str | None = None
    invariants_satisfied: dict[str, bool] = field(default_factory=dict)


class DAGValidator:
    def __init__(self):
        self._validated_dags: dict[str, ValidationResult] = {}

    def _get_node_id(self, node: dict) -> str:
        return node.get("node_id", node.get("id", ""))

    def _serialize(self, obj, _seen=None):
        if _seen is None:
            _seen = set()
        obj_id = id(obj)
        if obj_id in _seen:
            return "<circular>"
        _seen.add(obj_id)
        if isinstance(obj, (list, tuple)):
            return [self._serialize(x, _seen) for x in obj]
        if isinstance(obj, dict):
            return {k: self._serialize(v, _seen) for k, v in obj.items()}
        if callable(obj) and not isinstance(obj, type):
            return "<lambda>"
        if isinstance(obj, type):
            return f"<type:{obj.__name__}>"
        return obj

    def validate(self, dag: dict[str, Any], deterministic_seed: int | None = None) -> ValidationResult:
        raw_nodes = dag.get("nodes", [])
        nodes = {self._get_node_id(n): n for n in raw_nodes if self._get_node_id(n)}
        edges = dag.get("edges", [])
        dag_hash = self._compute_dag_hash(dag)

        violations = []
        cycle_path = self._find_cycle(nodes, edges)
        if cycle_path:
            violations.append(Violation(ViolationType.I1_CYCLE, None, f"Cycle: {' -> '.join(cycle_path)}"))
        violations.extend(self._check_dependency_closure(nodes, edges))
        violations.extend(self._check_deterministic_order(nodes, edges, deterministic_seed))
        violations.extend(self._check_side_effects(nodes))

        has_error = any(v.severity == "ERROR" for v in violations)
        result = ValidationResult(
            valid=not has_error,
            violations=violations,
            dag_hash=dag_hash,
            invariants_satisfied={
                "I1": cycle_path is None,
                "I2": not any(v.type == ViolationType.I2_MISSING_INPUT for v in violations),
                "I3": not any(v.type == ViolationType.I3_NONDETERMINISTIC for v in violations),
                "I4": not any(v.type == ViolationType.I4_SIDE_EFFECT for v in violations),
            },
        )
        self._validated_dags[dag_hash] = result
        return result

    def _compute_dag_hash(self, dag: dict) -> str:
        canonical = json.dumps(self._serialize(dag), sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def _find_cycle(self, nodes: dict, edges: list) -> list | None:
        graph = {nid: [] for nid in nodes}
        for src, dst in edges:
            if src in graph and dst in graph:
                graph[src].append(dst)
        visited, recstack, path = set(), set(), []

        def dfs(v):
            visited.add(v)
            recstack.add(v)
            path.append(v)
            for nb in graph.get(v, []):
                if nb not in visited:
                    found = dfs(nb)
                    if found:
                        return found
                elif nb in recstack:
                    idx = path.index(nb)
                    return path[idx:] + [nb]
            path.pop()
            recstack.discard(v)
            return None

        for v in nodes:
            if v not in visited:
                result = dfs(v)
                if result:
                    return result
        return None

    def _check_dependency_closure(self, nodes: dict, edges: list) -> list[Violation]:
        violations = []
        defined = set(nodes.keys())
        for src, dst in edges:
            if src not in defined:
                violations.append(Violation(ViolationType.I2_MISSING_INPUT, dst, f"Edge source '{src}' not in graph"))
        return violations

    def _check_deterministic_order(self, nodes: dict, edges: list, seed: int | None) -> list[Violation]:
        import random

        violations = []
        if seed is not None:
            random.seed(seed)
        in_deg = dict.fromkeys(nodes, 0)
        for src, _ in edges:
            if src in in_deg:
                in_deg[_] = in_deg.get(src, 0) + 1
        frontier = [nid for nid, d in in_deg.items() if d == 0]
        if len(frontier) > 1:
            violations.append(
                Violation(
                    ViolationType.I3_NONDETERMINISTIC,
                    None,
                    f"{len(frontier)} root nodes — deterministic tie-breaking required (seed={seed})",
                )
            )
        return violations

    def _check_side_effects(self, nodes: dict) -> list[Violation]:
        violations = []
        for nid, node in nodes.items():
            if node.get("type") in {"global_write", "filesystem_write", "network_call", "env_mutate"} and not node.get(
                "isolated"
            ):
                violations.append(
                    Violation(ViolationType.I4_SIDE_EFFECT, nid, f"Node '{nid}' performs side effect without isolation")
                )
        return violations

    def verify_hash(self, dag: dict, expected_hash: str) -> bool:
        return self._compute_dag_hash(dag) == expected_hash


if __name__ == "__main__":
    validator = DAGValidator()
    dag = {"nodes": [{"node_id": "a"}, {"node_id": "b"}, {"node_id": "c"}], "edges": [["a", "b"], ["b", "c"]]}
    result = validator.validate(dag, seed=42)
    print(f"DAG valid: {result.valid}")
    print(f"Invariants: {result.invariants_satisfied}")
    print(f"Hash: {result.dag_hash}")
    print(f"Violations: {[v.type.value for v in result.violations]}")
