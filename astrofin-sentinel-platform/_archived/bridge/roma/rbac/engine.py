"""ROMA RBAC Engine — Role-based permissions."""
from enum import Enum
from typing import Optional


class Role(Enum):
    OWNER = "owner"
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"

ROLE_PERMISSIONS = {
    Role.OWNER: {"billing:*", "job:*", "plugin:*", "tenant:*", "org:*", "audit:*", "member:*"},
    Role.ADMIN: {"billing:*", "job:*", "plugin:*", "tenant:read", "org:read", "audit:read", "member:manage"},
    Role.DEVELOPER: {"job:execute", "job:read", "plugin:read"},
    Role.VIEWER: {"job:read", "plugin:read"},
}

class RBACEngine:
    def __init__(self):
        self._orgs = {}   # org_id -> {user_id: role}
        self._keys = {}   # key_id -> {org_id, permissions}

    def create_org(self, org_id: str):
        self._orgs[org_id] = {}

    def assign_role(self, user_id: str, org_id: str, role: Role):
        if org_id not in self._orgs:
            self._orgs[org_id] = {}
        self._orgs[org_id][user_id] = role

    def can(self, user_id: str, org_id: str, permission: str) -> bool:
        if org_id not in self._orgs or user_id not in self._orgs[org_id]:
            return False
        role = self._orgs[org_id][user_id]
        allowed = ROLE_PERMISSIONS.get(role, set())
        for p in allowed:
            if p == "*" or p == permission or p.endswith(":*") and permission.startswith(p[:-2]):
                return True
        return False

    def get_role(self, user_id: str, org_id: str) -> Optional[Role]:
        if org_id not in self._orgs or user_id not in self._orgs[org_id]:
            return None
        return self._orgs[org_id][user_id]
