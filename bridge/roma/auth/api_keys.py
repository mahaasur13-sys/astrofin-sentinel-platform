"""ROMA API Key System — Scoped keys with rotation."""

import secrets
import time
from typing import List, Optional

PREFIX = "roma_sk-REDACTED-"


class APIKeyManager:
    def __init__(self):
        self._keys = {}
        self._counter = 0

    def create_key(self, org_id: str, project_id: str, permissions: list[str], expires_in: int = 0) -> str:
        self._counter += 1
        key_id = f"kid_{org_id}_{project_id}_{self._counter}"
        raw = f"{PREFIX}{key_id}_{secrets.token_urlsafe(32)}"
        self._keys[key_id] = {
            "key_id": key_id,
            "org_id": org_id,
            "project_id": project_id,
            "permissions": permissions,
            "created": time.time(),
            "expires_at": time.time() + expires_in if expires_in else None,
            "revoked": False,
            "last_used": None,
            "rate_limit": 1000,
        }
        return raw

    def validate_key(self, key: str) -> dict | None:
        if not key.startswith(PREFIX):
            return None
        rest = key[len(PREFIX) :]
        key_id = rest.rsplit("_", 1)[0]  # split from right, discard random suffix
        stored = self._keys.get(key_id)
        if not stored or stored["revoked"]:
            return None
        if stored["expires_at"] and time.time() > stored["expires_at"]:
            return None
        stored["last_used"] = time.time()
        return {
            "valid": True,
            "org_id": stored["org_id"],
            "project_id": stored["project_id"],
            "permissions": stored["permissions"],
        }

    def revoke_key(self, key: str) -> bool:
        if not key.startswith(PREFIX):
            return False
        rest = key[len(PREFIX) :]
        key_id = rest.rsplit("_", 1)[0]
        if key_id in self._keys:
            self._keys[key_id]["revoked"] = True
            return True
        return False

    def rotate_key(self, old_key: str, expires_in: int = 86400) -> str | None:
        v = self.validate_key(old_key)
        if not v:
            return None
        return self.create_key(v["org_id"], v["project_id"], v["permissions"], expires_in)


if __name__ == "__main__":
    km = APIKeyManager()
    key = km.create_key("org_acme", "proj_ml", permissions=["job:execute", "job:read"], expires_in=86400)
    print(f"Key: {key[:60]}...")
    v = km.validate_key(key)
    print(f"Valid: {v}")
    km.revoke_key(key)
    print(f"After revoke: {km.validate_key(key)}")
    new_key = km.rotate_key(key)
    print(f"Rotation blocked (revoked): {new_key is None}")
