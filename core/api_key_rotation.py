"""API key rotation with grace period (24h)."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


@dataclass
class APIKey:
    prefix: str
    hash: str
    created_at: float
    expires_at: float
    active: bool = True


@dataclass
class KeyStore:
    current: APIKey | None = None
    previous: APIKey | None = None
    _grace_hours: float = 24.0

    def rotate(self, new_prefix: str) -> APIKey:
        raw = secrets.token_hex(8)
        key_hash = hashlib.sha256(raw.encode()).hexdigest()
        now = time.time()
        new_key = APIKey(
            prefix=new_prefix,
            hash=key_hash,
            created_at=now,
            expires_at=now + 365 * 86400,
        )
        if self.current:
            self.previous = self.current
            self.previous.expires_at = now + self._grace_hours * 3600
            self.previous.active = True
        self.current = new_key
        return new_key

    def validate(self, raw_key: str) -> bool:
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        for k in (self.current, self.previous):
            if k and k.active and k.expires_at > time.time():
                if hmac.compare_digest(k.hash, key_hash):
                    return True
        return False


key_store = KeyStore()

def get_key_store() -> KeyStore:
    return key_store
