"""meta_rl/config.py — Feature flags & integration config (ATOM-META-RL-006: Production)

All production settings are controlled via environment variables.
NEVER hardcode exchange credentials or API keys here.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

# ── Modes (ATOM-META-RL-003) ─────────────────────────────────────────────────────
HISTORICAL_MODE = "historical"
PAPER_MODE = "paper"
LIVE_MODE = "live"
DEFAULT_MODE = os.getenv("META_RL_MODE", HISTORICAL_MODE)

# ── Defaults ─────────────────────────────────────────────────────────────
DEFAULT_SYMBOL = os.getenv("META_RL_SYMBOL", "BTC/USDT")
DEFAULT_TIMEFRAME = os.getenv("META_RL_TIMEFRAME", "1h")

# ── Core Meta-RL ──────────────────────────────────────────────────────────────
META_RL_ENABLED = os.getenv("META_RL_ENABLED", "true").lower() == "true"
RISK_INTEGRATION_ENABLED = os.getenv("RISK_INTEGRATION_ENABLED", "true").lower() == "true"
KARL_META_UPDATE_ENABLED = os.getenv("KARL_META_UPDATE_ENABLED", "true").lower() == "true"
EXECUTION_SANITY_ENABLED = os.getenv("EXECUTION_SANITY_ENABLED", "true").lower() == "true"
LIVE_DATA_ENABLED = os.getenv("LIVE_DATA_ENABLED", "true").lower() == "true"

# ── Alpha Decay / Early Stopping (ATOM-META-RL-003) ──────────────────────────
ALPHA_DECAY_DETECTION = os.getenv("ALPHA_DECAY_DETECTION", "true").lower() == "true"
ALPHA_DECAY_REWARD_DROP_PCT = float(os.getenv("ALPHA_DECAY_REWARD_DROP_PCT", "0.3"))
ALPHA_DECAY_WINDOW_GENS = int(os.getenv("ALPHA_DECAY_WINDOW_GENS", "5"))
DECAY_KILL_THRESHOLD = float(os.getenv("DECAY_KILL_THRESHOLD", "0.01"))

# ── Diversity ──────────────────────────────────────────────────────────────
DIVERSITY_ENFORCEMENT = os.getenv("DIVERSITY_ENFORCEMENT", "true").lower() == "true"
MIN_DIVERSITY_POPULATION = int(os.getenv("MIN_DIVERSITY_POPULATION", "3"))
DIVERSITY_SIMILARITY_THRESHOLD = float(os.getenv("DIVERSITY_SIMILARITY_THRESHOLD", "0.95"))

# ── Batch Evaluation ─────────────────────────────────────────────────────
BATCH_EVALUATION_SIZE = int(os.getenv("BATCH_EVALUATION_SIZE", "10"))

# ── Walk-Forward OOS Validation (P0.3) ────────────────────────────────────────
WALK_FORWARD_ENABLED = os.getenv("WALK_FORWARD_ENABLED", "true").lower() == "true"
OOS_OVERFIT_THRESHOLD = float(os.getenv("OOS_OVERFIT_THRESHOLD", "0.3"))
OOS_SHARPE_DEGRADATION_LIMIT = float(os.getenv("OOS_SHARPE_DEGRADATION_LIMIT", "0.5"))

# ── CCXT Real Exchange (P0.2) ──────────────────────────────────────────────────
CCXT_SANDBOX_MODE = os.getenv("CCXT_SANDBOX_MODE", "true").lower() == "true"
CCXT_LIVE_MODE = os.getenv("CCXT_LIVE_MODE", "false").lower() == "true"
CCXT_API_KEY = os.getenv("CCXT_API_KEY", "")
CCXT_API_SECRET = os.getenv("CCXT_API_SECRET", "")
CCXT_EXCHANGE = os.getenv("CCXT_EXCHANGE", "binance")
CCXT_RATE_LIMIT = int(os.getenv("CCXT_RATE_LIMIT", "50"))
CCXT_ENABLE_RATE_LIMIT = os.getenv("CCXT_ENABLE_RATE_LIMIT", "true").lower() == "true"

# ── Telegram Alerts (P1.3) ────────────────────────────────────────────────────
TELEGRAM_ALERTS_ENABLED = os.getenv("TELEGRAM_ALERTS_ENABLED", "false").lower() == "true"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_MIN_REWARD_ALERT = float(os.getenv("TELEGRAM_MIN_REWARD_ALERT", "0.8"))

# ── Reports (P1.2) ────────────────────────────────────────────────────────────
HTML_REPORTS_ENABLED = os.getenv("HTML_REPORTS_ENABLED", "true").lower() == "true"
REPORTS_OUTPUT_DIR = os.getenv("REPORTS_OUTPUT_DIR", "data/meta_rl/reports")
REPORTS_BASE_URL = os.getenv("REPORTS_BASE_URL", "")

# ── Composite Ranking (P1.1) ────────────────────────────────────────────────────
COMPOSITE_RANKING_ENABLED = os.getenv("COMPOSITE_RANKING_ENABLED", "true").lower() == "true"
COMPOSITE_WEIGHTS = {
    "sharpe": float(os.getenv("CW_SHARPE", "0.35")),
    "win_rate": float(os.getenv("CW_WIN_RATE", "0.20")),
    "risk_adjusted_pnl": float(os.getenv("CW_PNL", "0.25")),
    "stability": float(os.getenv("CW_STABILITY", "0.10")),
    "diversity": float(os.getenv("CW_DIVERSITY", "0.10")),
}

# ── Zo Space / Web Deployment (P0.1) ─────────────────────────────────────────
WEB_DASHBOARD_URL = os.getenv("WEB_DASHBOARD_URL", "")
ZO_SPACE_ENABLED = os.getenv("ZO_SPACE_ENABLED", "false").lower() == "true"
ZO_DASHBOARD_ENABLED = os.getenv("ZO_DASHBOARD_ENABLED", "true").lower() == "true"
ZO_DASHBOARD_PORT = int(os.getenv("ZO_DASHBOARD_PORT", "8050"))

# ── Production security ────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(32).hex())
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")


@dataclass
class MetaRLConfig:
    """Unified production configuration for Meta-RL engine."""

    # Core
    meta_rl_enabled: bool = field(default=META_RL_ENABLED)
    risk_integration_enabled: bool = field(default=RISK_INTEGRATION_ENABLED)
    karl_meta_update_enabled: bool = field(default=KARL_META_UPDATE_ENABLED)
    execution_sanity_enabled: bool = field(default=EXECUTION_SANITY_ENABLED)

    # Walk-forward
    walk_forward_enabled: bool = field(default=WALK_FORWARD_ENABLED)
    oos_overfit_threshold: float = field(default=OOS_OVERFIT_THRESHOLD)
    n_splits: int = field(default=5)
    train_window: int = field(default=100)
    test_window: int = field(default=20)

    # Capital & Risk
    initial_capital: float = field(default=100_000.0)
    risk_pct: float = field(default=0.02)
    max_drawdown_threshold: float = field(default=0.15)
    min_trades: int = field(default=5)

    # CCXT
    ccxt_sandbox_mode: bool = field(default=CCXT_SANDBOX_MODE)
    ccxt_exchange: str = field(default=CCXT_EXCHANGE)
    ccxt_rate_limit: int = field(default=CCXT_RATE_LIMIT)
    ccxt_enable_rate_limit: bool = field(default=CCXT_ENABLE_RATE_LIMIT)

    # Alerts
    telegram_alerts_enabled: bool = field(default=TELEGRAM_ALERTS_ENABLED)
    telegram_min_reward: float = field(default=TELEGRAM_MIN_REWARD_ALERT)

    # Reports
    html_reports_enabled: bool = field(default=HTML_REPORTS_ENABLED)
    reports_output_dir: str = field(default=REPORTS_OUTPUT_DIR)
    composite_ranking_enabled: bool = field(default=COMPOSITE_RANKING_ENABLED)
    composite_weights: dict = field(default_factory=lambda: dict(COMPOSITE_WEIGHTS))

    def __post_init__(self):
        total = sum(
            self.composite_weights.get(k, 0)
            for k in [
                "sharpe",
                "win_rate",
                "risk_adjusted_pnl",
                "stability",
                "diversity",
            ]
        )
        if abs(total - 1.0) > 0.01:
            norm = total
            for k in self.composite_weights:
                self.composite_weights[k] /= norm

    def is_production(self) -> bool:
        """True if configured for real market data (not sandbox)."""
        return not self.ccxt_sandbox_mode and bool(CCXT_API_KEY)

    def validate(self) -> list[str]:
        """Return list of validation warnings. Empty = all good."""
        warnings = []
        if self.is_production():
            if not CCXT_API_KEY:
                warnings.append("CCXT_API_KEY not set — cannot access real exchange")
            if not TELEGRAM_BOT_TOKEN:
                warnings.append("TELEGRAM_BOT_TOKEN not set — alerts disabled")
        if self.walk_forward_enabled and self.train_window < self.test_window * 2:
            warnings.append("train_window should be >= test_window * 2 for valid OOS")
        if self.composite_ranking_enabled:
            total = sum(self.composite_weights.values())
            if abs(total - 1.0) > 0.001:
                warnings.append(f"Composite weights sum to {total:.3f}, expected 1.0")
        return warnings


HYPEROPT_ENABLED = True
