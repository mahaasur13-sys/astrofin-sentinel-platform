"""meta_rl/config.py — Feature flags & integration config (ATOM-META-RL-006: Production)

All production settings are controlled via environment variables.
NEVER hardcode exchange credentials or API keys here.
"""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass, field

#
# Modes (ATOM-META-RL-003)
# ---------------------------------------------------------------------------
HISTORICAL_MODE = "historical"
PAPER_MODE = "paper"
LIVE_MODE = "live"
DEFAULT_MODE = os.getenv("META_RL_MODE", HISTORICAL_MODE)

# Defaults
DEFAULT_SYMBOL = os.getenv("META_RL_SYMBOL", "BTC/USDT")
DEFAULT_TIMEFRAME = os.getenv("META_RL_TIMEFRAME", "1h")

# Core Meta-RL
META_RL_ENABLED = os.getenv("META_RL_ENABLED", "true").lower() == "true"
RISK_INTEGRATION_ENABLED = os.getenv("RISK_INTEGRATION_ENABLED", "true").lower() == "true"
KARL_META_UPDATE_ENABLED = os.getenv("KARL_META_UPDATE_ENABLED", "true").lower() == "true"
EXECUTION_SANITY_ENABLED = os.getenv("EXECUTION_SANITY_ENABLED", "true").lower() == "true"
LIVE_DATA_ENABLED = os.getenv("LIVE_DATA_ENABLED", "true").lower() == "true"

# Alpha Decay / Early Stopping
ALPHA_DECAY_DETECTION = os.getenv("ALPHA_DECAY_DETECTION", "true").lower() == "true"
ALPHA_DECAY_REWARD_DROP_PCT = float(os.getenv("ALPHA_DECAY_REWARD_DROP_PCT", "0.3"))
ALPHA_DECAY_WINDOW_GENS = int(os.getenv("ALPHA_DECAY_WINDOW_GENS", "5"))
DECAY_KILL_THRESHOLD = float(os.getenv("DECAY_KILL_THRESHOLD", "-0.5"))

# Diversity
DIVERSITY_ENFORCEMENT = os.getenv("DIVERSITY_ENFORCEMENT", "true").lower() == "true"
MIN_DIVERSITY_POPULATION = int(os.getenv("MIN_DIVERSITY_POPULATION", "5"))
DIVERSITY_SIMILARITY_THRESHOLD = float(os.getenv("DIVERSITY_SIMILARITY_THRESHOLD", "0.85"))

# Batch Evaluation
BATCH_EVALUATION_SIZE = int(os.getenv("BATCH_EVALUATION_SIZE", "20"))

# Walk-Forward OOS Validation
WALK_FORWARD_ENABLED = os.getenv("WALK_FORWARD_ENABLED", "true").lower() == "true"
OOS_OVERFIT_THRESHOLD = float(os.getenv("OOS_OVERFIT_THRESHOLD", "0.30"))
OOS_SHARPE_DEGRADATION_LIMIT = float(os.getenv("OOS_SHARPE_DEGRADATION_LIMIT", "0.50"))

# CCXT Real Exchange (P0.2)
CCXT_SANDBOX_MODE = os.getenv("CCXT_SANDBOX_MODE", "true").lower() == "true"
CCXT_LIVE_MODE = os.getenv("CCXT_LIVE_MODE", "false").lower() == "true"
CCXT_API_KEY = os.getenv("CCXT_API_KEY", "")
CCXT_API_SECRET = os.getenv("CCXT_API_SECRET", "")
CCXT_EXCHANGE = os.getenv("CCXT_EXCHANGE", "binance")
CCXT_RATE_LIMIT = int(os.getenv("CCXT_RATE_LIMIT", "50"))
CCXT_ENABLE_RATE_LIMIT = os.getenv("CCXT_ENABLE_RATE_LIMIT", "true").lower() == "true"

# Telegram Alerts (P1.3)
TELEGRAM_ALERTS_ENABLED = os.getenv("TELEGRAM_ALERTS_ENABLED", "false").lower() == "true"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_MIN_REWARD_ALERT = float(os.getenv("TELEGRAM_MIN_REWARD_ALERT", "0.5"))

# Reports (P1.2)
HTML_REPORTS_ENABLED = os.getenv("HTML_REPORTS_ENABLED", "true").lower() == "true"
REPORTS_OUTPUT_DIR = os.getenv("REPORTS_OUTPUT_DIR", "reports/")
REPORTS_BASE_URL = os.getenv("REPORTS_BASE_URL", "http://localhost:8050/reports")

# Composite Ranking (P1.1)
COMPOSITE_RANKING_ENABLED = os.getenv("COMPOSITE_RANKING_ENABLED", "true").lower() == "true"
COMPOSITE_WEIGHTS = {
    "sharpe": float(os.getenv("CW_SHARPE", "0.35")),
    "win_rate": float(os.getenv("CW_WIN_RATE", "0.20")),
    "risk_adjusted_pnl": float(os.getenv("CW_PNL", "0.25")),
    "stability": float(os.getenv("CW_STABILITY", "0.20")),
}


