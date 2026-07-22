"""
trading/paper_broker.py — Paper Trading Broker (Sprint 8.1).

Simulates order execution with real-time Binance prices from data_room,
emulated slippage + commission, and virtual balance tracking.
Identical interface to BinanceBroker — drop-in replacement via factory.
"""

from __future__ import annotations

import time
import uuid

from tools.data_provider import fetch_current_price

from .broker.base import (
    AccountBalance,
    BaseBroker,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
)

import logging
log = logging.getLogger(__name__)


class PaperBroker(BaseBroker):
    """Paper trading broker — simulates execution on real market prices.

    Uses data_room/binance_resolver for live prices, emulates:
      - Slippage (0.05% by default)
      - Commission (0.1% by default)
      - Virtual balance tracking
      - Position tracking

    Does NOT require ccxt or API keys.
    """

    def __init__(
        self,
        paper: bool = True,
        initial_balance: float = 10000.0,
        fee_rate: float = 0.001,
        slippage_rate: float = 0.0005,
    ):
        super().__init__(paper=paper)
        self._balance = {"USDT": initial_balance}
        self._positions: dict[str, float] = {}
        self._avg_entry: dict[str, float] = {}
        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate
        self._order_history: list[Order] = []
        self.connected = True

    # ── BaseBroker abstract interface ──────────────────────────────────

    def connect(self) -> bool:
        self.connected = True
        log.info("PaperBroker connected (simulation mode)")
        return True

    def disconnect(self):
        self.connected = True  # Always available
        log.info("PaperBroker disconnected")

    def get_account_balance(self) -> AccountBalance:
        positions_value = sum(
            qty * self.get_market_price(sym)
            for sym, qty in self._positions.items()
        )
        total = self._balance.get("USDT", 0) + positions_value
        return AccountBalance(
            total_equity=total,
            available_cash=self._balance.get("USDT", 0),
            positions_value=positions_value,
            total_pnl=total - sum(
                self._avg_entry.get(sym, 0) * qty
                for sym, qty in self._positions.items()
            ),
            currency="USDT",
        )

    def get_positions(self) -> list[Position]:
        positions = []
        for sym, qty in self._positions.items():
            if qty <= 0:
                continue
            price = self.get_market_price(sym)
            positions.append(
                Position(
                    symbol=sym,
                    quantity=qty,
                    avg_entry_price=self._avg_entry.get(sym, price),
                    current_price=price,
                    unrealized_pnl=qty * (price - self._avg_entry.get(sym, price)),
                )
            )
        return positions

    def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: float | None = None,
    ) -> Order:
        """Place a simulated order with slippage + commission."""
        oid = f"paper_{uuid.uuid4().hex[:12]}"
        now = time.time()

        # 1. Get real market price
        try:
            current_price = fetch_current_price(symbol)
        except Exception as e:
            log.warning(f"[PaperBroker] Price fetch failed for {symbol}: {e}")
            if price and price > 0:
                current_price = price
            else:
                return Order(
                    order_id=oid, symbol=symbol, side=side, order_type=order_type,
                    quantity=quantity, price=price, status=OrderStatus.REJECTED,
                    notes=f"Price fetch failed: {e}",
                )

        # 2. Emulate slippage
        slippage = current_price * self.slippage_rate
        if side == OrderSide.BUY:
            exec_price = current_price + slippage
        else:
            exec_price = current_price - slippage
        if price and order_type != OrderType.MARKET:
            exec_price = price

        # 3. Commission
        cost = exec_price * quantity
        fee = cost * self.fee_rate

        # 4. Balance check + update
        if side == OrderSide.BUY:
            if self._balance.get("USDT", 0) < cost + fee:
                return Order(
                    order_id=oid, symbol=symbol, side=side, order_type=order_type,
                    quantity=quantity, price=exec_price, status=OrderStatus.REJECTED,
                    notes=f"Insufficient balance: need {cost + fee:.2f}, have {self._balance.get('USDT', 0):.2f}",
                )
            self._balance["USDT"] -= (cost + fee)
            old_qty = self._positions.get(symbol, 0)
            if old_qty > 0:
                old_cost = self._avg_entry.get(symbol, 0) * old_qty
                new_cost = old_cost + cost
                self._positions[symbol] = old_qty + quantity
                self._avg_entry[symbol] = new_cost / self._positions[symbol]
            else:
                self._positions[symbol] = quantity
                self._avg_entry[symbol] = exec_price
        else:
            if self._positions.get(symbol, 0) < quantity:
                return Order(
                    order_id=oid, symbol=symbol, side=side, order_type=order_type,
                    quantity=quantity, price=exec_price, status=OrderStatus.REJECTED,
                    notes=f"Insufficient position: have {self._positions.get(symbol, 0)}, need {quantity}",
                )
            self._balance["USDT"] += (cost - fee)
            self._positions[symbol] -= quantity
            if self._positions[symbol] <= 0:
                self._positions.pop(symbol, None)
                self._avg_entry.pop(symbol, None)

        # 5. Record order
        order = Order(
            order_id=oid, symbol=symbol, side=side, order_type=order_type,
            quantity=quantity, price=exec_price,
            status=OrderStatus.FILLED, filled_qty=quantity,
            avg_fill_price=exec_price,
            commission=fee, created_at=now, updated_at=now,
            notes=f"Paper: slippage={slippage:.4f}, fee={fee:.4f}",
        )
        self._order_history.append(order)

        log.info(
            f"[PaperBroker] {side.name} {quantity} {symbol} @ {exec_price:.2f} "
            f"(slippage={slippage:+.4f}, fee={fee:.4f}, balance={self._balance['USDT']:.2f})"
        )
        return order

    def cancel_order(self, order_id: str) -> bool:
        log.info(f"[PaperBroker] cancel_order({order_id}) — no-op in paper mode")
        return False

    def get_order_status(self, order_id: str) -> Order | None:
        for o in self._order_history:
            if o.order_id == order_id:
                return o
        return None

    def get_market_price(self, symbol: str) -> float:
        try:
            return fetch_current_price(symbol)
        except Exception:
            return 0.0

    @property
    def name(self) -> str:
        return "paper"


_paper_broker: PaperBroker | None = None


def get_paper_broker() -> PaperBroker:
    """Global singleton for paper broker."""
    global _paper_broker
    if _paper_broker is None:
        _paper_broker = PaperBroker()
    return _paper_broker
