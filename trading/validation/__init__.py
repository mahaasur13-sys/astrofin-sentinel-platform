"""trading/validation — out-of-sample protocol for backtests.

Development / Validation / Final-OOS chronological split with embargo, walk-forward on
Dev+Validation only, a frozen protocol that must exist before the single permitted final-OOS
run, and leakage guards. Opt-in, offline: nothing here is used by live trading.

Results never claim an edge. Status is UNVERIFIED unless the final OOS ran exactly once on a
frozen protocol, and even then only FINAL_OOS_EVALUATED is reported.
"""

from .errors import ChronologyError, ContaminationError, LeakageError, ProtocolError, ValidationError
from .leakage import Bar, StrategyDecision, assert_no_feature_leakage
from .protocol import FrozenProtocol, ProtocolStore, data_fingerprint, params_hash
from .registry import HypothesisRegistry, spec_sha256
from .runner import (
    ValidationConfig,
    ValidationReport,
    WindowResult,
    buy_and_hold_metrics,
    evaluate_window,
    run_development,
    run_final_oos,
)
from .splits import Segment, Split, chronological_split, walk_forward_windows
from .stats import DeflatedSharpe, buy_and_hold_returns, deflated_sharpe_ratio, expected_max_sharpe, performance_metrics

__all__ = [
    "Bar",
    "ChronologyError",
    "ContaminationError",
    "DeflatedSharpe",
    "HypothesisRegistry",
    "FrozenProtocol",
    "LeakageError",
    "ProtocolError",
    "ProtocolStore",
    "Segment",
    "Split",
    "StrategyDecision",
    "ValidationConfig",
    "ValidationError",
    "ValidationReport",
    "WindowResult",
    "assert_no_feature_leakage",
    "buy_and_hold_metrics",
    "buy_and_hold_returns",
    "chronological_split",
    "data_fingerprint",
    "deflated_sharpe_ratio",
    "evaluate_window",
    "expected_max_sharpe",
    "params_hash",
    "performance_metrics",
    "run_development",
    "run_final_oos",
    "spec_sha256",
    "walk_forward_windows",
]
