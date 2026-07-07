"""ROMA Organization Model — org → project → tenant hierarchy."""


class Organization:
    def __init__(self, org_id: str, name: str, plan: str, billing_account: str):
        self.org_id = org_id
        self.name = name
        self.plan = plan
        self.billing_account = billing_account

    def get_info(self) -> dict:
        return {"org_id": self.org_id, "name": self.name, "plan": self.plan, "billing_account": self.billing_account}
