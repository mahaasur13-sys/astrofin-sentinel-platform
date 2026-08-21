"""Security — API key auth, tenant isolation, permission enforcement."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Tenant:
    """A tenant in the DecisionOS platform."""

    tenant_id: str
    tier: str = "Start"  # Start, Pro, Enterprise
    api_key_hash: str = ""
    created_at: str = ""
    features: dict[str, bool] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        self.features.setdefault("p2p_transfer", self.tier in ("Pro", "Enterprise"))
        self.features.setdefault("custom_relay", self.tier == "Enterprise")
        self.features.setdefault("marketplace", self.tier == "Enterprise")
        self.features.setdefault("custom_plugins", self.tier == "Enterprise")

    def can_use_plugin(self, required_tiers: list[str]) -> bool:
        """Check if this tenant can use a plugin."""
        tier_order = {"Start": 0, "Pro": 1, "Enterprise": 2}
        tenant_level = tier_order.get(self.tier, 0)
        for req in required_tiers:
            if tenant_level < tier_order.get(req, 0):
                return False
        return True


class AuthService:
    """API key authentication and authorization service."""

    def __init__(self):
        self._tenants: dict[str, Tenant] = {}
        self._api_keys: dict[str, str] = {}  # key_hash -> tenant_id

    def create_tenant(self, tenant_id: str, tier: str = "Start") -> Tenant:
        """Create a new tenant."""
        tenant = Tenant(tenant_id=tenant_id, tier=tier)
        self._tenants[tenant_id] = tenant
        return tenant

    def generate_api_key(self, tenant_id: str) -> str:
        """Generate a new API key for a tenant."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant '{tenant_id}' not found")

        raw_key = f"dos_{secrets.token_hex(24)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        tenant.api_key_hash = key_hash
        self._api_keys[key_hash] = tenant_id
        return raw_key

    def validate_api_key(self, api_key: str) -> Tenant | None:
        """Validate an API key and return the tenant."""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        tenant_id = self._api_keys.get(key_hash)
        if not tenant_id:
            return None
        return self._tenants.get(tenant_id)

    def get_tenant(self, tenant_id: str) -> Tenant | None:
        """Get a tenant by ID."""
        return self._tenants.get(tenant_id)

    def check_permission(self, tenant_id: str, permission: str) -> bool:
        """Check if a tenant has a specific permission."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return False

        # Map permissions to features
        perm_map = {
            "dashbeam:ticket:create": "p2p_transfer",
            "dashbeam:file:send": "p2p_transfer",
            "dashbeam:relay:configure": "custom_relay",
            "dashbeam:wallet:share_view_only": "p2p_transfer",
        }

        feature = perm_map.get(permission, permission)
        return tenant.features.get(feature, False)

    @staticmethod
    def hash_key(key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(key.encode()).hexdigest()

    @staticmethod
    def constant_time_compare(a: str, b: str) -> bool:
        """Constant-time string comparison."""
        return hmac.compare_digest(a, b)
