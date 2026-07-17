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
def __getattr__(name: str):
    if name == "main":
        from sbs.cli import main
        return main
    if name == "app":
        from sbs.cli import app
        return app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# ── CLI modules (for programmatic access) ─────────────────────────────
# These can be imported directly: from sbs.cli_verify import run_verify

__all__ = [
    # Version
    "__version__", "__version_info__", "__version_tuple__",
    "VERSION", "VERSION_INFO", "VERSION_DATE", "BUILD",
    # Core
    "SystemBoundarySpec",
    "GlobalInvariantEngine", "LayerState",
    "FailureClassifier", "FailureCategory",
    "SYSTEM_CONTRACT", "InvariantType",
    # Schema
    "validate_state", "collect_state", "SchemaValidationError", "REQUIRED_LAYERS",
    "schema_validate_state",
    # Runtime
    "SBSRuntimeEnforcer", "SBS_MODE", "InvariantViolation", "ViolationPolicy", "ExecutionStage",
    # CLI lazy exports
    "main", "app",
    # __main__ (enables `python3 -m sbs`)
    "__main__",
]
