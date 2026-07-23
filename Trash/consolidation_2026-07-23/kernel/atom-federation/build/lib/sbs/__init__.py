"""
ATOMFederationOS — SBS (System Boundary Spec) v1
Cross-cutting verification layer for DRL + CCL + F2 + DESC.

Version: 0.6.0 (SBS v1 — CLI, schema validation, release pipeline)
"""

# ── Version (Single Source of Truth) ─────────────────────────────────
# ── Public API ───────────────────────────────────────────────────────
from sbs.boundary_spec import SystemBoundarySpec
from sbs.failure_classifier import FailureCategory, FailureClassifier
from sbs.global_invariant_engine import GlobalInvariantEngine, LayerState
from sbs.schema_validator import (
    REQUIRED_LAYERS,
    SchemaValidationError,
    collect_state,
    validate_state,
)
from sbs.system_contract import SYSTEM_CONTRACT, InvariantType
from sbs.version import (
    BUILD,
    VERSION,
    VERSION_DATE,
    VERSION_INFO,
    __version__,
    __version_info__,
    __version_tuple__,
)

# Alias for backward compatibility
schema_validate_state = validate_state
from sbs.runtime import (
    SBS_MODE,
    ExecutionStage,
    InvariantViolation,
    SBSRuntimeEnforcer,
    ViolationPolicy,
)


# ── CLI entry point (lazy import) ────────────────────────────────────
def main() -> None:
    """Entry point for `sbs` CLI command."""
    from sbs.cli import main as cli_main
    cli_main()

__all__ = [
    # Version
    "__version__",
    "__version_info__",
    "__version_tuple__",
    "VERSION",
    "VERSION_INFO",
    "VERSION_DATE",
    "BUILD",
    # Core
    "SystemBoundarySpec",
    "GlobalInvariantEngine",
    "LayerState",
    "FailureClassifier",
    "FailureCategory",
    "SYSTEM_CONTRACT",
    "InvariantType",
    # Schema
    "schema_validate_state",
    "SchemaValidationError",
    "REQUIRED_LAYERS",
    # Runtime
    "SBSRuntimeEnforcer",
    "SBS_MODE",
    "InvariantViolation",
    "ViolationPolicy",
    "ExecutionStage",
    # CLI
    "main",
]
