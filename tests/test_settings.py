"""Unit tests for core/settings.py (master consolidation, Step 2)."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import SecretStr, ValidationError


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Wipe the env between tests so pydantic-settings starts clean."""
    for k in (
        "ENV", "API_KEY", "REDIS_URL", "DATABASE_URL",
        "JWT_PRIVATE_KEY_PATH", "JWT_PUBLIC_KEY_PATH",
        "CCXT_API_KEY", "CCXT_API_SECRET", "LOG_LEVEL",
    ):
        monkeypatch.delenv(k, raising=False)
    # Also bust the lru_cache so get_settings() re-reads env each time
    from core.settings import get_settings
    get_settings.cache_clear()


# ── Defaults & env loading ──────────────────────────────────────────────


def test_defaults_for_development() -> None:
    """In dev mode, get_settings() should not raise even without env vars."""
    os.environ["ENV"] = "development"
    os.environ.pop("API_KEY", None)
    os.environ.pop("REDIS_URL", None)
    from core.settings import get_settings
    s = get_settings()
    assert s.env == "development"
    assert s.api_key.get_secret_value()  # dev placeholder applied
    assert s.redis_url.get_secret_value()
    assert s.require_auth is True


def test_env_override_wins() -> None:
    os.environ["ENV"] = "production"
    os.environ["API_KEY"] = "secret-from-env"
    from core.settings import get_settings
    s = get_settings()
    assert isinstance(s.api_key, SecretStr)
    assert s.api_key.get_secret_value() == "secret-from-env"


def test_log_level_uppercased() -> None:
    os.environ["ENV"] = "test"
    os.environ["LOG_LEVEL"] = "debug"
    from core.settings import get_settings
    s = get_settings()
    assert s.log_level == "DEBUG"


def test_log_level_invalid_rejected() -> None:
    os.environ["ENV"] = "test"
    os.environ["LOG_LEVEL"] = "NOPE"
    from core.settings import get_settings, Settings

    with pytest.raises(ValidationError):
        # bypass lru_cache by calling Settings() directly
        Settings()


# ── Production fail-fast ────────────────────────────────────────────────


def test_production_missing_secrets_raises(tmp_path: Path) -> None:
    os.environ["ENV"] = "production"
    # Intentionally do NOT set required secrets
    from core.settings import get_settings
    s = get_settings()
    with pytest.raises(RuntimeError) as exc:
        s.require_secrets()
    msg = str(exc.value)
    assert "API_KEY" in msg
    assert "REDIS_URL" in msg
    assert "DATABASE_URL" in msg


def test_production_with_all_secrets_passes(tmp_path: Path) -> None:
    priv = tmp_path / "priv.pem"
    priv.write_text("dummy")
    pub = tmp_path / "pub.pem"
    pub.write_text("dummy")
    os.environ["ENV"] = "production"
    os.environ["API_KEY"] = "prod-key"
    os.environ["REDIS_URL"] = "redis://prod-redis:6379/0"
    os.environ["DATABASE_URL"] = "postgresql://u:p@db:5432/astrofin"
    os.environ["JWT_PRIVATE_KEY_PATH"] = str(priv)
    os.environ["JWT_PUBLIC_KEY_PATH"] = str(pub)
    from core.settings import get_settings
    s = get_settings()
    s.require_secrets()  # must not raise
    assert s.is_production()


def test_production_missing_key_file_raises(tmp_path: Path) -> None:
    os.environ["ENV"] = "production"
    os.environ["API_KEY"] = "k"
    os.environ["REDIS_URL"] = "redis://x"
    os.environ["DATABASE_URL"] = "postgres://x"
    os.environ["JWT_PRIVATE_KEY_PATH"] = str(tmp_path / "missing.pem")
    os.environ["JWT_PUBLIC_KEY_PATH"] = str(tmp_path / "missing2.pem")
    from core.settings import get_settings
    s = get_settings()
    with pytest.raises(RuntimeError) as exc:
        s.require_secrets()
    assert "not found" in str(exc.value).lower()


# ── validate_startup entrypoint ────────────────────────────────────────


def test_validate_startup_ok_in_development() -> None:
    os.environ["ENV"] = "development"
    from core.settings import validate_startup
    s = validate_startup()
    assert s.env == "development"


def test_validate_startup_fails_in_production_without_secrets() -> None:
    os.environ["ENV"] = "production"
    from core.settings import validate_startup
    with pytest.raises(RuntimeError):
        validate_startup()


# ── legacy_env shim ─────────────────────────────────────────────────────


def test_legacy_env_passthrough() -> None:
    os.environ["MY_TEST_VAR"] = "hello"
    from core.settings import legacy_env
    assert legacy_env("MY_TEST_VAR") == "hello"
    assert legacy_env("MY_TEST_VAR", "default") == "hello"
    assert legacy_env("UNSET_VAR", "fallback") == "fallback"


# ── repr masks secrets ──────────────────────────────────────────────────


def test_repr_masks_secrets() -> None:
    os.environ["ENV"] = "test"
    os.environ["API_KEY"] = "super-secret-value"
    from core.settings import get_settings
    s = get_settings()
    text = repr(s)
    assert "super-secret-value" not in text
    assert "***" in text
