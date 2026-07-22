"""
message_signatures.py — Federation-level HMAC-based message signing for v9.8
"""
from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass


@dataclass
class SignedMessage:
    payload: str
    sender_id: str
    message_hash: str
    signature: str


class MessageSignatureError(Exception):
    pass


class FederationMessageSigning:
    """Simplified signature layer (HMAC-SHA256 over node_id+payload)."""

    def __init__(self, secret_cache: dict[str, str]):
        self._secrets = secret_cache

    def sign(self, sender_id: str, payload: str) -> SignedMessage:
        secret = self._get_secret(sender_id)
        message_hash = hashlib.sha256(payload.encode()).hexdigest()
        signature = hmac.new(secret.encode(), f"{sender_id}:{message_hash}".encode(), hashlib.sha256).hexdigest()
        return SignedMessage(payload=payload, sender_id=sender_id, message_hash=message_hash, signature=signature)

    def verify(self, signed: SignedMessage) -> bool:
        secret = self._get_secret(signed.sender_id)
        expected = hmac.new(secret.encode(), f"{signed.sender_id}:{signed.message_hash}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signed.signature):
            raise MessageSignatureError("signature mismatch")
        return True

    def _get_secret(self, sender_id: str) -> str:
        if sender_id not in self._secrets:
            raise MessageSignatureError(f"missing secret for {sender_id}")
        return self._secrets[sender_id]

__all__ = [
    "FederationMessageSigning",
    "MessageSignatureError",
    "SignedMessage",
]
