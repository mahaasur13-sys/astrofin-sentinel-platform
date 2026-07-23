"""ROMA RBAC Guard — Pre-execution permission enforcement."""

from typing import Optional


class RBACGuard:
    def __init__(self, rbac_engine):
        self.rbac = rbac_engine

    def check_pre_execution(self, key_validation: dict | None, action: str, context: dict) -> dict:
        if not key_validation:
            return {"allowed": False, "reason": "INVALID_KEY", "step": "auth"}
        org_id = key_validation["org_id"]
        perms = key_validation["permissions"]
        if action not in perms and "*" not in perms:
            return {"allowed": False, "reason": "PERMISSION_DENIED", "step": "rbac"}
        return {"allowed": True, "step": "passed", "org_id": org_id}
