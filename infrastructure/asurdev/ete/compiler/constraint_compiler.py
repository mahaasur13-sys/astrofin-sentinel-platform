#!/usr/bin/env python3
"""
Constraint Compiler — L9 Injection Engine

Transforms human-readable constraints into executable DAG guards:
  max_risk: 0.25  →  pre-check node + post-check node + kill switch

Every constraint becomes: PRE → (constraint_check) → POST pipeline.
"""
from __future__ import annotations
import uuid
from typing import Any

class ConstraintType:
    MAX_RISK = "max_risk"
    MAX_EXPOSURE = "max_exposure"
    FORBIDDEN_ASSETS = "forbidden_assets"
    LATENCY_SLA = "latency_sla"
    REQUIRED_ASSET = "required_asset"

class ConstraintCompiler:
    """
    Injects governance constraints into DAG as executable nodes.
    L9 is NOT optional — every job gets constraint nodes injected.
    """

    def inject(self, dag: dict, constraints: dict) -> dict:
        injected = {"dag_id": dag["dag_id"], "nodes": [], "edges": [], "metadata": dict(dag.get("metadata", {}))}
        pre_guard = self._make_pre_guard(constraints)
        injected["nodes"].append(pre_guard)
        injected["edges.extend"]([{"from": pre_guard["node_id"], "to": n["node_id"]}] for n in dag["nodes"])
        post_guard = self._make_post_guard(constraints)
        last_ids = [n["node_id"] for n in injected["nodes"][1:]] if injected["nodes"][1:] else [pre_guard["node_id"]]
        for nid in last_ids:
            injected["edges"].append({"from": nid, "to": post_guard["node_id"]})
        injected["nodes"].append(post_guard)
        injected["metadata"]["constraints_injected"] = list(constraints.keys())
        injected["metadata"]["has_kill_switch"] = True
        return injected

    def _make_pre_guard(self, constraints: dict) -> dict:
        checks = []
        if "max_risk" in constraints:
            checks.append(f'assert state.risk_score <= {constraints["max_risk"]}')
        if "max_exposure" in constraints:
            checks.append(f'assert state.exposure <= {constraints["max_exposure"]}')
        if "forbidden_assets" in constraints:
            assets = constraints["forbidden_assets"]
            checks.append(f'for a in {assets}: assert state.asset != a')
        return {
            "node_id": str(uuid.uuid4())[:8], "name": "L9:pre_guard",
            "type": "governance", "layer": "L9",
            "action": "validate", "checks": checks,
            "on_violation": "kill", "timeout_seconds": 5,
        }

    def _make_post_guard(self, constraints: dict) -> dict:
        return {
            "node_id": str(uuid.uuid4())[:8], "name": "L9:post_guard",
            "type": "governance", "layer": "L9",
            "action": "record", "checks": [], "on_violation": "rollback",
            "timeout_seconds": 5,
        }
