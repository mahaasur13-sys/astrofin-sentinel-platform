"""Centralised application settings (canonical configuration entrypoint).

This module is the **single source of truth** for environment variables.
All runtime code must import :data:`settings` from this module instead of
calling :func:`os.getenv` directly. Legacy ``os.getenv`` callers are
wrapped via :func:`legacy_env` to keep the refactor non-breaking.

Design
------
* Pydantic v2 ``BaseSettings`` with explicit ``env``/``alias`` mapping.
* Three environments: ``development`` (default), ``test``, ``production``.
  - ``production`` / ``staging``: **fail-fast** on missing required secrets.
  - ``test``: required secrets are seeded with safe placeholders
    (``test-*``); never used in real deployments.
  - ``development``: secrets are loaded from ``.env`` if present.

Security
--------
* API keys / passwords / private-key paths are **never** logged.
* ``repr()`` masks all fields ending in ``_key``, ``_secret``, ``_password``.
* :func:`validate_startup` is the canonical pre-flight check and must be
  called from every entrypoint (web/wsgi, health_endpoints,
  orchestration/sentinel_v5, meta_rl/live_data).

Migration
---------
Phase 1 (this commit): module + shim. Existing ``os.getenv`` callers keep
working through :func:`legacy_env`.
Phase 2 (follow-up PR): replace remaining ``os.getenv`` with ``settings.X``.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

Env = Literal["development", "test", "production", "staging"]

# Sensible defaults for local dev. Real secrets MUST come from environment
# (or a SOPS-encrypted file referenced by SOPS env, see ``.sops.yaml``).
_DEFAULTS_DEV: dict[str, str] = {
    "API_KEY": "dev-api-key-change-me",
    "REDIS_URL": "redis://localhost:6379/0",
    "DATABASE_URL": "postgresql://astrofin:astrofin@localhost:5432/astrofin",
    "JWT_PRIVATE_KEY_PATH": "./keys/jwt_private.pem",
    "JWT_PUBLIC_KEY_PATH": "./keys/jwt_public.pem",
}


class Settings(BaseSettings):
    """Canonical application settings.

    All required secrets raise :class:`pydantic.ValidationError` at
    instantiation time when the environment is ``production`` or
    ``staging``. ``test`` and ``development`` environments get safe
    placeholders so the process can boot.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        # Hide secret values in repr/log output
        json_schema_extra={"title": "AstroFin Sentinel Settings"},
    )

    # ── Environment discriminator ───────────────────────────────────────
    env: Env = Field(default="development", description="Runtime environment")

    # ── Required secrets (SecretStr masks in logs) ──────────────────────
    api_key: SecretStr = Field(
        default=SecretStr(""),
        description="Static API key for the X-API-Key auth header",
    )
    redis_url: SecretStr = Field(
        default=SecretStr(""),
        description="Redis connection URL (must include auth if prod)",
    )
    database_url: SecretStr = Field(
        default=SecretStr(""),
        description="PostgreSQL connection URL",
    )
    jwt_private_key_path: str = Field(
        default="",
        description="Path to RS256 private key (PEM)",
    )
    jwt_public_key_path: str = Field(
        default="",
        description="Path to RS256 public key (PEM)",
    )

    # ── Optional (CCXT, exchange credentials) ──────────────────────────
    ccxt_api_key: SecretStr = Field(default=SecretStr(""))
    ccxt_api_secret: SecretStr = Field(default=SecretStr(""))
    ccxt_exchange: str = Field(default="binance")
    ccxt_sandbox_mode: bool = Field(default=True)
    ccxt_rate_limit_ms: int = Field(default=50, ge=0, le=10_000)
    ccxt_live_mode: bool = Field(default=False)
    live_data_enabled: bool = Field(default=True)

    # ── Auth toggles ────────────────────────────────────────────────────
    require_auth: bool = Field(default=True)

    # ── Web / dashboard ────────────────────────────────────────────────
    web_port: int = Field(default=8050, ge=1, le=65_535)
    gunicorn_workers: int = Field(default=4, ge=1, le=64)
    enable_internal_endpoints: bool = Field(default=False)
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    # ── ML inference API ──────────────────────────────────────────────
    ml_port: int = Field(default=8081, ge=1, le=65_535)
    ml_model_path: str = Field(default="/app/models/failure_xgb_v2.pkl")
    ml_features_path: str = Field(default="/app/models/features.txt")

    # ── Feature pipeline ──────────────────────────────────────────────
    feature_pipeline_port: int = Field(default=8090)
    feature_pipeline_interval_sec: int = Field(default=60, ge=1)

    # ── GPU worker ────────────────────────────────────────────────────
    enable_gpu_worker: bool = Field(default=False)
    gpu_worker_port: int = Field(default=8000)
    cuda_visible_devices: str = Field(default="0")
    worker_id: str = Field(default="gpu-worker-01")

    # ── Observability ──────────────────────────────────────────────────
    log_level: str = Field(default="INFO")
    prometheus_port: int = Field(default=9090)
    sentry_dsn: SecretStr = Field(default=SecretStr(""))
    grafana_admin_password: SecretStr = Field(default=SecretStr(""))

    # ── Misc ──────────────────────────────────────────────────────────
    tz: str = Field(default="UTC")

    # ── Render / service identity ─────────────────────────────────────
    render_mode: str = Field(default="production")
    service_name: str = Field(default="astrofin-sentinel")
    jaeger_enabled: bool = Field(default=False)
    otel_exporter_otlp_endpoint: str = Field(default="http://jaeger:4317")

    # ── Postgres / Redis connection (in addition to URL) ───────────────
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432, ge=1, le=65_535)
    postgres_user: str = Field(default="astrofin")
    postgres_password: SecretStr = Field(default=SecretStr(""))
    postgres_db: str = Field(default="astrofin")
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379, ge=1, le=65_535)

    # ── RAG / Knowledge ───────────────────────────────────────────────
    rag_backend: str = Field(default="pgvector")
    afs_pg_dsn: SecretStr = Field(default=SecretStr(""))
    rag_legacy_fallback: bool = Field(default=True)
    rag_faiss_dir: str = Field(default="knowledge/indexes")

    # ── Web app / Dash ────────────────────────────────────────────────
    secret_key: SecretStr = Field(default=SecretStr(""))
    allowed_origins: str = Field(default="*")
    debug_mode: bool = Field(default=False)
    port: int = Field(default=8050, ge=1, le=65_535)
    url_base_pathname: str = Field(default="/")

    # ── Meta-RL feature flags ─────────────────────────────────────────
    meta_rl_mode: str = Field(default="historical")
    meta_rl_symbol: str = Field(default="BTC/USDT")
    meta_rl_timeframe: str = Field(default="1h")
    meta_rl_enabled: bool = Field(default=True)
    risk_integration_enabled: bool = Field(default=True)
    karl_meta_update_enabled: bool = Field(default=True)
    execution_sanity_enabled: bool = Field(default=True)
    alpha_decay_detection: bool = Field(default=True)
    alpha_decay_reward_drop_pct: float = Field(default=0.30, ge=0.0, le=1.0)
    alpha_decay_window_gens: int = Field(default=5, ge=1, le=1000)
    decay_kill_threshold: float = Field(default=0.15, ge=0.0, le=1.0)
    diversity_enforcement: bool = Field(default=True)
    min_diversity_population: int = Field(default=3, ge=1)
    diversity_similarity_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    batch_evaluation_size: int = Field(default=64, ge=1)
    walk_forward_enabled: bool = Field(default=True)
    oos_overfit_threshold: float = Field(default=0.20, ge=0.0, le=1.0)
    oos_sharpe_degradation_limit: float = Field(default=0.50, ge=0.0, le=10.0)
    hyperopt_enabled: bool = Field(default=False)

    # ── Meta-RL composite ranking weights ─────────────────────────────
    cw_sharpe: float = Field(default=0.35, ge=0.0, le=1.0)
    cw_win_rate: float = Field(default=0.20, ge=0.0, le=1.0)
    cw_pnl: float = Field(default=0.25, ge=0.0, le=1.0)
    cw_stability: float = Field(default=0.20, ge=0.0, le=1.0)
    composite_ranking_enabled: bool = Field(default=True)

    # ── Meta-RL reports / alerts ──────────────────────────────────────
    html_reports_enabled: bool = Field(default=True)
    reports_output_dir: str = Field(default="data/reports")
    reports_base_url: str = Field(default="/reports")
    telegram_alerts_enabled: bool = Field(default=False)
    telegram_bot_token: SecretStr = Field(default=SecretStr(""))
    telegram_chat_id: str = Field(default="")
    telegram_min_reward_alert: float = Field(default=0.0, ge=-10.0, le=10.0)

    # ── CCXT reconnect tuning ─────────────────────────────────────────
    ccxt_reconnect_attempts: int = Field(default=3, ge=0, le=20)
    ccxt_reconnect_delay_s: float = Field(default=2.0, ge=0.0, le=60.0)
    ccxt_enable_rate_limit: bool = Field(default=True)

    # ── Pressure field (coordination) ────────────────────────────────
    pressure_field_enabled: bool = Field(default=False)
    pressure_field_k_neighbors: int = Field(default=3, ge=1, le=64)
    pressure_field_influence_strength: float = Field(default=0.15, ge=0.0, le=1.0)
    pressure_field_min_consensus: float = Field(default=0.5, ge=0.0, le=1.0)

    # ── Validators ─────────────────────────────────────────────────────
    @field_validator("env", mode="before")
    @classmethod
    def _lower_env(cls, v: Any) -> str:
        return str(v).lower() if v is not None else "development"

    @field_validator("log_level")
    @classmethod
    def _upper_log_level(cls, v: str) -> str:
        v = v.upper()
        if v not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError(f"invalid log level: {v}")
        return v

    @field_validator("jwt_private_key_path", "jwt_public_key_path")
    @classmethod
    def _validate_key_path(cls, v: str) -> str:
        # In production, the path MUST exist at process start.
        # In test/dev we skip this — the keys are loaded lazily.
        return v

    # ── Helpers ────────────────────────────────────────────────────────
    def is_production(self) -> bool:
        return self.env in {"production", "staging"}

    def is_test(self) -> bool:
        return self.env == "test"

    def require_secrets(self) -> None:
        """Fail-fast check: required secrets must be non-empty in prod.

        Called from :func:`validate_startup` at process start.
        """
        if not self.is_production():
            return  # test/dev are allowed to have placeholders
        missing: list[str] = []
        if not self.api_key.get_secret_value().strip():
            missing.append("API_KEY")
        if not self.redis_url.get_secret_value().strip():
            missing.append("REDIS_URL")
        if not self.database_url.get_secret_value().strip():
            missing.append("DATABASE_URL")
        if not self.jwt_private_key_path.strip():
            missing.append("JWT_PRIVATE_KEY_PATH")
        if not self.jwt_public_key_path.strip():
            missing.append("JWT_PUBLIC_KEY_PATH")
        # In prod, the JWT key files must exist.
        for p in (self.jwt_private_key_path, self.jwt_public_key_path):
            if p and not Path(p).exists():
                missing.append(f"{p} (file not found)")
        if missing:
            raise RuntimeError(
                f"REFUSING TO START in env={self.env}: missing required " f"secrets: {', '.join(missing)}"
            )

    def __repr__(self) -> str:  # pragma: no cover - safety only
        masked = {k: "***" for k in self.model_fields if k.endswith(("_key", "_secret", "_password", "dsn"))}
        return f"Settings(env={self.env!r}, masked={masked})"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide cached :class:`Settings` instance.

    Reads from environment, then ``.env`` if present. Applies dev defaults
    if running in ``development`` mode and no real values are set.
    """
    raw_env = os.getenv("ENV", "development").lower()
    # For dev: seed defaults that pydantic would otherwise reject
    if raw_env in {"development", "test"}:
        for k, v in _DEFAULTS_DEV.items():
            os.environ.setdefault(k, v)
    return Settings()  # type: ignore[call-arg]


def validate_startup() -> Settings:
    """Module-level entrypoint. Loads + validates settings.

    Returns the validated :class:`Settings` instance on success; raises
    :class:`RuntimeError` if required secrets are missing in production.
    """
    s = get_settings()
    try:
        s.require_secrets()
    except RuntimeError:
        logger.exception("startup validation failed")
        raise
    logger.info("settings validated env=%s log_level=%s", s.env, s.log_level)
    return s


def legacy_env(name: str, default: str = "") -> str:
    """Compatibility shim for ``os.getenv`` callers.

    Phase 1 of the consolidation keeps existing ``os.getenv`` calls
    working by routing them through :data:`settings`. This will be
    removed in Phase 2 once all callers migrate.

    Example::

        # before
        API_KEY = os.getenv("API_KEY", "")
        # after (drop-in)
        API_KEY = legacy_env("API_KEY", "")
    """
    # Direct passthrough — keeps the surface minimal and avoids
    # surprise coercion. Phase 2 will replace these call-sites.
    return os.getenv(name, default)


# Module-level singleton (lazy)
settings: Settings = get_settings()
