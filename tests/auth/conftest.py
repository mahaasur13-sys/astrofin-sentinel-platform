"""Pytest fixtures for JWT auth tests (issue #81).

We **generate** a fresh RS256 keypair per test session and point the JWT
modules at the temp dir. The repo intentionally does **not** commit the
private key (``keys/jwt_private.pem`` is in .gitignore), so any test that
relied on a checked-in keypath would fail in CI.

Implementation note: we avoid importing ``cryptography`` at module level
because it is not a hard dependency in every CI env. The import is
deferred to inside the keypair fixture; if it ever fails the failure is
scoped to the JWT tests, not to the whole ``tests/`` collect (which would
mask unrelated issues).
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture
def lazy_jwt():
    """Deferred ``jwt`` resolver.

    Some CI images install ``pyjwt`` lazily; importing it at module
    collection time would crash the whole ``tests/`` discovery. Callers
    that need the module should request this fixture instead of writing
    ``import jwt`` at the top of the test file.
    """
    import jwt as pyjwt  # noqa: WPS433 — deferred by design

    return pyjwt


def _generate_rsa_keypair(tmp_dir: Path) -> tuple[Path, Path]:
    """Create a fresh RS256 keypair under ``tmp_dir`` and return (priv, pub)."""
    # Defer the import — cryptography is a transitive dep of pyjwt, but the
    # CI image we run on may install only the core test deps.
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


@pytest.fixture(scope="session")
def jwt_keypair(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    """Session-scoped RS256 keypair generated on the fly."""
    tmp = tmp_path_factory.mktemp("jwt_keys")
    return _generate_rsa_keypair(tmp)


@pytest.fixture(autouse=True)
def _wire_jwt_env(jwt_keypair: tuple[Path, Path]) -> None:
    """Point every JWT module at the temp keypair for the duration of a test."""
    priv, pub = jwt_keypair
    os.environ["JWT_PRIVATE_KEY_PATH"] = str(priv)
    os.environ["JWT_PUBLIC_KEY_PATH"] = str(pub)
    os.environ.setdefault("JWT_ISSUER", "astrofin-sentinel")
    os.environ.setdefault("JWT_AUDIENCE", "astrofin-sentinel")
    os.environ.setdefault("JWT_ACCESS_TTL", "3600")
    os.environ.setdefault("JWT_REFRESH_TTL", "86400")


@pytest.fixture
def cfg():
    """Reload AuthConfig from the (autouse-patched) env for each test."""
    from core.auth_jwt import AuthConfig

    return AuthConfig.from_env()


@pytest.fixture
def auth_app():
    """FastAPI app wired with a refresh route and a smoke endpoint."""
    from fastapi import Depends, FastAPI

    from core.auth_jwt import AuthConfig, verify_token
    from core.auth_refresh import register_refresh_route

    application = FastAPI()
    cfg = AuthConfig.from_env()
    register_refresh_route(application, cfg=cfg)

    @application.post("/_smoke")
    def _smoke(claims=Depends(verify_token)) -> dict:  # type: ignore[valid-type]
        return {"sub": claims.sub}

    return application
