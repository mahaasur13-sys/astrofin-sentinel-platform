"""trading/broker/base.py — ATOM-STEP-9: Base broker interface"""

from __future__ import annotations

import re
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    # Request may have reached the exchange but the outcome could not be confirmed.
    # Fail-closed: callers must NOT resubmit; reconcile by client_order_id instead.
    UNKNOWN = "UNKNOWN"


# Binance: newClientOrderId must match ^[\.A-Z\:/a-z0-9_-]{1,36}$
CLIENT_ORDER_ID_RE = re.compile(r"^[\.A-Z\:/a-z0-9_-]{1,36}$")


def new_client_order_id(prefix: str = "af") -> str:
    """Unique idempotency id, <=36 chars, Binance-safe charset."""
    return f"{prefix}-{uuid.uuid4().hex}"[:36]


def validate_client_order_id(cid: str) -> str:
    if not isinstance(cid, str) or not CLIENT_ORDER_ID_RE.match(cid):
        raise ValueError(f"invalid client_order_id: {cid!r}")
    return cid


@dataclass
class Order:
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: float | None = None
    status: OrderStatus = OrderStatus.PENDING
    filled_qty: float = 0.0
    avg_fill_price: float = 0.0
    commission: float = 0.0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    notes: str = ""
    client_order_id: str | None = None


@dataclass
class Position:
    symbol: str
    quantity: float
    avg_entry_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0


@dataclass
class AccountBalance:
    total_equity: float
    available_cash: float
    positions_value: float
    total_pnl: float
    currency: str = "USDT"


class BaseBroker(ABC):
    """Abstract base class for all broker integrations."""

    def __init__(self, paper: bool = True):
        self.paper = paper
        self.connected = False

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to broker/exchange."""
        ...

    @abstractmethod
    def disconnect(self):
        """Close connection."""
        ...

    @abstractmethod
    def get_account_balance(self) -> AccountBalance:
        """Get current account balance."""
        ...

    @abstractmethod
    def get_positions(self) -> list[Position]:
        """Get open positions."""
        ...

    @abstractmethod
    def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: float | None = None,
        client_order_id: str | None = None,
    ) -> Order:
        """Place an order.

        ``client_order_id`` is the idempotency key: resubmitting with the same id must
        never create a second order. If omitted, the broker generates one and returns it
        in ``Order.client_order_id``. If the outcome cannot be confirmed the broker returns
        ``OrderStatus.UNKNOWN`` (caller must reconcile, not retry with a new id).
        """
        ...

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by ID."""
        ...

    @abstractmethod
    def get_order_status(self, order_id: str) -> Order | None:
        """Get status of a specific order."""
        ...

    @abstractmethod
    def get_market_price(self, symbol: str) -> float:
        """Get current market price for symbol."""
        ...

    @property
    def name(self) -> str:
        return self.__class__.__name__.replace("Broker", "").lower()
