#!/usr/bin/env python3
"""
ACOS × AstroFin — Unified Execution Trace Schema
Every AstroFin action generates a trace.
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class ExecutionNode:
    node_id: str
    agent: str
    layer: str           # ACOS layer that produced this node
    input_features: dict = field(default_factory=dict)
    output: dict = field(default_factory=dict)
    latency_ms: float = 0.0
    compute_node: str = "unset"
    ml_model: Optional[str] = None


@dataclass
class ConstraintProfile:
    risk_limit: float = 0.3
    max_exposure: float = 0.10      # 10%
    forbidden_assets: list = field(default_factory=list)
    allowed_agents: list = field(default_factory=list)
    governance_flags: list = field(default_factory=list)


@dataclass
class AstroFinTrace:
    trace_id: str
    app: str = "astrofin"
    job_type: str = "strategy_execution"
    agents: list = field(default_factory=list)
    execution_graph: dict = field(default_factory=dict)   # {node_id: ExecutionNode}
    ml_models_used: list = field(default_factory=list)
    constraint_profile: ConstraintProfile = field(default_factory=ConstraintProfile)
    scheduler_path: str = "slurm"   # slurm | ray | mixed
    node_allocation: list = field(default_factory=list)
    risk_score: float = 0.0
    latency_ms: float = 0.0
    decision_path: list = field(default_factory=list)
    policy_result: str = "pending"  # approved | rejected | escalated
    rollback_status: bool = False
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    meta_rl_generation: int = 0
    strategy_id: Optional[str] = None
    execution_mode: str = "live"    # live | backtest | paper


def build_trace(
    trace_id: str,
    agents: list,
    job_type: str = "strategy_execution",
    ml_models: list = None,
    strategy_id: str = None,
) -> AstroFinTrace:
    """Factory to build a trace with standard ACOS AstroFin structure."""
    trace = AstroFinTrace(
        trace_id=trace_id,
        app="astrofin",
        job_type=job_type,
        agents=agents,
        ml_models_used=ml_models or [],
        strategy_id=strategy_id,
    )
    return trace


def trace_to_dict(t: AstroFinTrace) -> dict:
    """Serialize trace to dict for JSON / TSDB / Ceph storage."""
    return {
        "trace_id": t.trace_id,
        "app": t.app,
        "job_type": t.job_type,
        "agents": t.agents,
        "execution_graph": {
            node_id: {
                "agent": n.agent,
                "layer": n.layer,
                "input_features": n.input_features,
                "output": n.output,
                "latency_ms": n.latency_ms,
                "compute_node": n.compute_node,
                "ml_model": n.ml_model,
            }
            for node_id, n in t.execution_graph.items()
        },
        "ml_models_used": t.ml_models_used,
        "constraint_profile": {
            "risk_limit": t.constraint_profile.risk_limit,
            "max_exposure": t.constraint_profile.max_exposure,
            "forbidden_assets": t.constraint_profile.forbidden_assets,
            "allowed_agents": t.constraint_profile.allowed_agents,
            "governance_flags": t.constraint_profile.governance_flags,
        },
        "scheduler_path": t.scheduler_path,
        "node_allocation": t.node_allocation,
        "risk_score": t.risk_score,
        "latency_ms": t.latency_ms,
        "decision_path": t.decision_path,
        "policy_result": t.policy_result,
        "rollback_status": t.rollback_status,
        "timestamp": t.timestamp,
        "meta_rl_generation": t.meta_rl_generation,
        "strategy_id": t.strategy_id,
        "execution_mode": t.execution_mode,
    }


