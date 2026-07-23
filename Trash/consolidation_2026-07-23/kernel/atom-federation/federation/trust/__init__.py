"""
federation.trust — v9.5 Distributed Trust Consistency Layer

Modules:
  trust_vector          — TrustVector, TrustEntry, TrustDelta
  ledger_reconciliation — deterministic merge function
  trust_sync_protocol   — gossip protocol for trust state
"""

from federation.trust.ledger_reconciliation import (
    ConflictReport,
    LedgerReconciliation,
    MergeDecision,
)
from federation.trust.trust_sync_protocol import (
    PeerTrustState,
    TrustMessageType,
    TrustSyncMessage,
    TrustSyncProtocol,
)
from federation.trust.trust_vector import TrustDelta, TrustEntry, TrustVector

__all__ = [
    "ConflictReport",
    "LedgerReconciliation",
    "MergeDecision",
    "PeerTrustState",
    "TrustDelta",
    "TrustEntry",
    "TrustMessageType",
    "TrustSyncMessage",
    "TrustSyncProtocol",
    "TrustVector",
]
