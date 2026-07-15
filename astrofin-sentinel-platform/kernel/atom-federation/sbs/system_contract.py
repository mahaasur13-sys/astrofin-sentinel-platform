"""
SYSTEM_CONTRACT — hard constraints of ATOMFederationOS.

These invariants CANNOT be bypassed by any runtime layer.
All layers (DRL / CCL / F2 / DESC) MUST respect these rules.

Usage
-----
>>> ok = SYSTEM_CONTRACT.verify("quorum_required_for_commit", True)
>>> ok
True
"""

from __future__ import annotations

from enum import Enum


class InvariantType(Enum):
    """Canonical list of system-wide invariants."""

    NO_SPLIT_BRAIN_COMMIT = "no_split_brain_commit"
    QUORUM_REQUIRED_FOR_COMMIT = "quorum_required_for_commit"
    DESC_IS_IMMUTABLE = "desc_is_immutable"
    CCL_CONTRACT_MUST_HOLD = "cc_l_contract_must_hold"
    DRL_MUST_PRESERVE_CAUSALITY = "drl_must_preserve_causality"
    LEADER_UNIQUENESS = "leader_uniqueness"
    MONOTONIC_COMMIT_INDEX = "monotonic_commit_index"
    NO_UNCOMMITTED_READS = "no_uncommitted_reads"
    BYZANTINE_DETECTION_ENABLED = "byzantine_detection_enabled"
    TEMPORAL_CONSISTENCY = "temporal_consistency"


class SYSTEM_CONTRACT:
    """
    Hard constraints registry.

    Each key is an invariant name; value must always be True in production.
    Any layer reporting a violation MUST halt or recover.
    """

    INVARIANTS: dict[str, bool] = {
        # Core consensus
        "no_split_brain_commit": True,
        "quorum_required_for_commit": True,
        "leader_uniqueness": True,
        "monotonic_commit_index": True,
        # DESC
        "desc_is_immutable": True,
        "desc_append_only": True,
        # CCL
        "cc_l_contract_must_hold": True,
        "no_uncommitted_reads": True,
        # DRL
        "drl_must_preserve_causality": True,
        "temporal_consistency": True,
        # Byzantine
        "byzantine_detection_enabled": True,
    }

    @staticmethod
    def verify(invariant_name: str, value: bool) -> bool:
        """
        Verify a single invariant value against the contract.

        Parameters
        ----------
        invariant_name : str
            Key from INVARIANTS dict.
        value : bool
            Actual value reported by a layer.

        Returns
        -------
        bool
            True if value matches the contract expectation.

        Raises
        ------
        KeyError
            If invariant_name is not in the contract.
        """
        expected = SYSTEM_CONTRACT.INVARIANTS[invariant_name]
        return expected == value

    @staticmethod
    def verify_all(reported: dict[str, bool]) -> tuple[bool, list[str]]:
        """
        Verify multiple invariants at once.

        Parameters
        ----------
        reported : dict[str, bool]
            Mapping of invariant_name → reported_value.

        Returns
        -------
        tuple[bool, list[str]]
            (all_ok, violations) — violations is list of "{name}: expected X, got Y"
        """
        violations: list[str] = []
        for name, value in reported.items():
            if name not in SYSTEM_CONTRACT.INVARIANTS:
                violations.append(f"UNKNOWN_INVARIANT: {name}")
                continue
            expected = SYSTEM_CONTRACT.INVARIANTS[name]
            if expected != value:
                violations.append(
                    f"CONTRACT_VIOLATION: {name} — expected {expected}, got {value}"
                )
        return len(violations) == 0, violations

    @staticmethod
    def list_invariants() -> list[str]:
        """Return all defined invariant names."""
        return list(SYSTEM_CONTRACT.INVARIANTS.keys())

    @staticmethod
    def is_loaded() -> bool:
        """Return True if contract is loaded (always true; for future plugin use)."""
        return True
