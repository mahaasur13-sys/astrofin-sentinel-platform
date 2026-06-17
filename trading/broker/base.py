"""trading/broker/base.py — ATOM-STEP-9: Base broker interface"""

from __future__ import annotations

import time
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
    ) -> Order:
        """Place an order."""
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
