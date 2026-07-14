"""
saas/branding/models.py
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Optional


class TenantBranding(BaseModel):
    tenant_id: str
    app_name: str = Field(..., description="Brand name — must contain VEGA")
    logo_url: Optional[str] = None
    primary_color: str = "#3b82f6"
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    support_email: str
    from_name: str = "VEGA GPU Cloud"
    custom_domain: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
