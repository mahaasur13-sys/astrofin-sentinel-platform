#!/usr/bin/env python3
"""
L9 EBL — Capability Registry
Capability-based access control for all infra actions.
"""
from enum import Enum, auto
from typing import Dict, Set, List, Optional
from dataclasses import dataclass, field
import uuid

class Capability(Enum):
    INFRA_READ = "infra:read"
    INFRA_WRITE = "infra:write"
    INFRA_EXECUTE = "infra:execute"
    ML_READ = "ml:read"
    ML_WRITE = "ml:write"
    STATE_READ = "state:read"
    STATE_WRITE = "state:write"
    GOVERNANCE_OVERRIDE = "gov:override"
    ROLLBACK_EXECUTE = "rollback:execute"
    SELF_HEAL_TRIGGER = "heal:trigger"

@dataclass
class CapabilitySet:
    name: str
    capabilities: Set[Capability]
    description: str = ""
    tags: List[str] = field(default_factory=list)

    def grants(self, cap: Capability) -> bool:
        return cap in self.capabilities

    def grants_any(self, caps: List[Capability]) -> bool:
        return bool(self.capabilities & set(caps))

ROLE_CAPABILITIES: Dict[str, CapabilitySet] = {}

def register_role(name: str, caps: List[str], description: str = "", tags: List[str] = None) -> CapabilitySet:
    cap_set = CapabilitySet(
        name=name,
        capabilities={Capability(c) for c in caps},
        description=description,
        tags=tags or []
    )
    ROLE_CAPABILITIES[name] = cap_set
    return cap_set

# === BUILT-IN ROLES ===

register_role("root",
    [c.value for c in Capability],
    "Unrestricted — used only by governance kernel")

register_role("ml_inference",
    ["infra:read", "ml:read", "state:read"],
    "ML inference pipeline — read-only access")

register_role("optimizer",
    ["infra:read", "ml:read", "state:read", "state:write", "infra:execute"],
    "Optimization engine — constrained execution")

register_role("self_healing",
    ["infra:read", "ml:read", "state:read", "infra:execute", "heal:trigger"],
    "Self-healing system — trigger only, no state mutation")

register_role("governance",
    [c.value for c in Capability],
    "Governance kernel — full authority")

register_role("operator",
    ["infra:read", "ml:read", "state:read", "state:write", "rollback:execute"],
    "Human operator — rollback only")

@dataclass
class ExecutionContext:
    trace_id: str
    role: str
    session_id: str
    granted: Set[Capability] = field(default_factory=set)
    denied: Set[Capability] = field(default_factory=set)
    checked_at: Optional[str] = None

    @staticmethod
    def create(trace_id: str, role: str, session_id: str) -> "ExecutionContext":
        cap_set = ROLE_CAPABILITIES.get(role)
        if not cap_set:
            raise ValueError(f"Unknown role: {role}")
        return ExecutionContext(
            trace_id=trace_id,
            role=role,
            session_id=session_id,
            granted=cap_set.capabilities
        )

    def can(self, cap: Capability) -> bool:
        return cap in self.granted

    def check(self, cap: Capability, reason: str = "") -> bool:
        if cap not in self.granted:
            raise CapabilityDenied(
                capability=cap,
                role=self.role,
                trace_id=self.trace_id,
                reason=reason
            )
        return True

class CapabilityDenied(Exception):
    def __init__(self, capability: Capability, role: str, trace_id: str, reason: str = ""):
        self.capability = capability
        self.role = role
        self.trace_id = trace_id
        self.reason = reason
        super().__init__(f"CapabilityDenied: {capability.value} for role={role} trace={trace_id} reason={reason}")

def enforce(ctx: ExecutionContext, cap: Capability, reason: str = "") -> None:
    ctx.check(cap, reason)

def enforce_any(ctx: ExecutionContext, caps: List[Capability], reason: str = "") -> None:
    for cap in caps:
        try:
            ctx.check(cap, reason)
            return
        except CapabilityDenied:
            continue
    raise CapabilityDenied(
        capability=Capability(caps[0].value + "_any"),
        role=ctx.role,
        trace_id=ctx.trace_id,
        reason=f"None of {[c.value for c in caps]} granted to role={ctx.role}"
    )

def enforce_all(ctx: ExecutionContext, caps: List[Capability], reason: str = "") -> None:
    for cap in caps:
        ctx.check(cap, reason)

# Capability registry query
def query_capabilities(role: str) -> List[str]:
    cs = ROLE_CAPABILITIES.get(role)
    return [c.value for c in cs.capabilities] if cs else []

def list_roles() -> List[str]:
    return list(ROLE_CAPABILITIES.keys())
