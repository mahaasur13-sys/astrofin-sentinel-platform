"""trading/broker/binance.py — ATOM-STEP-9: Binance broker adapter"""

from __future__ import annotations

import time

import yaml

import logging
log = logging.getLogger(__name__)


try:
    import ccxt

    HAS_CCXT = True
except ImportError:
    HAS_CCXT = False

from tools.metrics_server import BROKER_ERRORS

from .base import (
    AccountBalance,
    BalanceUnavailableError,
    BaseBroker,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    new_client_order_id,
    validate_client_order_id,
)


def _is_definite_reject(exc: Exception) -> bool:
    """True only for errors where the exchange definitely did NOT accept the order.

    Network errors / timeouts (and anything unclassifiable) are NOT definite: the
    request may have been executed, so the caller must reconcile by clientOrderId.
    """
    if not HAS_CCXT:
        return False
    if isinstance(exc, ccxt.NetworkError):
        return False
    return isinstance(exc, ccxt.ExchangeError)


def _map_ccxt_status(status, filled: float, amount=None) -> OrderStatus:
    """Map a ccxt unified order status to OrderStatus. Unknown → UNKNOWN (never silent PENDING)."""
    st = str(status or "").lower()
    try:
        amt = float(amount) if amount is not None else None
    except (TypeError, ValueError):
        amt = None
    if st == "closed":
        if amt is not None and 0 < filled < amt:
            return OrderStatus.PARTIAL
        return OrderStatus.FILLED
    if st in ("canceled", "cancelled", "expired"):
        return OrderStatus.PARTIAL if filled > 0 else OrderStatus.CANCELLED
    if st == "rejected":
        return OrderStatus.REJECTED
    if st == "open":
        return OrderStatus.PARTIAL if filled > 0 else OrderStatus.PENDING
    return OrderStatus.UNKNOWN


