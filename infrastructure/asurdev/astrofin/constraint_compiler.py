#!/usr/bin/env python3
"""
ACOS × AstroFin — Constraint Compiler
Transforms AstroFin trading constraints → executable DAG → L9 enforcement hooks.
"""
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum
import hashlib


class ConstraintOp(Enum):
    LTE = "<="
    GTE = ">="
    EQ = "=="
    IN = "in"
    NOT_IN = "not_in"
    FORBIDDEN = "forbidden"


class ConstraintType(Enum):
    RISK = "risk"
    EXPOSURE = "exposure"
    ASSET = "asset"
    AGENT = "agent"
    LATENCY = "latency"
    CUSTOM = "custom"


@dataclass
class Constraint:
    cid: str
    ctype: ConstraintType
    op: ConstraintOp
    threshold: Any
    description: str
    severity: str = "high"   # critical | high | medium | low
    enabled: bool = True

    @staticmethod
    def make_id(*parts: str) -> str:
        return hashlib.sha256("|".join(parts).encode()).hexdigest()[:12]

    def evaluate(self, value: Any) -> bool:
        if not self.enabled:
            return True
        if self.op == ConstraintOp.LTE:
            return value <= self.threshold
        elif self.op == ConstraintOp.GTE:
            return value >= self.threshold
        elif self.op == ConstraintOp.EQ:
            return value == self.threshold
        elif self.op == ConstraintOp.IN:
            return value in self.threshold
        elif self.op == ConstraintOp.NOT_IN:
            return value not in self.threshold
        elif self.op == ConstraintOp.FORBIDDEN:
            return value not in self.threshold
        return True

    def to_guard(self) -> str:
        op_map = {
            ConstraintOp.LTE: "<=",
            ConstraintOp.GTE: ">=",
            ConstraintOp.EQ: "==",
            ConstraintOp.IN: "in",
            ConstraintOp.NOT_IN: "not in",
            ConstraintOp.FORBIDDEN: "forbidden",
        }
        return f"assert {self.ctype.value} {op_map[self.op]} {self.threshold}  # {self.description}"


@dataclass
class PolicyBlock:
    block_id: str
    name: str
    constraints: list[Constraint] = field(default_factory=list)
    parent: Optional[str] = None   # block_id of parent
    children: list[str] = field(default_factory=list)

    def all_constraints(self) -> list[Constraint]:
        result = list(self.constraints)
        for child_id in self.children:
            pass  # resolved at runtime via PolicyBlockDB
        return result

    def to_executable(self) -> list[str]:
        guards = [c.to_guard() for c in self.constraints if c.enabled]
        return guards


