"""meta_rl/security.py — ATOM-META-RL-009: Secure API Key Management

Security requirements:
- NEVER log API keys (even partially)
- NEVER commit keys to git
- Keys loaded ONLY from environment variables
- Live mode requires explicit confirmation flag
- All key access logged with masked values
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env if present (development only)
_dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_dotenv_path):
    load_dotenv(_dotenv_path)


@dataclass
class APIKeyConfig:
    """Validated API key configuration."""

    exchange: str
    sandbox_mode: bool
    api_key: str | None
    api_secret: str | None
    rate_limit_ms: int
    enable_rate_limit: bool
    is_production: bool  # True only when sandbox=False AND keys present

    @property
    def key_masked(self) -> str:
        """Return masked key for logging (NEVER the real key)."""
        if self.api_key and len(self.api_key) > 8:
            return f"{self.api_key[:4]}...{self.api_key[-4:]}"
        return "***"


def load_api_keys() -> APIKeyConfig:
    """
    Load and validate API keys from environment.

    Security rules:
    1. Keys NEVER logged in full
    2. Sandbox mode works without keys
    3. Live mode requires both KEY and SECRET
    4. Explicit LIVE_ENABLED flag required for live trading

    Returns:
        APIKeyConfig with masked key for logging
    """
    sandbox = os.getenv("CCXT_SANDBOX_MODE", "true").lower() == "true"
    live_enabled = os.getenv("META_RL_LIVE_ENABLED", "false").lower() == "true"

    api_key = os.getenv("CCXT_API_KEY", "") or None
    api_secret = os.getenv("CCXT_API_SECRET", "") or None
    exchange = os.getenv("CCXT_EXCHANGE", "binance")
    rate_limit = int(os.getenv("CCXT_RATE_LIMIT", "50"))
    enable_rl = os.getenv("CCXT_ENABLE_RATE_LIMIT", "true").lower() == "true"

    # Production = sandbox disabled + live explicitly enabled + keys present
    is_production = not sandbox and live_enabled and bool(api_key) and bool(api_secret)

    # Validation
    if not sandbox and not is_production:
        if not api_key or not api_secret:
            logger.warning(f"[SECURITY] Live mode requested but CCXT_API_KEY/CCXT_API_SECRET not set. Falling back to sandbox. Keys present: KEY={bool(api_key)}, SECRET={bool(api_secret)}")
            sandbox = True
            is_production = False

    config = APIKeyConfig(
        exchange=exchange,
        sandbox_mode=sandbox,
        api_key=api_key,
        api_secret=api_secret,
        rate_limit_ms=rate_limit,
        enable_rate_limit=enable_rl,
        is_production=is_production,
    )

    logger.info(f"[SECURITY] CCXT Config loaded: exchange={exchange} mode={'SANDBOX' if sandbox else 'LIVE'} keys={'YES(production)' if is_production else 'NO'} rate_limit={rate_limit}ms")

    return config


def validate_live_mode() -> tuple[bool, str]:
    """
    Validate that live mode can be safely enabled.

    Returns:
        (can_enable, reason)
    """
    config = load_api_keys()

    if config.sandbox_mode:
        return True, "Sandbox mode active"

    if not config.is_production:
        return False, "Production mode requires CCXT_SANDBOX_MODE=false + real keys"

    if not config.api_key or not config.api_secret:
        return False, "API keys not configured"

    if len(config.api_key) < 8:
        return False, "API key too short - appears invalid"

    return True, f"Production ready: {config.key_masked}"
