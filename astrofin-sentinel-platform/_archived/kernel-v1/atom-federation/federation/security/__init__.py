"""
federation/security/ — v9.9 Federation Inbound Security Gate

Single cryptographic enforcement point for all inbound federation messages.

Modules:
    inbound_security_gate  — FederationInboundSecurityGate
    replay_protection      — NonceSequenceValidator (sliding window anti-replay)
    signed_envelope        — SignedEnvelope wrapper
    origin_policy           — OriginPolicy (whitelist / trust_threshold)

Usage:
    gate = FederationInboundSecurityGate(
        signing=FederationMessageSigning(secrets),
        replay_window=100,
        default_policy=OriginPolicy(trust_threshold=0.1),
    )

    # TrustSyncProtocol
    gate.verify(trust_sync_msg, sender_id="node_A", msg_type=MessageCategory.TRUST)

    # DeltaGossipProtocol
    gate.verify(delta_gossip_msg, sender_id="node_B", msg_type=MessageCategory.GOSSIP)
"""

from federation.security.inbound_security_gate import (
    FederationInboundSecurityGate,
    MessageCategory,
    SecurityGateError,
    SecurityGateResult,
    SecurityViolation,
)
from federation.security.origin_policy import OriginPolicy, OriginViolation
from federation.security.replay_protection import NonceSequenceValidator, ReplayProtectionError
from federation.security.signed_envelope import EnvelopeError, SignedEnvelope

__all__ = [
    "EnvelopeError",
    "FederationInboundSecurityGate",
    "MessageCategory",
    "NonceSequenceValidator",
    "OriginPolicy",
    "OriginViolation",
    "ReplayProtectionError",
    "SecurityGateError",
    "SecurityGateResult",
    "SecurityViolation",
    "SignedEnvelope",
]
