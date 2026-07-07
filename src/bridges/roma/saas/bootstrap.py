"""ROMA SaaS Bootstrap — Self-service onboarding."""

import sys

sys.path.insert(0, "/home/workspace/roma-execution-bridge")

from org.organization import Organization
from auth.api_keys import APIKeyManager
from rbac.engine import RBACEngine


class ROMASaaS:
    def __init__(self):
        self.orgs = {}
        self.akm = APIKeyManager()
        self.rbac = RBACEngine()

    def signup(self, org_name: str, plan: str = "FREE") -> dict:
        org = Organization(org_id=f"org_{org_name}", name=org_name, plan=plan, billing_account=f"acct_{org_name[:8]}")
        self.orgs[org.org_id] = org
        key = self.akm.create_key(org_id=org.org_id, project_id="default", permissions=["job:submit", "job:read", "cost:estimate"])
        return {"org": org.get_info(), "api_key": key, "dashboard": f"https://app.roma.sh/org/{org_name}"}


if __name__ == "__main__":
    print("=== ROMA SaaS Bootstrap ===")
    saas = ROMASaaS()
    result = saas.signup("acme", "PRO")
    print(f"Org: {result['org']['org_id']}")
    print(f"Plan: {result['org']['plan']}")
    print(f"API Key: {result['api_key'][:40]}...")
    print(f"Dashboard: {result['dashboard']}")
