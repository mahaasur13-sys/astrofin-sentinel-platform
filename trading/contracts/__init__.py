"""trading/contracts — data contracts between research, risk and execution."""

from .adapter import from_signal_dict
from .signal import SCHEMA_VERSION, Evidence, Side, Signal, SignalRefused, Verdict, build_signal

__all__ = [
    "SCHEMA_VERSION",
    "Evidence",
    "Side",
    "Signal",
    "SignalRefused",
    "Verdict",
    "build_signal",
    "from_signal_dict",
]
