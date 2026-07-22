"""ACOS Event Types — unified enum for all event categories."""

from __future__ import annotations

from enum import Enum


class EventType(str, Enum):
    """
    Complete event type taxonomy for ACOS.

    Format: CATEGORY_SUBCATEGORY

    Categories:
        DAG_*     — Graph lifecycle
        GOVERNANCE_* — Policy decisions
        NODE_*    — Node lifecycle
        TRACE_*   — Trace lifecycle
        TUNNEL_*  — AmneziaWG tunnel events
        INCIDENT_* — Fault/incident events
        SYSTEM_*  — System-level events
    """

    # ─── DAG lifecycle ─────────────────────────────────────────────
    DAG_CREATED = "DAG_CREATED"
    DAG_VALIDATED = "DAG_VALIDATED"
    DAG_INVALID = "DAG_INVALID"
    DAG_REJECTED = "DAG_REJECTED"

    # ─── Governance ─────────────────────────────────────────────────
    GOVERNANCE_APPROVED = "GOVERNANCE_APPROVED"
    GOVERNANCE_REJECTED = "GOVERNANCE_REJECTED"
    POLICY_EVALUATED = "POLICY_EVALUATED"

    # ─── Node lifecycle ─────────────────────────────────────────────
    NODE_SCHEDULED = "NODE_SCHEDULED"
    NODE_EXECUTED = "NODE_EXECUTED"
    NODE_FAILED = "NODE_FAILED"
    NODE_START = "node_start"
    NODE_END = "node_end"

    # ─── Trace lifecycle ────────────────────────────────────────────
    TRACE_RECORDED = "TRACE_RECORDED"
    STATE_RECONSTRUCTED = "STATE_RECONSTRUCTED"
    SNAPSHOT_CREATED = "SNAPSHOT_CREATED"
    SCHEDULER_TIMEOUT = "SCHEDULER_TIMEOUT"
    REPLAY_INCONSISTENT = "REPLAY_INCONSISTENT"

    # ─── Tunnel events (AmneziaWG) ─────────────────────────────────
    TUNNEL_UP = "TUNNEL_UP"
    TUNNEL_DOWN = "TUNNEL_DOWN"
    TUNNEL_FAILOVER = "TUNNEL_FAILOVER"
    TUNNEL_HEALTH_CHECK = "TUNNEL_HEALTH_CHECK"
    TUNNEL_CONFIG_ERROR = "TUNNEL_CONFIG_ERROR"
