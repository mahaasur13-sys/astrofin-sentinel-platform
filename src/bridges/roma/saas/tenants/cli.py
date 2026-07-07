#!/usr/bin/env python3
"""saas.tenants.cli — Tenant management CLI."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from saas.tenants.onboarding import OnboardingSession


_TENANTS_FILE = Path(__file__).parent.parent / "tenants.json"


def _load_tenants() -> dict:
    if _TENANTS_FILE.exists():
        return json.loads(_TENANTS_FILE.read_text())
    return {}


def _save_tenants(data: dict) -> None:
    _TENANTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _TENANTS_FILE.write_text(json.dumps(data, indent=2))


def cmd_create(args: argparse.Namespace) -> None:
    s = OnboardingSession(
        display_name=args.display_name,
        slug=args.slug,
        email=args.email,
        revenue_share=args.revenue_share,
        tier=args.tier,
    )
    if args.app_name:
        s.set_branding(args.app_name, primary_color=args.color or "#6366f1")
    s, tenant = s.create_tenant()
    if s.errors:
        for err in s.errors:
            print(f"ERROR: {err}")
        sys.exit(1)
    data = _load_tenants()
    data[tenant["id"]] = tenant
    _save_tenants(data)
    print(f"✅ Tenant created: {tenant['id']}")
    print(f"   Slug: {tenant['slug']}")
    print(f"   Revenue share: {tenant['revenue_share']}%")
    print(f"   Tier: {tenant['tier']}")


def cmd_list(args: argparse.Namespace) -> None:
    data = _load_tenants()
    if not data:
        print("No tenants found.")
        return
    for t in data.values():
        status = t.get("status", "unknown")
        print(f"[{status}] {t['id']} — {t['display_name']} ({t['email']})")


def cmd_get(args: argparse.Namespace) -> None:
    data = _load_tenants()
    t = data.get(args.tenant_id)
    if not t:
        print(f"Tenant not found: {args.tenant_id}")
        sys.exit(1)
    print(json.dumps(t, indent=2))


def cmd_suspend(args: argparse.Namespace) -> None:
    data = _load_tenants()
    t = data.get(args.tenant_id)
    if not t:
        print(f"Tenant not found: {args.tenant_id}")
        sys.exit(1)
    t["status"] = "suspended"
    _save_tenants(data)
    print(f"✅ Suspended: {args.tenant_id}")


def cmd_activate(args: argparse.Namespace) -> None:
    data = _load_tenants()
    t = data.get(args.tenant_id)
    if not t:
        print(f"Tenant not found: {args.tenant_id}")
        sys.exit(1)
    t["status"] = "active"
    _save_tenants(data)
    print(f"✅ Activated: {args.tenant_id}")


def cmd_stripe_onboard(args: argparse.Namespace) -> None:
    data = _load_tenants()
    t = data.get(args.tenant_id)
    if not t:
        print(f"Tenant not found: {args.tenant_id}")
        sys.exit(1)
    s = OnboardingSession(display_name=t["display_name"], slug=t["slug"], email=t["email"], revenue_share=t["revenue_share"])
    s.tenant_id = t["id"]
    s.start_stripe_onboarding()
    print(f"Stripe onboarding URL:\n{s.stripe_onboarding_url}")
    print("\nShare this URL with the tenant to complete Stripe Connect setup.")


def main() -> None:
    parser = argparse.ArgumentParser(description="ROMA SaaS Tenant Management")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("create", help="Create a new tenant")
    p.add_argument("--display-name", required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--email", required=True)
    p.add_argument("--revenue-share", type=float, default=15.0)
    p.add_argument("--tier", default="pro")
    p.add_argument("--app-name", default="")
    p.add_argument("--color", default="")

    sub.add_parser("list", help="List all tenants")
    p = sub.add_parser("get", help="Get tenant details")
    p.add_argument("tenant_id")
    p = sub.add_parser("suspend", help="Suspend a tenant")
    p.add_argument("tenant_id")
    p = sub.add_parser("activate", help="Activate a tenant")
    p.add_argument("tenant_id")
    p = sub.add_parser("stripe-onboard", help="Generate Stripe Connect onboarding URL")
    p.add_argument("tenant_id")

    args = parser.parse_args()
    if args.cmd == "create":
        cmd_create(args)
    elif args.cmd == "list":
        cmd_list(args)
    elif args.cmd == "get":
        cmd_get(args)
    elif args.cmd == "suspend":
        cmd_suspend(args)
    elif args.cmd == "activate":
        cmd_activate(args)
    elif args.cmd == "stripe-onboard":
        cmd_stripe_onboard(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