class AstroFinConstraintCompiler:
    """
    Compiles AstroFin YAML/policy text → executable Constraint DAG.
    DAG structure: PolicyBlock (root) → PolicyBlock (sub) → Constraint
    Output: L9 enforcement hooks ready for gate.py validation.
    """

    def __init__(self):
        self.blocks: dict[str, PolicyBlock] = {}
        self.constraints: dict[str, Constraint] = {}

    def add_constraint(self, block_id: str, constraint: Constraint) -> None:
        if block_id not in self.blocks:
            self.blocks[block_id] = PolicyBlock(block_id=block_id, name=block_id)
        self.blocks[block_id].constraints.append(constraint)
        self.constraints[constraint.cid] = constraint

    def add_block(self, block: PolicyBlock) -> None:
        self.blocks[block.block_id] = block

    def build_risk_profile(self, risk_limit: float = 0.3, max_exposure: float = 0.10,
                           forbidden: list = None) -> str:
        """Build standard AstroFin risk profile. Returns block_id."""
        block_id = "astrofin_risk_default"
        forbidden = forbidden or [
            "high_leverage_derivatives",
            "naked_options",
            "forex_crypto_spot",
        ]

        constraints = [
            Constraint(
                cid=Constraint.make_id(block_id, "risk"),
                ctype=ConstraintType.RISK,
                op=ConstraintOp.LTE,
                threshold=risk_limit,
                description="risk_score must stay below limit",
                severity="critical",
            ),
            Constraint(
                cid=Constraint.make_id(block_id, "exposure"),
                ctype=ConstraintType.EXPOSURE,
                op=ConstraintOp.LTE,
                threshold=max_exposure,
                description="max portfolio exposure 10%",
                severity="critical",
            ),
            Constraint(
                cid=Constraint.make_id(block_id, "forbidden_assets"),
                ctype=ConstraintType.ASSET,
                op=ConstraintOp.NOT_IN,
                threshold=forbidden,
                description=f"forbidden assets: {forbidden}",
                severity="critical",
            ),
        ]

        for c in constraints:
            self.add_constraint(block_id, c)

        return block_id

    def build_agent_policy(self, agent_name: str, allowed_agents: list = None) -> str:
        """Build per-agent policy block. Returns block_id."""
        block_id = f"agent_policy_{agent_name}"
        allowed = allowed_agents or [agent_name]
        c = Constraint(
            cid=Constraint.make_id(block_id, "agent"),
            ctype=ConstraintType.AGENT,
            op=ConstraintOp.IN,
            threshold=allowed,
            description=f"only agents {allowed} can execute this block",
            severity="high",
        )
        self.add_constraint(block_id, c)
        return block_id

    def build_latency_sla(self, max_latency_ms: int = 5000) -> str:
        """Build latency SLA block."""
        block_id = "latency_sla"
        c = Constraint(
            cid=Constraint.make_id(block_id, "latency"),
            ctype=ConstraintType.LATENCY,
            op=ConstraintOp.LTE,
            threshold=max_latency_ms,
            description=f"end-to-end latency must not exceed {max_latency_ms}ms",
            severity="medium",
        )
        self.add_constraint(block_id, c)
        return block_id

    def compile(self) -> dict:
        """
        Compile all blocks → executable DAG for L9 gate.
        Returns: {
            "blocks": {block_id: PolicyBlock},
            "constraints": {cid: Constraint},
            "guard_lines": [executable_guard_str],
        }
        """
        all_guards = []
        for block in self.blocks.values():
            all_guards.extend(block.to_executable())

        return {
            "blocks": self.blocks,
            "constraints": self.constraints,
            "guard_lines": all_guards,
        }

    def validate_trace(self, trace_dict: dict) -> tuple[bool, list[str]]:
        """
        Validate a trace_dict against compiled constraints.
        Returns: (passes, list_of_failures)
        """
        failures = []
        cp = trace_dict.get("constraint_profile", {})

        for c in self.constraints.values():
            if c.ctype == ConstraintType.RISK:
                val = trace_dict.get("risk_score", 0.0)
            elif c.ctype == ConstraintType.EXPOSURE:
                val = cp.get("max_exposure", 0.0)
            elif c.ctype == ConstraintType.ASSET:
                val = cp.get("forbidden_assets", [])
                val = any(fa in val for fa in c.threshold)
            elif c.ctype == ConstraintType.AGENT:
                val = trace_dict.get("agents", [])
            elif c.ctype == ConstraintType.LATENCY:
                val = trace_dict.get("latency_ms", 0)
            else:
                continue

            if not c.evaluate(val):
                failures.append(
                    f"CONSTRAINT_FAIL [{c.severity}] {c.ctype.value} "
                    f"{c.op.name} {c.threshold}: got={val}"
                )

        return len(failures) == 0, failures


def build_astrofin_policy(
    risk_limit: float = 0.3,
    max_exposure: float = 0.10,
    forbidden_assets: list = None,
) -> AstroFinConstraintCompiler:
    """One-call factory for standard AstroFin policy."""
    compiler = AstroFinConstraintCompiler()
    compiler.build_risk_profile(risk_limit, max_exposure, forbidden_assets)
    compiler.build_latency_sla(max_latency_ms=5000)
    return compiler


