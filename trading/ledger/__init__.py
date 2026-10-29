"""trading/ledger — persistent order ledger (orders, append-only hash-chained events, fills).

Not wired into the orchestrator or live paths; schema is created only via
``create_ledger_schema(engine)``.
"""

from .models import (
    ALLOWED_TRANSITIONS,
    TERMINAL_STATUSES,
    Decision,
    EventType,
    LedgerBase,
    LedgerFill,
    LedgerOrder,
    LedgerOrderEvent,
    OrderSide,
    OrderStatus,
    create_ledger_schema,
)
from .repository import (
    GENESIS_HASH,
    ChainBroken,
    ConcurrentAppend,
    FillRejected,
    IdempotencyConflict,
    InvalidTransition,
    LedgerError,
    OrderLedger,
    OrderNotFound,
    OrderRequest,
    canonical_json,
    compute_event_hash,
)

__all__ = [
    "ALLOWED_TRANSITIONS",
    "TERMINAL_STATUSES",
    "GENESIS_HASH",
    "ChainBroken",
    "ConcurrentAppend",
    "Decision",
    "EventType",
    "FillRejected",
    "IdempotencyConflict",
    "InvalidTransition",
    "LedgerBase",
    "LedgerError",
    "LedgerFill",
    "LedgerOrder",
    "LedgerOrderEvent",
    "OrderLedger",
    "OrderNotFound",
    "OrderRequest",
    "OrderSide",
    "OrderStatus",
    "canonical_json",
    "compute_event_hash",
    "create_ledger_schema",
]
