#!/usr/bin/env python3
"""
ACOS Contract Validator — DAG + Event + Trace validation.
Patch 1: DAGValidator with full schema validation.
"""
from __future__ import annotations
from typing import Any, Dict, List
from uuid import UUID
from dataclasses import dataclass
from enum import Enum


class EventType(str, Enum):
    NODE_START = "node_start"
    NODE_END = "node_end"
    DAG_START = "dag_start"
    DAG_END = "dag_end"
    DAG_CREATED = "DAG_CREATED"
    DAG_VALIDATED = "DAG_VALIDATED"
    GOVERNANCE_APPROVED = "GOVERNANCE_APPROVED"
    GOVERNANCE_REJECTED = "GOVERNANCE_REJECTED"
    NODE_SCHEDULED = "NODE_SCHEDULED"
    NODE_EXECUTED = "NODE_EXECUTED"
    NODE_FAILED = "NODE_FAILED"
    TRACE_RECORDED = "TRACE_RECORDED"


@dataclass
class ContractViolation:
    message: str
    path: str
    severity: str  # error, warning


class DAGValidator:
    """
    Validates DAG, Event, and Trace contracts.
    
    Guarantees:
    - validate_dag() checks graph structure before execution
    - validate_event() checks event schema
    - validate_trace() checks trace-level constraints
    """

    @staticmethod
    def validate_dag(dag: Dict[str, Any]) -> List[ContractViolation]:
        violations = []

        # 1. Presence of nodes
        if "nodes" not in dag:
            violations.append(ContractViolation("Missing 'nodes'", "/dag", "error"))
            return violations

        nodes = dag["nodes"]
        node_ids = set()

        # 2. Unique node IDs
        for node in nodes:
            node_id = node.get("id")
            if not node_id:
                violations.append(ContractViolation("Node missing 'id'", "/nodes", "error"))
            elif node_id in node_ids:
                violations.append(ContractViolation(f"Duplicate node id: {node_id}", f"/nodes/{node_id}", "error"))
            else:
                node_ids.add(node_id)

        # 3. Valid edge references
        edges = dag.get("edges", [])
        for edge in edges:
            src = edge.get("source")
            tgt = edge.get("target")
            if src not in node_ids:
                violations.append(ContractViolation(f"Edge source '{src}' not found", f"/edges/{edge}", "error"))
            if tgt not in node_ids:
                violations.append(ContractViolation(f"Edge target '{tgt}' not found", f"/edges/{edge}", "error"))

        # 4. trace_id UUID format (if present)
        trace_id = dag.get("trace_id")
        if trace_id:
            try:
                UUID(trace_id)
            except ValueError:
                violations.append(ContractViolation(f"Invalid trace_id format: {trace_id}", "/dag/trace_id", "error"))

        # 5. EventType validation in nodes (if present)
        for node in nodes:
            event_type = node.get("event_type")
            if event_type and not isinstance(event_type, EventType):
                try:
                    EventType(event_type)
                except ValueError:
                    violations.append(ContractViolation(f"Invalid EventType: {event_type}", f"/nodes/{node.get('id')}/event_type", "error"))

        return violations

    @staticmethod
    def validate_event(event: Dict[str, Any]) -> List[ContractViolation]:
        violations = []
        required_fields = ["event_id", "trace_id", "node_id", "event_type", "payload", "created_at"]
        for field in required_fields:
            if field not in event:
                violations.append(ContractViolation(f"Missing field '{field}' in event", "/event", "error"))
        return violations

    @staticmethod
    def validate_trace(trace_data: Dict[str, Any]) -> List[ContractViolation]:
        violations = []
        if "trace_id" not in trace_data:
            violations.append(ContractViolation("Missing trace_id in trace", "/trace", "error"))
        if "events" not in trace_data or not isinstance(trace_data["events"], list):
            violations.append(ContractViolation("Missing or invalid 'events' list", "/trace", "error"))
        return violations
