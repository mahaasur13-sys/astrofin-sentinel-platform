"""Gateway configuration schemas."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum


class RateLimitStrategy(str, Enum):
    TOKEN_BUCKET = "token_bucket"
    SLOWAPI = "slowapi"
    IN_MEMORY = "in_memory"


class RateLimitConfig(BaseModel):
    enabled: bool = True
    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET
    requests_per_minute: int = Field(default=60, ge=1, le=10000)
    burst_size: int = Field(default=10, ge=1, le=1000)
    redis_url: Optional[str] = None  # redis://host:6379/0
    use_redis: bool = False  # auto-detect


class BrandingConfig(BaseModel):
    enabled: bool = True
    inject_html_prefix: bool = False  # inject branding into HTML responses
    inject_headers: bool = True  # X-Tenant-ID, X-Branding-Version
    custom_css_url: Optional[str] = None
    logo_url: Optional[str] = None
    support_email: Optional[str] = None
    terms_url: Optional[str] = None
    privacy_url: Optional[str] = None


class AuthConfig(BaseModel):
    enabled: bool = True
    require_api_key: bool = True
    require_jwt: bool = False  # optional second factor
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    api_key_header: str = "X-API-Key"
    allowed_origins: list[str] = ["*"]


class TenantGatewayConfig(BaseModel):
    tenant_id: str
    display_name: str
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    branding: BrandingConfig = Field(default_factory=BrandingConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    custom_headers: Dict[str, str] = {}
    metadata: Dict[str, Any] = {}


class GatewayConfig(BaseModel):
    default_rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    default_branding: BrandingConfig = Field(default_factory=BrandingConfig)
    default_auth: AuthConfig = Field(default_factory=AuthConfig)
    tenants: Dict[str, TenantGatewayConfig] = {}
    global_headers: Dict[str, str] = {
        "X-Gateway": "roma-execution-bridge",
        "X-Gateway-Version": "1.0.0",
    }
