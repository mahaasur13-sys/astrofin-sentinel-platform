"""
saas/tenants/manager.py
CRUD operations for tenant management.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from .models import Tenant, TenantCreate, TenantStatus, TenantUpdate


class TenantNotFoundError(Exception):
    pass


class TenantManager:
    def __init__(self) -> None:
        self._tenants: dict[str, Tenant] = {}

    # ── Create ─────────────────────────────────────────────────────────────────

    def create(self, data: TenantCreate) -> Tenant:
        tenant = data.make_tenant()
        self._tenants[tenant.tenant_id] = tenant
        return tenant

    # ── Read ───────────────────────────────────────────────────────────────────

    def get(self, tenant_id: str) -> Tenant:
        if tenant_id not in self._tenants:
            raise TenantNotFoundError(tenant_id)
        return self._tenants[tenant_id]

    def get_by_slug(self, slug: str) -> Tenant | None:
        for t in self._tenants.values():
            prefix = t.tenant_id.rsplit("-", 1)[0]
            if prefix == slug.lower():
                return t
        return None

    def list_all(self) -> list[Tenant]:
        return list(self._tenants.values())

    def list_active(self) -> list[Tenant]:
        return [t for t in self._tenants.values() if t.status == TenantStatus.ACTIVE]

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, tenant_id: str, data: TenantUpdate) -> Tenant:
        tenant = self.get(tenant_id)
        patch = data.model_dump(exclude_unset=True)

        for field, value in patch.items():
            if field == "branding" and value is not None:
                tenant.branding = tenant.branding.model_copy(update=value)
            else:
                setattr(tenant, field, value)

        tenant.updated_at = datetime.utcnow()
        return tenant

    def suspend(self, tenant_id: str) -> Tenant:
        return self.update(tenant_id, TenantUpdate(status=TenantStatus.SUSPENDED))

    def activate(self, tenant_id: str) -> Tenant:
        return self.update(tenant_id, TenantUpdate(status=TenantStatus.ACTIVE))

    # ── Delete ────────────────────────────────────────────────────────────────

    def delete(self, tenant_id: str) -> None:
        if tenant_id not in self._tenants:
            raise TenantNotFoundError(tenant_id)
        del self._tenants[tenant_id]

    # ── Stats ─────────────────────────────────────────────────────────────────

    def summary(self) -> dict:
        tenants = self.list_all()
        by_status = {}
        by_tier = {}
        for t in tenants:
            by_status[t.status.value] = by_status.get(t.status.value, 0) + 1
            by_tier[t.tier.value] = by_tier.get(t.tier.value, 0) + 1
        return {
            "total": len(tenants),
            "by_status": by_status,
            "by_tier": by_tier,
        }
