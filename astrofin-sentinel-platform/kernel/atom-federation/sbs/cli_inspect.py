"""
sbs/cli_inspect.py — inspect subcommand implementation.
"""
from typing import Any

from sbs import GlobalInvariantEngine, SystemBoundarySpec


def run_inspect(layer: str | None) -> dict[str, Any]:
    """Deep-inspect a specific layer."""
    engine = GlobalInvariantEngine(SystemBoundarySpec())

    if layer:
        layer_info = _get_layer_info(engine, layer)
        return {layer: layer_info}

    return {l: _get_layer_info(engine, l) for l in ["drl", "ccl", "f2", "desc", "sbs"]}


def _get_layer_info(engine: GlobalInvariantEngine, layer: str) -> dict[str, Any]:
    from sbs.runtime import SBSRuntimeEnforcer

    if layer == "sbs":
        return {
            "description": "System Boundary Spec — global invariant enforcement",
            "version": "0.6.0",
            "state": "active",
        }

    try:
        enforcer = SBSRuntimeEnforcer.current()
        if enforcer:
            state = enforcer.collect_state()
            if layer in state:
                return {"state": state[layer], "description": _layer_desc(layer)}
    except Exception:
        pass

    return {"state": "nominal", "description": _layer_desc(layer)}


def _layer_desc(name: str) -> str:
    return {
        "drl": "Distributed Reality Layer — network partition, clock skew, causality",
        "ccl": "Consensus Contract Layer — semantic contracts, stale reads",
        "f2": "Quorum Kernel — commit safety, leader uniqueness",
        "desc": "Distributed Event Sourcing Component — immutable audit trail",
    }.get(name, "Unknown layer")
