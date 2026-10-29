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
    GLOBAL_KEY,
    KillScope,
    LedgerKillSwitch,
    LedgerKillSwitchAudit,
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

from .killswitch import KillSwitch, KillSwitchAuditBroken, KillSwitchState  # noqa: E402
from .recovery import RecoveryAction, RecoveryReport, recover  # noqa: E402

__all__ = [
    "GLOBAL_KEY",
    "KillScope",
    "KillSwitch",
    "KillSwitchAuditBroken",
    "KillSwitchState",
    "LedgerKillSwitch",
    "LedgerKillSwitchAudit",
    "RecoveryAction",
    "RecoveryReport",
    "recover",
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
