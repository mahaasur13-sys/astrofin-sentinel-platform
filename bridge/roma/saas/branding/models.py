"""
saas/branding/models.py
"""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


class TenantBranding(BaseModel):
    tenant_id: str
    app_name: str = Field(..., description="Brand name — must contain VEGA")
    logo_url: str | None = None
    primary_color: str = "#3b82f6"
    secondary_color: str | None = None
    accent_color: str | None = None
    support_email: str
    from_name: str = "VEGA GPU Cloud"
    custom_domain: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
