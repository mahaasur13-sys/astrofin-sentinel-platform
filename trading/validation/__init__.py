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
from .runner import (
    ValidationConfig,
    ValidationReport,
    WindowResult,
    evaluate_window,
    run_development,
    run_final_oos,
)
from .splits import Segment, Split, chronological_split, walk_forward_windows

__all__ = [
    "Bar",
    "ChronologyError",
    "ContaminationError",
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
    "chronological_split",
    "data_fingerprint",
    "evaluate_window",
    "params_hash",
    "run_development",
    "run_final_oos",
    "walk_forward_windows",
]
