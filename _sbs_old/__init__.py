"""
ATOMFederationOS — SBS (System Boundary Spec) v1
Cross-cutting verification layer for DRL + CCL + F2 + DESC.

Architecture:
    [DRL]  → reality distortion layer
    [CCL]  → semantic contract layer
    [F2]   → quorum kernel
    [DESC] → event sourcing / audit trail
    [SBS]  → system boundary enforcement (GLOBAL INVARIANTS)

SBS v1 provides:
    - GlobalInvariantEngine: cross-layer invariant verification
    - SystemBoundarySpec: hard boundary validation gate
    - FailureClassifier: DRL failure → SBS-level semantic categories
    - SYSTEM_CONTRACT: hard constraints that cannot be bypassed

Version: 0.5.1 (SBS v1 — initial release)
"""

from sbs.boundary_spec import SystemBoundarySpec
from sbs.global_invariant_engine import GlobalInvariantEngine, LayerState
from sbs.failure_classifier import FailureClassifier, FailureCategory
from sbs.system_contract import SYSTEM_CONTRACT, InvariantType
from sbs.runtime import (
    SBSRuntimeEnforcer,
    SBS_MODE,
    InvariantViolation,
    ViolationPolicy,
    ExecutionStage,
)

__version__ = "0.5.1"

__all__ = [
    "__version__",
    "SystemBoundarySpec",
    "GlobalInvariantEngine",
    "LayerState",
    "FailureClassifier",
    "FailureCategory",
    "SYSTEM_CONTRACT",
    "InvariantType",
    # Runtime
    "SBSRuntimeEnforcer",
    "SBS_MODE",
    "InvariantViolation",
    "ViolationPolicy",
    "ExecutionStage",
]
