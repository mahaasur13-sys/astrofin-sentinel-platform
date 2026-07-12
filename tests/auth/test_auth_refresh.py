"""Integration tests for core.auth_refresh.

These tests cover the refresh-token rotation flow described in
ADR-0009. They use a freshly generated RSA keypair and the real
``core.auth_jwt`` + ``core.auth_refresh`` modules — no mocks.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest


def _issue_pair(monkeypatch, tmp_path: Path):
    """Wire env to a fresh keypair, then issue a (sub, refresh_token, rotate, issue_access_token) bundle."""
    priv, pub = _generate_keypair(tmp_path)
    monkeypatch.setenv("JWT_PRIVATE_KEY_PATH", str(priv))
    monkeypatch.setenv("JWT_PUBLIC_KEY_PATH", str(pub))
    monkeypatch.setenv("JWT_ISSUER", "astrofin-test")
    monkeypatch.setenv("JWT_AUDIENCE", "astrofin-clients")
    monkeypatch.setenv("JWT_REQUIRE_AUTH", "false")
    _clear_settings_cache()
    for mod in ("core.auth_jwt", "core.auth_refresh"):
        sys.modules.pop(mod, None)
    from core.auth_jwt import issue_access_token, issue_refresh_token
    import core.auth_refresh as ar

    importlib.reload(ar)
    from core.auth_jwt import issue_access_token as ia
    from core.auth_jwt import issue_refresh_token as ir
    from core.auth_refresh import rotate

    user_id = "user-123"
    refresh, _ = ir(user_id)
    return user_id, refresh, rotate, ia


def _generate_keypair(tmp_dir: Path) -> tuple[Path, Path]:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    priv_path = tmp_dir / "jwt_private.pem"
    pub_path = tmp_dir / "jwt_public.pem"
    priv_path.write_bytes(priv_pem)
    pub_path.write_bytes(pub_pem)
    return priv_path, pub_path


def _clear_settings_cache() -> None:
    from core.settings import get_settings
    if hasattr(get_settings, "cache_clear"):
        get_settings.cache_clear()


def test_rotate_returns_new_pair(monkeypatch, tmp_path) -> None:
    _, refresh, rotate, _ = _issue_pair(monkeypatch, tmp_path)
    result = rotate(refresh)
    assert "access_token" in result
    assert "refresh_token" in result
    assert result["refresh_token"] != refresh
    assert isinstance(result["access_token"], str) and len(result["access_token"]) > 0


def test_rotate_rejects_already_used_token(monkeypatch, tmp_path) -> None:
    _, refresh, rotate, _ = _issue_pair(monkeypatch, tmp_path)
    rotate(refresh)
    with pytest.raises(Exception):
        rotate(refresh)


def test_rotate_rejects_tampered_token(monkeypatch, tmp_path) -> None:
    _, refresh, rotate, _ = _issue_pair(monkeypatch, tmp_path)
    bad = refresh[:-2] + ("AA" if refresh[-2:] != "AA" else "BB")
    with pytest.raises(Exception):
        rotate(bad)


def test_rotate_rejects_garbage(monkeypatch, tmp_path) -> None:
    _, _, rotate, _ = _issue_pair(monkeypatch, tmp_path)
    with pytest.raises(Exception):
        rotate("not.a.real.jwt")


def test_rotate_still_works_when_auth_disabled(monkeypatch, tmp_path) -> None:
    """REQUIRE_AUTH=false must not block refresh rotation itself."""
    _, refresh, rotate, _ = _issue_pair(monkeypatch, tmp_path)
    result = rotate(refresh)
    assert "access_token" in result
    assert "refresh_token" in result
