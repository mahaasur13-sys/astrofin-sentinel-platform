"""Pytest fixtures for JWT auth tests (issue #81).

We rely on the same RS256 keypair that ships under ``keys/jwt_*.pem``.
The fixture patches ``AuthConfig.from_env`` so JWT modules resolve the
correct paths even when the test runner's CWD differs.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

# Make sure the auth_jwt module picks up our keypair before any test
# module imports it. Doing this at module-import time keeps every test
# in this directory deterministic.
_REPO_ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("JWT_PRIVATE_KEY_PATH", str(_REPO_ROOT / "keys" / "jwt_private.pem"))
os.environ.setdefault("JWT_PUBLIC_KEY_PATH", str(_REPO_ROOT / "keys" / "jwt_public.pem"))
os.environ.setdefault("JWT_ISSUER", "astrofin-sentinel")
os.environ.setdefault("JWT_AUDIENCE", "astrofin-sentinel")
os.environ.setdefault("JWT_ACCESS_TTL", "3600")
os.environ.setdefault("JWT_REFRESH_TTL", "86400")


@pytest.fixture
def cfg():
    """Reload AuthConfig from the patched env for each test."""
    from core.auth_jwt import AuthConfig

    return AuthConfig.from_env()
