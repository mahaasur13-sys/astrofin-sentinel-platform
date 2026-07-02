"""
v8.2a — Controlled Autocorrection Foundation
Mutation Safety Kernel (MSK)

Modules:
  - invariant_checker   # pre-mutation constraint validation
  - stability_governor  # hard gate before mutation
  - mutation_ledger      # immutable audit log
  - rollback_engine      # state recovery subsystem

Execution order: invariant_checker → stability_governor → mutation_ledger → rollback_engine
"""

from .invariant_checker import (
    InvariantChecker,
    InvariantViolation,
    NormInvariant,
    PositiveSemidefiniteInvariant,
    SpectralInvariant,
)
from .mutation_ledger import LedgerEntry, MutationLedger, TriggerSource
from .rollback_engine import Checkpoint, RollbackEngine
from .stability_governor import GovernorDecision, GovernorSignal, GovernorThresholds, StabilityGovernor

__all__ = [
    "Checkpoint",
    "GovernorDecision",
    "GovernorSignal",
    "GovernorThresholds",
    "InvariantChecker",
    "InvariantViolation",
    "LedgerEntry",
    "MutationLedger",
    "NormInvariant",
    "PositiveSemidefiniteInvariant",
    "RollbackEngine",
    "SpectralInvariant",
    "StabilityGovernor",
    "TriggerSource",
]
