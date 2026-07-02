"""
Meta-Control Integration Layer — v8.0
Bridges v7.x instantaneous controllers with v8 persistence layer.
"""
from __future__ import annotations

from meta_control.integration.persistence_bridge import (
    CoherenceEnricher,
    GainModulator,
    PersistenceBridge,
    WeightModulator,
)

__all__ = [
    "CoherenceEnricher",
    "GainModulator",
    "PersistenceBridge",
    "WeightModulator",
]
