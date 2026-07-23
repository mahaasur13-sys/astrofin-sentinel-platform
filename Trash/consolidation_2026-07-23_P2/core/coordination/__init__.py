"""core/coordination — ATOM-COORD-001: Agent Coordination Layer"""

from core.coordination.pressure_field import (
    PRESSURE_FIELD_ENABLED,
    AgentSignal,
    apply_pressure_field,
    apply_pressure_field_with_metrics,
    compute_similarity,
    signal_to_direction,
)

__all__ = [
    "AgentSignal",
    "signal_to_direction",
    "signal_to_sign",
    "compute_similarity",
    "apply_pressure_field",
    "apply_pressure_field_with_metrics",
    "PRESSURE_FIELD_ENABLED",
]
