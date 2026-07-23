"""
AntiEntropy — merkle-tree reconciliation between federation peers.

Implements the Scoop algorithm for efficient state reconciliation:
  1. Compare merkle tree roots
  2. If equal → state in sync, done
  3. If not equal → traverse differing levels to find exact mismatches
  4. Exchange only missing/differing nodes

This turns O(n) full-state comparison into O(log n) exchanges.

Usage:
    ae = AntiEntropy()
    digests = ae.compute_merkle_tree(all_node_hashes)
    delta = ae.compute_remote_digest(their_root, digests)
    to_pull, to_push = delta['missing'], delta['extra']
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from federation.delta_gossip.dag_hash_modes import DAGHashMode, dag_hash


@dataclass
class MerkleNode:
    """Single node in a merkle tree."""
    digest: str          # hash of this subtree
    node_ids: list[str]  # all node IDs in this subtree
    left: MerkleNode | None = None
    right: MerkleNode | None = None
    is_leaf: bool = False
    hash_mode: DAGHashMode = DAGHashMode.CONSENSUS  # v9.0: mode propagation

    @property
    def height(self) -> int:
        if self.is_leaf:
            return 0
        l = self.left.height if self.left else -1
        r = self.right.height if self.right else -1
        return max(l, r) + 1


class AntiEntropy:
    """
    Merkle-tree based anti-entropy for DAG federation.

    Exchanges O(log n) digests instead of O(n) node hashes.

    Algorithm (Scoop-style):
      - Both peers compute merkle tree of their DAG state
      - Exchange root digests
      - If roots match → in sync
      - If not → recursively find subtrees that differ
      - Exchange only nodes in differing subtrees
    """

    def __init__(self, hash_size: int = 16):
        self.hash_size = hash_size

    # ── merkle tree construction ─────────────────────────────────

    def build_tree(self, node_hashes: dict[str, str], mode: DAGHashMode = DAGHashMode.CONSENSUS) -> MerkleNode:
        """
        Build a full merkle tree from {node_id: content_hash}.

        Returns the root MerkleNode with hash_mode set.
        """
        if not node_hashes:
            return self._empty_leaf("")

        # Layer 0: leaves — store mode in each node
        items = sorted(node_hashes.items())
        leaves = [
            self._make_leaf(nid, h, mode) for nid, h in items
        ]

        # Build upward — parents inherit mode
        while len(leaves) > 1:
            parent_level: list[MerkleNode] = []
            for i in range(0, len(leaves), 2):
                pair = leaves[i:i + 2]
                if len(pair) == 2:
                    parent = self._make_parent(pair[0], pair[1], mode)
                else:
                    parent = pair[0]
                parent_level.append(parent)
            leaves = parent_level

        return leaves[0]

    def _make_leaf(self, node_id: str, content_hash: str, mode: DAGHashMode = DAGHashMode.CONSENSUS) -> MerkleNode:
        digest = hashlib.sha256(content_hash.encode()).hexdigest()[:self.hash_size]
        return MerkleNode(
            digest=digest,
            node_ids=[node_id],
            is_leaf=True,
            hash_mode=mode,
        )

    def _make_parent(self, left: MerkleNode, right: MerkleNode, mode: DAGHashMode = DAGHashMode.CONSENSUS) -> MerkleNode:
        combined_ids = left.node_ids + right.node_ids
        combined_digest = dag_hash(
            left.digest, right.digest, mode
        )
        return MerkleNode(
            digest=combined_digest,
            node_ids=combined_ids,
            left=left,
            right=right,
            is_leaf=False,
            hash_mode=mode,
        )

    def _empty_leaf(self, digest: str) -> MerkleNode:
        return MerkleNode(digest=digest, node_ids=[], is_leaf=True)

    # ── merkle digest (layered hash) ─────────────────────────────

    def merkle_digest(self, node_hashes: dict[str, str], mode: DAGHashMode = DAGHashMode.CONSENSUS) -> dict[int, str]:
        """
        Compute layered merkle digest.

        Returns dict: layer_index → digest string

        Layer 0: sha256 of all {node_id: content_hash} items (sorted → CONSENSUS)
        Layer 1+: dag_hash of pairs (sorted → CONSENSUS, original order → CAUSAL)

        This is used by DeltaGossipProtocol for quick root comparison.
        """
        if not node_hashes:
            return {0: ""}

        if mode == DAGHashMode.CONSENSUS:
            sorted_hashes = sorted(node_hashes.items())
            layer0 = {nid: h for nid, h in sorted_hashes}
        else:
            # CAUSAL: preserve original insertion order
            layer0 = dict(node_hashes)

        digest_by_layer: dict[int, str] = {0: self._hash_dict(layer0)}
        current = layer0
        L = 1

        while len(current) > 1:
            next_layer: dict[str, str] = {}
            items = list(current.items())
            for i in range(0, len(items), 2):
                pair = items[i:i + 2]
                if len(pair) == 2:
                    key = f"{pair[0][0]}:{pair[1][0]}"
                    val = dag_hash(pair[0][1], pair[1][1], mode)
                else:
                    key, val = pair[0]
                next_layer[key] = val
            digest_by_layer[L] = self._hash_dict(next_layer)
            current = next_layer
            L += 1

        return digest_by_layer

    def _hash_dict(self, items: dict[str, str]) -> str:
        h = hashlib.sha256()
        for k in sorted(items):
            h.update(f"{k}:{items[k]}".encode())
        return h.hexdigest()[:self.hash_size]

    # ── reconciliation ──────────────────────────────────────────

    def reconcile(
        self,
        my_hashes: dict[str, str],
        their_hashes: dict[str, str],
        mode: DAGHashMode = DAGHashMode.CONSENSUS,
    ) -> tuple[list[str], list[str], list[str]]:
        """
        Compare my DAG state with a peer's DAG state.

        Returns (missing_on_my_side, missing_on_their_side, content_differ):
          - missing_on_my_side: node IDs they have but I don't
          - missing_on_their_side: node IDs I have but they don't
          - content_differ: node IDs both have but different content
        """
        my_ids = set(my_hashes.keys())
        their_ids = set(their_hashes.keys())

        missing_on_my_side = list(their_ids - my_ids)
        missing_on_their_side = list(my_ids - their_ids)
        content_differ = [
            nid for nid in my_ids & their_ids
            if my_hashes[nid] != their_hashes[nid]
        ]

        return missing_on_my_side, missing_on_their_side, content_differ

    def reconcile_with_digests(
        self,
        my_root_digest: str,
        my_hashes: dict[str, str],
        their_root_digest: str,
        their_hashes: dict[str, str],
        mode: DAGHashMode = DAGHashMode.CONSENSUS,
    ) -> dict[str, any]:
        """
        High-level reconcile using merkle digests.

        If roots match → fast path (in sync).
        If not → full reconciliation.

        Returns dict with reconciliation results.
        """
        if my_root_digest == their_root_digest and my_hashes == their_hashes:
            return {
                "in_sync": True,
                "missing_on_my_side": [],
                "missing_on_their_side": [],
                "content_differ": [],
            }

        missing_mine, missing_theirs, differ = self.reconcile(my_hashes, their_hashes, mode)

        return {
            "in_sync": False,
            "missing_on_my_side": missing_mine,
            "missing_on_their_side": missing_theirs,
            "content_differ": differ,
            "delta_byte_size": sum(len(k) + len(v) for k, v in my_hashes.items() if k in missing_theirs),
        }

    # ── merkle proof ─────────────────────────────────────────────

    def prove_membership(self, node_id: str, node_hashes: dict[str, str]) -> list[str]:
        """
        Generate merkle proof: path of digests proving node_id is in tree.

        Returns list of sibling digests from leaf to root.
        """
        if node_id not in node_hashes:
            return []

        tree = self.build_tree(node_hashes)
        return self._prove_membership_rec(tree, node_id)

    def _prove_membership_rec(self, node: MerkleNode, node_id: str) -> list[str]:
        if node.is_leaf:
            if node.node_ids == [node_id]:
                return []
            return []

        proof = []
        if node.left and node_id in node.left.node_ids:
            proof.append(node.right.digest if node.right else "")
            proof.extend(self._prove_membership_rec(node.left, node_id))
        elif node.right and node_id in node.right.node_ids:
            proof.append(node.left.digest if node.left else "")
            proof.extend(self._prove_membership_rec(node.right, node_id))

        return proof

    def verify_proof(
        self,
        node_id: str,
        content_hash: str,
        proof: list[str],
        root_digest: str,
        mode: DAGHashMode = DAGHashMode.CONSENSUS,
    ) -> bool:
        """
        Verify a merkle proof.

        Args:
            node_id: the node being proven
            content_hash: hash of the node's content
            proof: sibling digests from prove_membership (bottom-up order)
            root_digest: expected root digest
            mode: DAGHashMode — must match the mode used in build_tree
        """
        current = hashlib.sha256(content_hash.encode()).hexdigest()[:self.hash_size]
        for sibling in reversed(proof):
            current = dag_hash(current, sibling, mode)
        return current == root_digest
