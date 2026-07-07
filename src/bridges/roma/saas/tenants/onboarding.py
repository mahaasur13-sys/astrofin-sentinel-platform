"""saas.tenants.onboarding — Tenant onboarding wizard."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class OnboardingStep(str, Enum):
    BASIC_INFO = "basic_info"
    BRANDING = "branding"
    BILLING_SETUP = "billing_setup"
    STRIPE_CONNECT = "stripe_connect"
    READY = "ready"


@dataclass
class BrandingData:
    app_name: str = "ROMA"
    primary_color: str = "#6366f1"
    secondary_color: str = "#8b5cf6"
    logo_url: str = ""
    dashboard_url: str = ""
    support_email: str = ""
    support_url: str = ""
    terms_url: str = ""
    privacy_url: str = ""


@dataclass
class BillingSetup:
    billing_email: str = ""
    billing_name: str = ""
    address_country: str = ""
    address_city: str = ""
    address_line: str = ""


@dataclass
class OnboardingSession:
    display_name: str
    slug: str
    email: str
    revenue_share: float
    tier: str = "pro"
    step: OnboardingStep = OnboardingStep.BASIC_INFO
    branding: BrandingData = field(default_factory=BrandingData)
    billing: BillingSetup = field(default_factory=BillingSetup)
    stripe_onboarding_url: str = ""
    tenant_id: str = ""
    errors: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def _validate_slug(self) -> bool:
        if not re.match(r"^[a-z0-9][a-z0-9-]{2,62}[a-z0-9]$", self.slug):
            self.errors.append(f"Invalid slug: '{self.slug}' (use lowercase letters, numbers, hyphens)")
            return False
        return True

    def _validate_email(self) -> bool:
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", self.email):
            self.errors.append(f"Invalid email: '{self.email}'")
            return False
        return True

    def _validate_revenue_share(self) -> bool:
        if not (5.0 <= self.revenue_share <= 30.0):
            self.errors.append(f"Revenue share must be 5-30%, got {self.revenue_share}%")
            return False
        return True

    def set_branding(self, app_name: str, primary_color: str = "#6366f1", **kwargs: Any) -> OnboardingSession:
        self.branding = BrandingData(app_name=app_name, primary_color=primary_color, **kwargs)
        self.step = OnboardingStep.BRANDING
        return self

    def create_tenant(self) -> tuple[OnboardingSession, dict[str, Any] | None]:
        self.errors.clear()
        if not self._validate_slug():
            return self, None
        if not self._validate_email():
            return self, None
        if not self._validate_revenue_share():
            return self, None

        self.tenant_id = f"{self.slug}-{uuid.uuid4().hex[:8]}"
        tenant = {
            "id": self.tenant_id,
            "display_name": self.display_name,
            "slug": self.slug,
            "email": self.email,
            "revenue_share": self.revenue_share,
            "tier": self.tier,
            "branding": {
                "app_name": self.branding.app_name,
                "primary_color": self.branding.primary_color,
                "secondary_color": self.branding.secondary_color,
                "logo_url": self.branding.logo_url,
                "dashboard_url": self.branding.dashboard_url,
                "support_email": self.branding.support_email,
                "support_url": self.branding.support_url,
                "terms_url": self.branding.terms_url,
                "privacy_url": self.branding.privacy_url,
            },
            "billing": {
                "billing_email": self.billing.billing_email,
                "billing_name": self.billing.billing_name,
                "address_country": self.billing.address_country,
                "address_city": self.billing.address_city,
                "address_line": self.billing.address_line,
            },
            "status": "active",
            "created_at": self.created_at,
        }
        self.step = OnboardingStep.BILLING_SETUP
        return self, tenant

    def start_stripe_onboarding(self, return_url: str = "https://dashboard.roma.ai/stripe/return", refresh_url: str = "https://dashboard.roma.ai/stripe/refresh") -> OnboardingSession:
        self.stripe_onboarding_url = (
            f"https://connect.stripe.com/oauth/authorize?response_type=code&client_id={{ROM_A_STOR E_CLIENT_ID}}&scope=read_write&redirect_uri={return_url}&state={self.tenant_id}"
        )
        self.step = OnboardingStep.STRIPE_CONNECT
        return self

    def complete_stripe_onboarding(self, stripe_user_id: str = "") -> OnboardingSession:
        self.step = OnboardingStep.READY
        return self

    def get_status(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "step": self.step.value,
            "errors": self.errors,
            "stripe_onboarding_url": self.stripe_onboarding_url,
            "progress": {
                "basic_info": True,
                "branding": self.step in (OnboardingStep.BRANDING, OnboardingStep.BILLING_SETUP, OnboardingStep.STRIPE_CONNECT, OnboardingStep.READY),
                "billing_setup": self.step in (OnboardingStep.BILLING_SETUP, OnboardingStep.STRIPE_CONNECT, OnboardingStep.READY),
                "stripe_connect": self.step == OnboardingStep.READY,
            },
        }


if __name__ == "__main__":
    s = OnboardingSession(display_name="VEGA Cloud", slug="vega-kz", email="ops@vega.kz", revenue_share=15.0)
    s, tenant = s.create_tenant()
    print(f"Tenant: {tenant['id']}")
    print(f"Step: {s.step.value}")
    s.set_branding("VEGA Cloud", "#E53935")
    s.start_stripe_onboarding()
    print(f"Stripe: {s.stripe_onboarding_url[:60]}...")
    print(f"Status: {s.get_status()}")
