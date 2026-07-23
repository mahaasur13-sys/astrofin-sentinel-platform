#!/usr/bin/env python3
"""
ACOS SCL v6 — StateProjection (PATCH 3: enriched projections).
Adds node_graph_resolution and execution_order to standard projection.
"""
from __future__ import annotations
from typing import Any
from acos.state.reducer import StateReducer


class StateProjection:
    """
    Read-side state projection.
    
    PATCH 3: enrich_projection() adds node_graph_resolution and execution_order.
    """

    def __init__(self, log):
        self._reducer = StateReducer(log)
        self._log = log

    def get_trace(self, trace_id: str) -> dict[str, Any]:
        """Rebuild standard state."""
        return self._reducer.rebuild(trace_id)

    def get_enriched_trace(self, trace_id: str) -> dict[str, Any]:
        """
        PATCH 3: Returns state with node_graph_resolution and execution_order.
        
        node_graph_resolution: topological order of nodes from DAG
        execution_order: actual execution sequence from events
        """
        # Get base state
        state = self._reducer.rebuild(trace_id)
        
        # 1. node_graph_resolution — from DAG node order
        dag_nodes = state.get("dag", {}).get("nodes", [])
        node_graph_resolution = [
            n.get("id", n.get("name", str(n))) if isinstance(n, dict) else str(n)
            for n in dag_nodes
        ]
        
        # 2. execution_order — from NODE_SCHEDULED/NODE_EXECUTED events
        events = self._log.get_trace(trace_id)
        execution_order = []
        for event in sorted(events, key=lambda e: e.timestamp):
            et = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
            if et in ("NODE_SCHEDULED", "NODE_EXECUTED", "NODE_FAILED"):
                p = dict(event.payload) if hasattr(event.payload, 'items') else {}
                execution_order.append({
                    "node_id": p.get("node_id", ""),
                    "event": et,
                    "timestamp": event.timestamp,
                })
        
        return {
            **state,
            "node_graph_resolution": node_graph_resolution,
            "execution_order": execution_order,
        }
