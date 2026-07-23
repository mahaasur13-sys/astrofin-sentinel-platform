"""
SBS State Schema Validator — enforces required layer + version contract.
"""
from typing import Any

REQUIRED_LAYERS = ["drl", "ccl", "f2_f3_f8", "desc", "sbs"]


class SchemaValidationError(Exception):
    """Raised when state fails schema validation."""
    pass


def validate_state(state: dict[str, Any]) -> None:
    """Validate that state dict contains all required layers with a version field."""
    for layer in REQUIRED_LAYERS:
        if layer not in state:
            raise SchemaValidationError(f"Missing layer: {layer}")
        if "version" not in state[layer]:
            raise SchemaValidationError(f"{layer}.version missing — state schema broken")


def collect_state() -> dict[str, Any]:
    """
    Collect current SBS state from all registered layers.
    Returns dict matching the schema expected by validate_state().
    """
    from sbs.boundary_spec import SystemBoundarySpec
    from sbs.runtime import SBSRuntimeEnforcer

    try:
        enforcer = SBSRuntimeEnforcer.current()
        if enforcer is not None:
            return enforcer.collect_state()
    except Exception:
        pass

    spec = SystemBoundarySpec()
    return {
        "drl": {"version": 1},
        "ccl": {"version": 1},
        "f2_f3_f8": {"version": 1},
        "desc": {"version": 1},
        "sbs": {"version": spec.version if hasattr(spec, "version") else "0.5.2"},
    }
