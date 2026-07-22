"""
dag_hash_modes.py — v8.5 Semantic separation of DAG hash contracts

Two distinct hash semantics for two distinct use-cases:

CONSENSUS (unordered):
  - Children order does NOT matter
  - Used by: federation, state_vector, gossip, anti-entropy
  - Hash = sha256(sorted([left_digest, right_digest]))

CAUSAL (ordered):
  - Children order DOES matter
  - Used by: replay validation, execution traces, plan_graph
  - Hash = sha256(left_digest || right_digest)  [left then right]

Invariant contract: the same DAG structure must produce
ONE AND ONLY ONE canonical hash per mode.

Usage:
    from federation.delta_gossip.dag_hash_modes import DAGHashMode, dag_hash

    # Consensus (federation/gossip)
    digest = dag_hash(left_digest, right_digest, mode=DAGHashMode.CONSENSUS)

    # Causal (replay/plan_graph)
    digest = dag_hash(left_digest, right_digest, mode=DAGHashMode.CAUSAL)
"""

from __future__ import annotations

import hashlib
from enum import Enum, auto


class DAGHashMode(Enum):
    """
    Hash mode determines the semantic of combining parent digests.

    CONSENSUS  — unordered; order of children is irrelevant.
                 Suitable for federation state reconciliation,
                 gossip protocols, quorum decisions.

    CAUSAL     — ordered; left-to-right ordering is part of the hash.
                 Suitable for deterministic replay, causal traces,
                 execution order verification.
    """
    CONSENSUS = auto()
    CAUSAL = auto()


def dag_hash(left_digest: str, right_digest: str, mode: DAGHashMode) -> str:
    """
    Combine two parent digests into a parent digest, respecting mode.

    CONSENSUS: deterministic regardless of child ordering.
    CAUSAL:    deterministic with fixed left-to-right ordering.

    Args:
        left_digest:  digest of the left child
        right_digest: digest of the right child
        mode:         DAGHashMode.CONSENSUS or DAGHashMode.CAUSAL

    Returns:
        SHA256 hexdigest (first 16 chars by default convention)
    """
    if mode == DAGHashMode.CONSENSUS:
        # Order does not matter: sort before hashing
        parts = sorted([left_digest, right_digest])
        combined = "".join(parts)
    elif mode == DAGHashMode.CAUSAL:
        # Order matters: left then right (fixed)
        combined = left_digest + right_digest
    else:
        raise ValueError(f"Unknown DAGHashMode: {mode}")

    return hashlib.sha256(combined.encode()).hexdigest()


def dag_hash_n(children: list[str], mode: DAGHashMode) -> str:
    """
    Combine N children into one parent digest (binary tree reduction).

    CONSENSUS mode:  children sorted first → canonical unordered hash
                     Commutative: any permutation of children → same digest.
                     For federation, gossip, anti-entropy.

    CAUSAL mode:     children reduced left-to-right (NO sorting).
                     Non-commutative: different orderings → different digests.
                     For replay, execution traces, causal lineage.

    Args:
        children: list of child digests to combine
        mode:     DAGHashMode.CONSENSUS or DAGHashMode.CAUSAL

    Returns:
        SHA256 hexdigest of the combined parent
    """
    if not children:
        return ""

    if len(children) == 1:
        return children[0]

    # CONSENSUS: sort first, then pair left-to-right
    # CAUSAL: pair left-to-right directly (no sorting preserves order)
    if mode == DAGHashMode.CONSENSUS:
        reduction_list = sorted(children)
    else:  # CAUSAL
        reduction_list = list(children)

    while len(reduction_list) > 1:
        next_level: list[str] = []
        for i in range(0, len(reduction_list), 2):
            pair = reduction_list[i:i + 2]
            if len(pair) == 2:
                next_level.append(dag_hash(pair[0], pair[1], mode))
            else:
                next_level.append(pair[0])
        reduction_list = next_level

    return reduction_list[0]


def verify_consistency(
    digest_a: str,
    digest_b: str,
    mode: DAGHashMode,
) -> bool:
    """
    Check whether two digests are equal under the same mode semantics.

    Useful for federation reconciliation: both peers must arrive
    at the same root digest if their state is identical.
    """
    return digest_a == digest_b  # same mode → same result


__all__ = [
    "DAGHashMode",
    "dag_hash",
    "dag_hash_n",
    "verify_consistency",
]
