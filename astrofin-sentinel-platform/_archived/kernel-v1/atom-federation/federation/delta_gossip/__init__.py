"""
DeltaGossip — O(Δnodes) federation gossip with DAG fingerprint deltas.

Key design:
  - DeltaGossipMessage carries fingerprint delta, not full snapshot
  - Routing index: node_id → H(fingerprint) → last_seq
  - Selective propagation via AntiEntropy with merkle-tree diff
  - Event-driven convergence via ConvergeConsensus
  - Exponential backoff with jitter on push failures

Architecture:
  DeltaGossipProtocol  — delta-driven gossip (replaces full-vector push)
  DeltaMessageEnvelope — fingerprint + high-water mark + changed_node_ids
  AntiEntropy          — merkle-tree reconcile between two peers
  ConvergeConsensus    — delta-based quorum (uses DAGChange from fingerprint)
  DeltaRouter          — tracks per-node delta sequences for routing
"""

from federation.delta_gossip.anti_entropy import AntiEntropy
from federation.delta_gossip.consensus import ConvergeConsensus, ConvergeQuorumResult
from federation.delta_gossip.protocol import (
    DeltaGossipConfig,
    DeltaGossipMessage,
    DeltaGossipProtocol,
)
from federation.delta_gossip.routing import DeltaRouter

__all__ = [
    "AntiEntropy",
    "ConvergeConsensus",
    "ConvergeQuorumResult",
    "DeltaGossipConfig",
    "DeltaGossipMessage",
    "DeltaGossipProtocol",
    "DeltaRouter",
]
