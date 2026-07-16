#!/usr/bin/env python3
"""ROMA Auth Engine — API Keys, HMAC signing, tenant identity."""

import hashlib
import hmac
import secrets
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class KeyType(Enum):
    SERVER = "server"  # server-to-server
    USER = "user"  # user-facing
    WEBHOOK = "webhook"  # outbound callbacks


class KeyStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"  # created but not yet activated


@dataclass
class APIKey:
    key_id: str
    tenant_id: str
    project_id: str
    key_type: KeyType
    key_prefix: str  # first 8 chars for identification
    key_hash: str  # SHA256 of full key
    status: KeyStatus
    created_at: float
    expires_at: float | None
    last_used_at: float | None
    scopes: list[str]
    description: str


@dataclass
class Tenant:
    tenant_id: str
    name: str
    plan: str  # FREE | PRO | ENTERPRISE
    created_at: float
    api_keys: list[str]  # key_ids
    active: bool = True
    metadata: dict = field(default_factory=dict)


class AuthEngine:
    def __init__(self, secret_key: str | None = None):
        self.secret_key = secret_key or secrets.token_hex(32)
        self.keys: dict[str, APIKey] = {}  # key_id → APIKey
        self.key_index: dict[str, str] = {}  # key_prefix:key_hash → key_id
        self.tenants: dict[str, Tenant] = {}  # tenant_id → Tenant
        self.hmac_secrets: dict[str, str] = {}  # tenant_id → HMAC secret

    # ── Key Management ──────────────────────────────────────────────────────
    def create_key(
        self,
        tenant_id: str,
        project_id: str,
        key_type: KeyType,
        description: str,
        expires_at: float | None = None,
        scopes: list[str] | None = None,
    ) -> tuple[str, str]:
        """Create API key. Returns (key_id, full_secret). Secret shown ONLY once."""
        key_id = f"roma_{uuid.uuid4().hex[:16]}"
        full_secret = f"sk_{secrets.token_bytes(24).hex()}"
        prefix = full_secret[:8]
        key_hash = hashlib.sha256(full_secret.encode()).hexdigest()

        key = APIKey(
            key_id=key_id,
            tenant_id=tenant_id,
            project_id=project_id,
            key_type=key_type,
            key_prefix=prefix,
            key_hash=key_hash,
            status=KeyStatus.ACTIVE,
            created_at=time.time(),
            expires_at=expires_at,
            last_used_at=None,
            scopes=scopes or ["submit", "status", "cancel"],
            description=description,
        )
        self.keys[key_id] = key
        self.key_index[f"{prefix}:{key_hash}"] = key_id
        return key_id, full_secret

    def validate_key(self, full_secret: str) -> APIKey | None:
        """Validate secret, update last_used, return APIKey or None."""
        if len(full_secret) < 16:
            return None
        prefix = full_secret[:8]
        key_hash = hashlib.sha256(full_secret.encode()).hexdigest()
        key_id = self.key_index.get(f"{prefix}:{key_hash}")
        if not key_id:
            return None
        key = self.keys[key_id]
        if key.status != KeyStatus.ACTIVE:
            return None
        if key.expires_at and time.time() > key.expires_at:
            key.status = KeyStatus.EXPIRED
            return None
        key.last_used_at = time.time()
        return key

    def revoke_key(self, key_id: str) -> bool:
        if key_id in self.keys:
            self.keys[key_id].status = KeyStatus.REVOKED
            return True
        return False

    def rotate_key(self, key_id: str) -> tuple[str, str]:
        """Rotate key: revoke old, create new. Returns (key_id, new_secret)."""
        old = self.keys[key_id]
        self.revoke_key(key_id)
        return self.create_key(
            old.tenant_id,
            old.project_id,
            old.key_type,
            old.description,
            old.expires_at,
            old.scopes,
        )

    # ── Tenant Management ───────────────────────────────────────────────────
    def create_tenant(
        self,
        tenant_id: str,
        name: str,
        plan: str = "FREE",
        hmac_secret: str | None = None,
    ) -> Tenant:
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            plan=plan,
            created_at=time.time(),
            api_keys=[],
        )
        self.tenants[tenant_id] = tenant
        if hmac_secret:
            self.hmac_secrets[tenant_id] = hmac_secret
        return tenant

    def attach_key_to_tenant(self, tenant_id: str, key_id: str):
        if tenant_id in self.tenants:
            self.tenants[tenant_id].api_keys.append(key_id)

    # ── HMAC Signing ────────────────────────────────────────────────────────
    def create_hmac_secret(self, tenant_id: str) -> str:
        secret = secrets.token_hex(16)
        self.hmac_secrets[tenant_id] = secret
        return secret

    def sign_request(self, tenant_id: str, method: str, path: str, body: str, timestamp: float) -> str:
        """Create HMAC signature for request signing."""
        secret = self.hmac_secrets.get(tenant_id)
        if not secret:
            return ""
        msg = f"{method}:{path}:{body}:{timestamp}"
        return hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()

    def verify_signature(
        self,
        tenant_id: str,
        method: str,
        path: str,
        body: str,
        timestamp: float,
        signature: str,
    ) -> bool:
        """Verify HMAC signature. Reject if >5 min old."""
        if abs(time.time() - timestamp) > 300:
            return False
        expected = self.sign_request(tenant_id, method, path, body, timestamp)
        return hmac.compare_digest(expected, signature)

    # ── Enforcement ─────────────────────────────────────────────────────────
    def require_valid_key(self, full_secret: str) -> APIKey:
        """Validate or raise AuthError."""
        key = self.validate_key(full_secret)
        if not key:
            raise AuthError("invalid_or_expired_key", "API key is invalid, expired, or revoked")
        return key

    def require_tenant(self, tenant_id: str) -> Tenant:
        if tenant_id not in self.tenants:
            raise AuthError("tenant_not_found", f"Tenant {tenant_id} not found")
        return self.tenants[tenant_id]

    def require_scope(self, key: APIKey, scope: str):
        if scope not in key.scopes:
            raise AuthError("insufficient_scope", f"Missing required scope: {scope}")


class AuthError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


if __name__ == "__main__":
    # Demo
    auth = AuthEngine()
    t = auth.create_tenant("tenant-acme", "ACME Corp", "PRO")
    key_id, secret = auth.create_key(
        "tenant-acme",
        "proj-1",
        KeyType.SERVER,
        "Production key",
        scopes=["submit", "status", "cancel", "metering"],
    )
    auth.attach_key_to_tenant("tenant-acme", key_id)
    print(f"Tenant: {t.tenant_id} ({t.plan})")
    print(f"Key: {key_id} | Secret: {secret[:20]}...")
    validated = auth.validate_key(secret)
    print(f"Validated: {validated.key_id if validated else 'FAIL'}")
    print(f"Scopes: {validated.scopes if validated else 'N/A'}")

    # HMAC
    hmac_secret = auth.create_hmac_secret("tenant-acme")
    ts = time.time()
    sig = auth.sign_request("tenant-acme", "POST", "/api/v1/submit", '{"task":"test"}', ts)
    verify = auth.verify_signature("tenant-acme", "POST", "/api/v1/submit", '{"task":"test"}', ts, sig)
    print(f"HMAC verify: {verify}")
    print(
        f"Timestamp drift (+10min): {auth.verify_signature('tenant-acme', 'POST', '/api/v1/submit', '{\"task\":\"test\"}', ts - 600, sig)}"
    )
