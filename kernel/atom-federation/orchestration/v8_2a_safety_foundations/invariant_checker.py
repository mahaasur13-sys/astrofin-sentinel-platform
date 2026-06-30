"""
invariant_checker.py — pre-mutation constraint validation

v8.2a foundation #1
Keeps mutation bounded within safe operating envelope.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

import numpy as np


class InvariantViolation(Exception):
    """Raised when a mutation violates a safety invariant."""

    def __init__(self, invariant_name: str, message: str, details: dict):
        self.invariant_name = invariant_name
        self.details = details
        super().__init__(f"[{invariant_name}] {message}: {details}")


@dataclass
class NormInvariant:
    """
    ε-norm bound on parameter change.

    enforce: ||θ_new − θ_old||_p ≤ ε
    """

    name: str
    epsilon: float
    p: float = 2.0  # L2 by default

    def check(self, theta_old: np.ndarray, theta_new: np.ndarray) -> bool:
        delta = theta_new - theta_old
        norm = float(np.linalg.norm(delta, ord=self.p))
        return norm <= self.epsilon

    def validate(self, theta_old: np.ndarray, theta_new: np.ndarray) -> None:
        """Raise InvariantViolation if bound is exceeded."""
        if not self.check(theta_old, theta_new):
            delta = theta_new - theta_old
            norm = float(np.linalg.norm(delta, ord=self.p))
            raise InvariantViolation(
                self.name,
                f"norm {norm:.4f} exceeds epsilon {self.epsilon}",
                {"theta_old_norm": float(np.linalg.norm(theta_old, ord=self.p)),
                 "theta_new_norm": float(np.linalg.norm(theta_new, ord=self.p)),
                 "delta_norm": norm,
                 "epsilon": self.epsilon,
                 "p": self.p},
            )


@dataclass
class SpectralInvariant:
    """
    Bounds the spectral radius of the gain matrix after mutation.

    Ensures: max(|eigenvalues(K_new)|) ≤ λ_max
    """

    name: str
    lambda_max: float = 0.95

    def validate(self, K_old: np.ndarray, K_new: np.ndarray) -> None:
        eigenvalues_new = np.linalg.eigvals(K_new)
        spectral_radius = float(np.max(np.abs(eigenvalues_new)))
        if spectral_radius > self.lambda_max:
            raise InvariantViolation(
                self.name,
                f"spectral radius {spectral_radius:.4f} exceeds λ_max {self.lambda_max}",
                {"spectral_radius": spectral_radius,
                 "lambda_max": self.lambda_max,
                 "eigenvalues": eigenvalues_new.tolist()},
            )


@dataclass
class PositiveSemidefiniteInvariant:
    """
    Ensures a matrix remains positive semi-definite after mutation.

    Valid for covariance / information matrices.
    """

    name: str
    matrix_getter: Callable[[np.ndarray], np.ndarray] = field(
        default=lambda theta: theta.reshape(int(np.sqrt(len(theta))), -1)
    )

    def validate(self, theta_old: np.ndarray, theta_new: np.ndarray) -> None:
        M_new = self.matrix_getter(theta_new)
        try:
            eigenvalues = np.linalg.eigvalsh(M_new)
        except np.linalg.LinAlgError as e:
            raise InvariantViolation(self.name, f"eigenvalue computation failed: {e}", {})
        if np.any(eigenvalues < -1e-9):
            raise InvariantViolation(
                self.name,
                f"matrix has negative eigenvalues: {eigenvalues}",
                {"min_eigenvalue": float(np.min(eigenvalues)),
                 "threshold": -1e-9},
            )


Invariant = NormInvariant | SpectralInvariant | PositiveSemidefiniteInvariant


class InvariantChecker:
    """
    Pre-mutation safety validator.

    Runs all registered invariants before a mutation is applied.
    If any invariant fails → mutation is blocked.

    Usage:
        checker = InvariantChecker()
        checker.register(NormInvariant("param_drift", epsilon=0.15))
        checker.register(SpectralInvariant("gain_bound", lambda_max=0.9))
        checker.validate(theta_old, theta_new)   # raises on violation
    """

    def __init__(self):
        self._invariants: list[Invariant] = []

    def register(self, invariant: Invariant) -> None:
        self._invariants.append(invariant)

    def validate(
        self,
        theta_old: np.ndarray,
        theta_new: np.ndarray,
        metadata: dict | None = None,
    ) -> None:
        """
        Run all registered invariants.

        Args:
            theta_old: pre-mutation parameter vector
            theta_new: post-mutation parameter vector
            metadata: optional context passed through to violation details

        Raises:
            InvariantViolation: on first invariant failure (fail-fast)
        """
        for invariant in self._invariants:
            invariant.validate(theta_old, theta_new)

    def validate_bulk(
        self,
        pairs: Sequence[tuple[np.ndarray, np.ndarray]],
        metadata: dict | None = None,
    ) -> list[InvariantViolation]:
        """
        Validate multiple mutations; collect all violations instead of fail-fast.

        Returns:
            List of InvariantViolation for each failed pair.
        """
        violations = []
        for i, (theta_old, theta_new) in enumerate(pairs):
            try:
                self.validate(theta_old, theta_new, metadata)
            except InvariantViolation as e:
                e.details["pair_index"] = i
                violations.append(e)
        return violations
