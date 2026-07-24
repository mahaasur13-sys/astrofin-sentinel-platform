"""
federation/security/inbound_security_gate.py — v9.9 FederationInboundSecurityGate

Provides a single enforcement point for all inbound federation messages.

Responsibilities:
  - Verify signatures via FederationMessageSigning (HMAC-SHA256)
  - Enforce replay protection via NonceSequenceValidator
  - Enforce origin policy via OriginPolicy
  - Emit SecurityGateResult (enforced flag, violation details)

Usage:
    gate = FederationInboundSecurityGate(
        signer=FederationMessageSigning(secrets),
        replay_validator=NonceSequenceValidator(window_size=100),
        origin_policy=OriginPolicy(mode=OriginMode.TRUST_THRESHOLD, trust_threshold=0.1),
    )

    result = gate.verify(
        envelope=SignedEnvelope.from_dict(raw),
        trust_score=trust_scores.get(envelope.sender_id, 0.0),
        category=MessageCategory.GOSSIP,
    )
    if not result.passed:
        raise SecurityGateError(result)
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from federation.byzantine.message_signatures import FederationMessageSigning
from federation.security.origin_policy import OriginPolicy, OriginViolation
import logging
log = logging.getLogger(__name__)

from federation.security.replay_protection import (
    NonceSequenceValidator,
    NonceStatus,
    ReplayProtectionError,
)
from federation.security.signed_envelope import EnvelopeError, MessageCategory, SignedEnvelope


class SecurityViolation(Exception):
    """General security gate violation."""


class SecurityGateError(Exception):
    """Raised when the security gate refuses a message."""


@dataclass
class SecurityGateResult:
    category: MessageCategory
    sender_id: str
    seq: int
    passed: bool
    violation: str | None = None
    details: dict | None = None


class FederationInboundSecurityGate:
    """
    Central enforcement gate for inbound federation messages.

    Verifies authenticity, replay, and origin policies uniformly.
    """

    def __init__(self,
        signer: FederationMessageSigning,
        replay_validator: NonceSequenceValidator,
        origin_policy: OriginPolicy,
        allowed_categories: set[MessageCategory] | None = None,
        rejection_hook: Callable[[SecurityGateResult], None] | None = None,
    ) -> None:
        self._signer = signer
        self._replay = replay_validator
        self._origin = origin_policy
        self._allowed_categories = allowed_categories or set(MessageCategory)
        self._rejection_hook = rejection_hook

    def verify(
        self,
        envelope: SignedEnvelope,
        trust_score: float | None = None,
    ) -> SecurityGateResult:
        """Verify envelope authenticity and policy compliance."""
        category = MessageCategory(envelope.category)
        if category not in self._allowed_categories:
            return self._reject(
                category,
                envelope.sender_id,
                envelope.seq,
                f"category {category} disallowed",
            )

        # 1. Signature + payload hash
        try:
            envelope.verify(self._signer)
        except EnvelopeError as exc:
            return self._reject(
                category,
                envelope.sender_id,
                envelope.seq,
                f"signature_invalid: {exc}",
            )

        # 2. Replay protection
        try:
            check = self._replay.check_and_record(
                sender_id=envelope.sender_id,
                seq=envelope.seq,
                ts_ns=envelope.ts_ns,
            )
        except ReplayProtectionError as exc:
            return self._reject(
                category,
                envelope.sender_id,
                envelope.seq,
                f"replay_validator_error: {exc}",
            )

        if check.status != NonceStatus.ACCEPTED:
            return self._reject(
                category,
                envelope.sender_id,
                envelope.seq,
                f"replay_rejected: {check.status.name}",
                details={
                    "gap": check.gap,
                    "age_ns": check.age_ns,
                    "window_summary": self._replay.window_summary().get(envelope.sender_id),
                },
            )

        # 3. Origin policy
        try:
            policy_result = self._origin.check(envelope.sender_id, trust_score)
        except OriginViolation as exc:
            return self._reject(
                category,
                envelope.sender_id,
                envelope.seq,
                f"origin_policy_violation: {exc}",
            )

        return SecurityGateResult(
            category=category,
            sender_id=envelope.sender_id,
            seq=envelope.seq,
            passed=True,
            details={
                "trust_score": policy_result.trust_score,
                "policy_mode": policy_result.mode.name,
            },
        )

    def _reject(
        self,
        category: MessageCategory,
        sender_id: str,
        seq: int,
        violation: str,
        details: dict | None = None,
    ) -> SecurityGateResult:
        result = SecurityGateResult(
            category=category,
            sender_id=sender_id,
            seq=seq,
            passed=False,
            violation=violation,
            details=details,
        )
        if self._rejection_hook:
            self._rejection_hook(result)
        raise SecurityGateError(result)


# ─── Constants (Invariant) ────────────────────────────────────────────────

INBOUND_MESSAGE_AUTHENTICITY_INVARIANT = "INBOUND_MESSAGE_AUTHENTICITY"


# ─── Tests ─────────────────────────────────────────────────────────────────

def _test_security_gate():
    from federation.byzantine.message_signatures import FederationMessageSigning
    from federation.security.origin_policy import OriginMode, OriginPolicy
    from federation.security.replay_protection import NonceSequenceValidator
    from federation.security.signed_envelope import EnvelopeBuilder

    secrets = {"node_A": "secret_A_123", "node_B": "secret_B_456"}
    signer = FederationMessageSigning(secrets)
    replay = NonceSequenceValidator(window_size=10)
    origin = OriginPolicy(mode=OriginMode.TRUST_THRESHOLD, trust_threshold=0.3)
    origin.update_trust_score("node_A", 0.5)

    gate = FederationInboundSecurityGate(
        signer=signer,
        replay_validator=replay,
        origin_policy=origin,
    )

    builder = EnvelopeBuilder(node_id="node_A", signer=signer)
    envelope = builder.wrap("{\"type\": \"TRUST_DELTA\"}", category=MessageCategory.TRUST)
    result = gate.verify(envelope, trust_score=0.5)
    assert result.passed is True
    log.info("✅ gate accept + trust policy OK")

    # ── replay rejection ────────────────────────────────────────────────
    try:
        gate.verify(envelope, trust_score=0.5)
        assert False, "duplicate should be rejected"
    except SecurityGateError as exc:
        assert exc.args[0].violation.startswith("replay_rejected")
        log.info("✅ gate rejects replayed envelope")

    # ── origin rejection ────────────────────────────────────────────────
    builder_b = EnvelopeBuilder(node_id="node_B", signer=signer)
    envelope_b = builder_b.wrap("{\"type\": \"GOSSIP\"}", category=MessageCategory.GOSSIP)
    try:
        gate.verify(envelope_b, trust_score=0.1)
        assert False
    except SecurityGateError as exc:
        assert "origin_policy_violation" in exc.args[0].violation
        log.info("✅ gate rejects low-trust sender")

    log.info("\n✅ v9.9 FederationInboundSecurityGate — all checks passed")


if __name__ == "__main__":
    _test_security_gate()
