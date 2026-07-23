"""
ExecutionGateway — atom-federation-os v9.0 Single Entry Point

Sole runtime entry enforcing the full safety algebra chain:
    G1 → G2 → G3 → G4 → G5 → G6 → G7 → G8 → G9 → G10 → ACT

All state mutations MUST route exclusively through ExecutionGateway.execute().
All other entry points MUST be deprecated and delegate here.
"""
from .execution_gateway import ExecutionGateway, GateResult, GatewayState

__all__ = ["ExecutionGateway", "GateResult", "GatewayState"]
__version__ = "9.0.0"
