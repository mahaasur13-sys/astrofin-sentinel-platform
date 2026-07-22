"""
federation.trust_weighted — v9.7 Trust-Weighted Consensus Binding

Modules:
  node_weights            — TrustVector-backed node weight registry
  consensus_resolver      — TrustWeightedConsensusResolver
  skew_detector           — Trust skew + consensus domination + trust collapse detection
  trust_feedback_dampener — v9.7 EMA + decay + delta cap for trust updates
  trust_dynamics_stabilizer — v9.7 Full stabilization layer (entropy + anti-monopoly)

Key shift from v9.5→v9.6:
  trust is consistent (deterministic merge, convergence)
  v9.6→v9.7: trust becomes CONTROL VARIABLE (weights affect consensus outcome)
             AND now consensus outcome feeds back into trust.

v9.7 new feedback loop:
  trust → consensus → outcome → dampened_trust_update → trust

Anti-patterns solved in v9.7:
  trust monopolies        → AntiMonopolyConstraint (ceiling + gradient cap)
  phase locking          → ConsensusEntropyMonitor (entropy floor gating)
  consensus inertia      → entropy minimum enforced before acceptance
  Byzantine weight freeze → regime detection (BYZANTINE_FREEZE)
  feedback amplification → TrustFeedbackDampener (EMA + decay + delta cap)
"""

from federation.trust_weighted.consensus_resolver import (
    ConsensusShiftEvent,
    ConsensusShiftType,
    TrustWeightedConsensusResolver,
)
from federation.trust_weighted.node_weights import (
    NodeWeightRegistry,
    NodeWeightsSnapshot,
)
from federation.trust_weighted.skew_detector import (
    ConsensusDominationAlert,
    TrustCollapseAlert,
    TrustSkewDetector,
    TrustSkewReport,
)
from federation.trust_weighted.trust_dynamics_stabilizer import (
    AntiMonopolyConstraint,
    ConsensusEntropyMonitor,
    DynamicsReport,
    EntropyStats,
    MonopolyStats,
    TrustDynamicsStabilizer,
)
from federation.trust_weighted.trust_feedback_dampener import (
    DampenerConfig,
    FeedbackRegime,
    TrustFeedbackDampener,
    TrustUpdateResult,
)

__all__ = [
    # node_weights
    "NodeWeightRegistry",
    "NodeWeightsSnapshot",
    # consensus_resolver
    "TrustWeightedConsensusResolver",
    "ConsensusShiftEvent",
    "ConsensusShiftType",
    # skew_detector
    "TrustSkewDetector",
    "TrustSkewReport",
    "TrustCollapseAlert",
    "ConsensusDominationAlert",
    # v9.7 feedback stabilization
    "TrustFeedbackDampener",
    "TrustUpdateResult",
    "DampenerConfig",
    "FeedbackRegime",
    "TrustDynamicsStabilizer",
    "DynamicsReport",
    "EntropyStats",
    "MonopolyStats",
    "AntiMonopolyConstraint",
    "ConsensusEntropyMonitor",
]
