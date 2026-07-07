"""
saas/tenants/models.py
Tenant model for white-label management.
"""

from __future__ import annotations

import random
import string
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TenantStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class TenantTier(str, Enum):
    STARTER = "starter"  # ≤ $100 MRR
    GROWTH = "growth"  # ≤ $1,000 MRR
    SCALE = "scale"  # ≤ $10,000 MRR
    ENTERPRISE = "enterprise"  # > $10,000 MRR


def generate_tenant_id(slug: str) -> str:
    suffix = "".join(random.choices(string.digits, k=4))
    return f"{slug.lower().replace(' ', '-')}-{suffix}"


class TenantBase(BaseModel):
    tenant_id: str
    display_name: str
    status: TenantStatus = TenantStatus.ACTIVE
    revenue_share_percent: int = Field(default=15, ge=0, le=50)
    tier: TenantTier = TenantTier.STARTER


class TenantBrandingMinimal(BaseModel):
    app_name: str = "ROMA"
    primary_color: str = "#6366F1"
    logo_url: Optional[str] = None
    support_email: str = "support@roma.ai"
    website_url: Optional[str] = None


class Tenant(TenantBase):
    branding: TenantBrandingMinimal = Field(default_factory=TenantBrandingMinimal)
    stripe_connect_account_id: Optional[str] = None
    contact_email: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_summary(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "display_name": self.display_name,
            "status": self.status.value,
            "tier": self.tier.value,
            "revenue_share_percent": self.revenue_share_percent,
            "contact_email": self.contact_email,
            "created_at": self.created_at.isoformat(),
        }


class TenantCreate(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=128)
    slug: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    contact_email: str
    revenue_share_percent: int = Field(default=15, ge=0, le=50)
    tier: TenantTier = TenantTier.STARTER
    branding: Optional[TenantBrandingMinimal] = None

    def make_tenant(self) -> Tenant:
        tenant_id = generate_tenant_id(self.slug)
        return Tenant(
            tenant_id=tenant_id,
            display_name=self.display_name,
            contact_email=self.contact_email,
            revenue_share_percent=self.revenue_share_percent,
            tier=self.tier,
            branding=self.branding or TenantBrandingMinimal(),
        )


class TenantUpdate(BaseModel):
    display_name: Optional[str] = None
    status: Optional[TenantStatus] = None
    revenue_share_percent: Optional[int] = Field(default=None, ge=0, le=50)
    tier: Optional[TenantTier] = None
    branding: Optional[TenantBrandingMinimal] = None
    stripe_connect_account_id: Optional[str] = None