class BinanceBroker(BaseBroker):
    """Binance spot/futures broker via CCXT."""

    def __init__(self, paper: bool = True, config_path: str | None = None):
        super().__init__(paper=paper)
        self.api_key: str | None = None
        self.secret: str | None = None
        self.exchange: object | None = None
        self._load_credentials(config_path)

    def _load_credentials(self, config_path: str | None = None):
        import os

        self.api_key = os.environ.get("BINANCE_API_KEY")
        self.secret = os.environ.get("BINANCE_SECRET")
        if not self.api_key and config_path:
            try:
                with open(config_path) as f:
                    creds = yaml.safe_load(f)
                    self.api_key = creds.get("api_key")
                    self.secret = creds.get("secret")
            except Exception:
                pass

    def connect(self) -> bool:
        if not HAS_CCXT:
            # Fail-closed: no exchange client -> NOT connected. Simulation lives in
            # trading/paper_broker.py (TRADING_MODE=PAPER), never here.
            log.error("BinanceBroker: ccxt not installed — cannot connect (no simulation).")
            self.connected = False
            return False
        try:
            config = {"enableRateLimit": True, "options": {"defaultType": "spot"}}
            if not self.paper and self.api_key and self.secret:
                config["apiKey"] = self.api_key
                config["secret"] = self.secret
            else:
                config["test"] = True
            self.exchange = ccxt.binance(config)
            self.exchange.fetch_balance()
            self.connected = True
            log.info(f"BinanceBroker connected (paper={self.paper})")
            return True
        except Exception as e:
            BROKER_ERRORS.inc()
            log.info(f"Binance connection failed: {e}")
            self.connected = False
            return False

    def disconnect(self):
        self.exchange = None
        self.connected = False
        log.info("BinanceBroker disconnected")

    def get_account_balance(self) -> AccountBalance:
        if not self.connected:
            return AccountBalance(
                total_equity=0, available_cash=0, positions_value=0, total_pnl=0
            )
        if not HAS_CCXT or not self.exchange:
            # Fail-closed: no exchange client -> no real balance. Never invent equity.
            raise BalanceUnavailableError("ccxt/exchange unavailable — balance unknown")
        try:
            balance = self.exchange.fetch_balance()
            total_usd = float(balance.get("total", {}).get("USDT", 0))
            free_usd = float(balance.get("free", {}).get("USDT", 0))
            return AccountBalance(
                total_equity=total_usd,
                available_cash=free_usd,
                positions_value=total_usd - free_usd,
                total_pnl=0.0,
                currency="USDT",
            )
        except Exception as e:
            BROKER_ERRORS.inc()
            # Fail-closed: a failed fetch_balance must not become a fake 10000 equity.
            raise BalanceUnavailableError(f"fetch_balance failed: {type(e).__name__}") from e

    def get_positions(self) -> list[Position]:
        if not self.connected:
            return []
        if not HAS_CCXT or not self.exchange:
            return []
        try:
            balance = self.exchange.fetch_balance()
            positions = []
            for symbol, data in balance.get("total", {}).items():
                if symbol == "USDT" or float(data) <= 0:
                    continue
                try:
                    ticker = self.exchange.fetch_ticker(symbol + "/USDT")
                    price = ticker.get("last", 0)
                    qty = float(data)
                    positions.append(
                        Position(
                            symbol=symbol,
                            quantity=qty,
                            avg_entry_price=0,
                            current_price=price,
                            unrealized_pnl=0,
                            unrealized_pnl_pct=0,
                        )
                    )
                except Exception:
                    continue
            return positions
        except Exception:
            BROKER_ERRORS.inc()
            return []

    def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: float | None = None,
        client_order_id: str | None = None,
    ) -> Order:
        cid = validate_client_order_id(client_order_id) if client_order_id else new_client_order_id()
        order_id = f"sim_{int(time.time() * 1000)}"
        if not self.connected:
            return Order(
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                status=OrderStatus.REJECTED,
                notes="Not connected",
                client_order_id=cid,
            )
        if not HAS_CCXT or not self.exchange:
            # Fail-closed: without an exchange client nothing can be executed.
            return Order(
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                status=OrderStatus.REJECTED,
                notes="Exchange unavailable (ccxt/exchange missing)",
                client_order_id=cid,
            )
        if self.paper:
            # Fail-closed: paper simulation lives in trading/paper_broker.py
            # (TRADING_MODE=PAPER). No duplicate fill simulation on live tickers here.
            return Order(
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                status=OrderStatus.REJECTED,
                notes="BinanceBroker(paper=True) does not simulate fills — use PaperBroker (TRADING_MODE=PAPER)",
                client_order_id=cid,
            )
        try:
            side_str = "buy" if side == OrderSide.BUY else "sell"
            type_str = order_type.value
            # Binance spot (/api/v3/order) and USD-M futures (/fapi/v1/order) both take
            # newClientOrderId; a duplicate id is rejected by the exchange.
            params = {"newClientOrderId": cid}
            if order_type == OrderType.LIMIT or order_type == OrderType.STOP_LIMIT:
                order = self.exchange.create_order(
                    symbol, type_str, side_str, quantity, price, params
                )
            elif order_type == OrderType.STOP:
                order = self.exchange.create_order(
                    symbol, "stop", side_str, quantity, price, params
                )
            else:
                order = self.exchange.create_order(
                    symbol, "market", side_str, quantity, None, params
                )
            return Order(
                order_id=str(order.get("id", order_id)),
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                status=OrderStatus.FILLED,
                filled_qty=float(order.get("filled", quantity)),
                avg_fill_price=float(order.get("average", price or 0)),
                commission=float(order.get("fee", {}).get("cost", 0)),
                created_at=order.get("timestamp", time.time() * 1000) / 1000,
                client_order_id=cid,
            )
        except Exception as e:
            BROKER_ERRORS.inc()
            if not _is_definite_reject(e):
                # Outcome unknown: never resubmit blindly — look the order up by clientOrderId.
                return self._reconcile_by_client_id(
                    cid, symbol, side, order_type, quantity, price, e
                )
            return Order(
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                status=OrderStatus.REJECTED,
                notes=str(e),
                client_order_id=cid,
            )

    def _reconcile_by_client_id(
        self, cid, symbol, side, order_type, quantity, price, exc
    ) -> Order:
        """Query the order by origClientOrderId; UNKNOWN (fail-closed) if not confirmable."""
        try:
            o = self.exchange.fetch_order(None, symbol, {"origClientOrderId": cid})
        except Exception as qe:  # noqa: BLE001 — includes OrderNotFound: still not proof of absence
            BROKER_ERRORS.inc()
            log.warning("[BinanceBroker] order %s state UNKNOWN after %s; lookup failed: %s",
                        cid, type(exc).__name__, type(qe).__name__)
            return Order(
                order_id=cid, symbol=symbol, side=side, order_type=order_type,
                quantity=quantity, price=price, status=OrderStatus.UNKNOWN,
                notes=f"state unknown after {type(exc).__name__}: {exc}; lookup failed: {qe}",
                client_order_id=cid,
            )
        filled = float(o.get("filled") or 0)
        status = _map_ccxt_status(o.get("status"), filled, o.get("amount"))
        return Order(
            order_id=str(o.get("id") or cid), symbol=symbol, side=side,
            order_type=order_type, quantity=quantity, price=price, status=status,
            filled_qty=filled, avg_fill_price=float(o.get("average") or 0),
            notes=f"reconciled by clientOrderId after {type(exc).__name__}",
            client_order_id=cid,
        )

    def cancel_order(self, order_id: str) -> bool:
        if not self.connected or not HAS_CCXT or not self.exchange or self.paper:
            return False
        try:
            self.exchange.cancel_order(order_id)
            return True
        except Exception:
            BROKER_ERRORS.inc()
            return False

    def get_order_status(self, order_id: str) -> Order | None:
        if not self.connected:
            return None
        if "sim_" in order_id:
            return None
        if not HAS_CCXT or not self.exchange:
            return None
        try:
            order = self.exchange.fetch_order(order_id)
            return Order(
                order_id=str(order["id"]),
                symbol=order["symbol"],
                side=OrderSide.BUY if order["side"] == "buy" else OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=float(order["amount"]),
                price=float(order.get("price", 0)),
                status=_map_ccxt_status(
                    order.get("status"), float(order.get("filled") or 0), order.get("amount")
                ),
                filled_qty=float(order.get("filled") or 0),
            )
        except Exception:
            BROKER_ERRORS.inc()
            return None

    def get_market_price(self, symbol: str) -> float:
        if not self.connected:
            return 0.0
        if not HAS_CCXT or not self.exchange:
            # Fail-closed: never invent a price.
            raise RuntimeError("ccxt/exchange unavailable — market price unknown")
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return float(ticker.get("last", 0))
        except Exception:
            BROKER_ERRORS.inc()
            return 0.0

    def __repr__(self) -> str:
        status = "connected" if self.connected else "disconnected"
        mode = "PAPER" if self.paper else "LIVE"
        return f"BinanceBroker({mode}, {status})"
