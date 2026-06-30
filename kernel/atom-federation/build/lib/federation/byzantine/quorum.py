"""
quorum.py — Byzantine quorum definitions for v9.8

Quorum types:
  f+1  — wait for any f+1 responses (Byzantine reader quorum)
  2f+1 — wait for 2f+1 matching responses (Byzantine consensus quorum)
  3f+1 — wait for 3f+1 responses (stronger liveness)

All quorums require integer f: f < n.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class QuorumType(Enum):
    f_plus_1 = "f_plus_1"   # Byzantine fault tolerant reader
    two_f_plus_1 = "2f+1"  # Standard Byzantine consensus
    three_f_plus_1 = "3f+1"  # Stronger liveness guarantee


@dataclass
class QuorumResult:
    quorum_type: QuorumType
    n: int          # total nodes
    f: int          # max tolerated Byzantine nodes
    required: int   # minimum responses needed
    achieved: int   # responses collected
    reached: bool
    missing: int    # n - achieved


class QuorumCalculator:
    """Computes Byzantine fault tolerance quorum thresholds."""

    @staticmethod
    def compute_f(n: int) -> int:
        if n < 3:
            return 0
        return (n - 1) // 3

    @staticmethod
    def quorum_size(n: int, qt: QuorumType) -> int:
        f = QuorumCalculator.compute_f(n)
        if qt == QuorumType.f_plus_1:
            return f + 1
        elif qt == QuorumType.two_f_plus_1:
            return 2 * f + 1
        elif qt == QuorumType.three_f_plus_1:
            return 3 * f + 1
        raise ValueError(f"Unknown QuorumType: {qt}")

    @staticmethod
    def check(responses: int, n: int, qt: QuorumType) -> QuorumResult:
        f = QuorumCalculator.compute_f(n)
        required = QuorumCalculator.quorum_size(n, qt)
        return QuorumResult(
            quorum_type=qt,
            n=n,
            f=f,
            required=required,
            achieved=responses,
            reached=responses >= required,
            missing=max(0, required - responses),
        )


__all__ = [
    "QuorumCalculator",
    "QuorumResult",
    "QuorumType",
]