@dataclass
class MetaRLConfig:
    """Validated configuration object produced by :func:`load_config`."""

    mode: str = HISTORICAL_MODE
    symbol: str = DEFAULT_SYMBOL
    timeframe: str = DEFAULT_TIMEFRAME
    enabled: bool = True
    risk_integration: bool = True
    karl_meta_update: bool = True
    execution_sanity: bool = True
    live_data: bool = True
    alpha_decay_detection: bool = True
    alpha_decay_reward_drop_pct: float = 0.3
    alpha_decay_window_gens: int = 5
    decay_kill_threshold: float = -0.5
    diversity_enforcement: bool = True
    min_diversity_population: int = 5
    diversity_similarity_threshold: float = 0.85
    batch_evaluation_size: int = 20
    walk_forward_enabled: bool = True
    oos_overfit_threshold: float = 0.30
    oos_sharpe_degradation_limit: float = 0.50
    ccxt_sandbox_mode: bool = True
    ccxt_api_key: str = ""
    ccxt_api_secret: str = ""
    ccxt_exchange: str = "binance"
    ccxt_rate_limit_ms: int = 50
    ccxt_enable_rate_limit: bool = True
    ccxt_live_mode: bool = False
    composite_ranking_enabled: bool = True
    composite_weights: dict = field(default_factory=lambda: dict(COMPOSITE_WEIGHTS))
    telegram_alerts_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_min_reward_alert: float = 0.5
    html_reports_enabled: bool = True
    reports_output_dir: str = "reports/"
    reports_base_url: str = "http://localhost:8050/reports"

    def validate(self, *, strict: bool = False) -> list[str]:
        """Return list of warning strings; raise if ``strict`` and any warnings."""
        warnings: list[str] = []
        if self.mode not in (HISTORICAL_MODE, PAPER_MODE, LIVE_MODE):
            warnings.append(f"unknown mode {self.mode!r}")
        if self.alpha_decay_reward_drop_pct <= 0 or self.alpha_decay_reward_drop_pct >= 1:
            warnings.append("alpha_decay_reward_drop_pct must be in (0, 1)")
        if self.alpha_decay_window_gens < 2:
            warnings.append("alpha_decay_window_gens must be >= 2 for valid OOS")
        if self.composite_ranking_enabled:
            total = sum(self.composite_weights.values())
            if abs(total - 1.0) > 0.001:
                warnings.append(f"Composite weights sum to {total:.3f}, expected 1.0")
        if strict and warnings:
            raise ValueError("MetaRLConfig validation failed: " + "; ".join(warnings))
        return warnings


def load_config() -> MetaRLConfig:
    """Build a :class:`MetaRLConfig` from the current process environment.

    This is the canonical helper for callers that want a typed object
    rather than the module-level constants.  It does **not** perform I/O
    and is therefore safe to call at import time.
    """
    return MetaRLConfig(
        mode=DEFAULT_MODE,
        symbol=DEFAULT_SYMBOL,
        timeframe=DEFAULT_TIMEFRAME,
        enabled=META_RL_ENABLED,
        risk_integration=RISK_INTEGRATION_ENABLED,
        karl_meta_update=KARL_META_UPDATE_ENABLED,
        execution_sanity=EXECUTION_SANITY_ENABLED,
        live_data=LIVE_DATA_ENABLED,
        alpha_decay_detection=ALPHA_DECAY_DETECTION,
        alpha_decay_reward_drop_pct=ALPHA_DECAY_REWARD_DROP_PCT,
        alpha_decay_window_gens=ALPHA_DECAY_WINDOW_GENS,
        decay_kill_threshold=DECAY_KILL_THRESHOLD,
        diversity_enforcement=DIVERSITY_ENFORCEMENT,
        min_diversity_population=MIN_DIVERSITY_POPULATION,
        diversity_similarity_threshold=DIVERSITY_SIMILARITY_THRESHOLD,
        batch_evaluation_size=BATCH_EVALUATION_SIZE,
        walk_forward_enabled=WALK_FORWARD_ENABLED,
        oos_overfit_threshold=OOS_OVERFIT_THRESHOLD,
        oos_sharpe_degradation_limit=OOS_SHARPE_DEGRADATION_LIMIT,
        ccxt_sandbox_mode=CCXT_SANDBOX_MODE,
        ccxt_api_key=CCXT_API_KEY,
        ccxt_api_secret=CCXT_API_SECRET,
        ccxt_exchange=CCXT_EXCHANGE,
        ccxt_rate_limit_ms=CCXT_RATE_LIMIT,
        ccxt_enable_rate_limit=CCXT_ENABLE_RATE_LIMIT,
        ccxt_live_mode=CCXT_LIVE_MODE,
        composite_ranking_enabled=COMPOSITE_RANKING_ENABLED,
        composite_weights=dict(COMPOSITE_WEIGHTS),
        telegram_alerts_enabled=TELEGRAM_ALERTS_ENABLED,
        telegram_bot_token=TELEGRAM_BOT_TOKEN,
        telegram_chat_id=TELEGRAM_CHAT_ID,
        telegram_min_reward_alert=TELEGRAM_MIN_REWARD_ALERT,
        html_reports_enabled=HTML_REPORTS_ENABLED,
        reports_output_dir=REPORTS_OUTPUT_DIR,
        reports_base_url=REPORTS_BASE_URL,
    )


HYPEROPT_ENABLED = True
