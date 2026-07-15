"""
Actuator Layer — v7.4
Closed-loop causal control system for swarm dynamics.

Modules:
  causal_actuation_engine  — maps divergence field → corrective actions
  divergence_response_policy — threshold-driven intervention policy
  swarm_control_surface    — maps S_full → actuator command primitives
  stability_feedback_controller — oscillation collapse prevention
"""

from actuator.causal_actuation_engine import (
    ActuationSignal,
    ActuatorCommand,
    CausalActuationEngine,
)
from actuator.divergence_response_policy import (
    DivergenceResponsePolicy,
    InterventionLevel,
    ResponseAction,
)
from actuator.stability_feedback_controller import (
    OscillationMode,
    StabilityFeedbackController,
    StabilityState,
)
from actuator.swarm_control_surface import (
    ControlPrimitive,
    SwarmActuatorState,
    SwarmControlSurface,
)

__all__ = [
    "ActuationSignal",
    "ActuatorCommand",
    "CausalActuationEngine",
    "ControlPrimitive",
    "DivergenceResponsePolicy",
    "InterventionLevel",
    "OscillationMode",
    "ResponseAction",
    "StabilityFeedbackController",
    "StabilityState",
    "SwarmActuatorState",
    "SwarmControlSurface",
]
