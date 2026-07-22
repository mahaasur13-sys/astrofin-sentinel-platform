"""
byzantine/__init__.py — v9.8 Byzantine Fault Tolerance Hardening Layer

Scope (minimal correct PBFT-lite):
  1. FederationMessageSigning     — node_id + message_hash + HMAC-SHA256 signature
  2. QuorumCalculator             — f+1 / 2f+1 / 3f+1 quorum types
  3. ViewChangeManager            — leader rotation on entropy_freeze / trust_collapse / stalled_round
  4. PBFTLiteConsensusEngine      — PREPARE/COMMIT phases wired to existing consensus_resolver
  5. ByzantineDetector            — signals from TrustDynamicsStabilizer + ConsensusEntropyMonitor

Design constraints:
  - Signatures are pseudocode (HMAC-SHA256), not real PKI
  - view_change is cooperative (not PBFT SMR view-change), lightweight
  - PBFT phases integrate ON TOP of existing TrustWeightedConsensusResolver
  - ByzantineDetector feeds INTO TrustDynamicsStabilizer (trust collapse signal)

Usage:
    from federation.byzantine import (
        FederationMessageSigning,
        QuorumCalculator,
        ViewChangeManager,
        PBFTLiteConsensusEngine,
        ByzantineDetector,
    )
"""

from .byzantine_detector import ByzantineDetector, ByzantineSignal
from .message_signatures import FederationMessageSigning, MessageSignatureError, SignedMessage
from .pbft_consensus import ConsensusOutcome, PBFTLiteConsensusEngine, PBFTMessage, PBFTPhase
from .quorum import QuorumCalculator, QuorumResult, QuorumType
from .view_change import ViewChangeEvent, ViewChangeManager, ViewChangeReason

__all__ = [
    "ByzantineDetector",
    "ByzantineSignal",
    "ConsensusOutcome",
    "FederationMessageSigning",
    "MessageSignatureError",
    "PBFTLiteConsensusEngine",
    "PBFTMessage",
    "PBFTPhase",
    "QuorumCalculator",
    "QuorumResult",
    "QuorumType",
    "SignedMessage",
    "ViewChangeEvent",
    "ViewChangeManager",
    "ViewChangeReason",
]
