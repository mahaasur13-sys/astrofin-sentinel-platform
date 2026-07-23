"""trading/broker/binance.py — ATOM-STEP-9: Binance broker adapter"""

from __future__ import annotations

import time

import yaml

try:
    import ccxt

    HAS_CCXT = True
except ImportError:
    HAS_CCXT = False

from tools.metrics_server import BROKER_ERRORS

from .base import (
    AccountBalance,
    BaseBroker,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
)


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
            print("Warning: ccxt not installed. Running in simulation mode.")
            self.connected = True
            return True
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
            print(f"BinanceBroker connected (paper={self.paper})")
            return True
        except Exception as e:
            BROKER_ERRORS.inc()
            print(f"Binance connection failed: {e}")
            self.connected = False
            return False

    def disconnect(self):
        self.exchange = None
        self.connected = False
        print("BinanceBroker disconnected")

    def get_account_balance(self) -> AccountBalance:
        if not self.connected:
            return AccountBalance(total_equity=0, available_cash=0, positions_value=0, total_pnl=0)
        if not HAS_CCXT or not self.exchange:
            return AccountBalance(
                total_equity=10000.0,
                available_cash=10000.0,
                positions_value=0.0,
                total_pnl=0.0,
                currency="USDT",
            )
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
        except Exception:
            BROKER_ERRORS.inc()
            return AccountBalance(total_equity=10000, available_cash=10000, positions_value=0, total_pnl=0)

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
    ) -> Order:
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
            )
        if not HAS_CCXT or not self.exchange or self.paper:
            exec_price = price or self.get_market_price(symbol)
            commission = quantity * exec_price * 0.001
            return Order(
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                status=OrderStatus.FILLED,
                filled_qty=quantity,
                avg_fill_price=exec_price,
                commission=commission,
                notes="Paper simulation" if self.paper else "Live (testnet)",
            )
        try:
            side_str = "buy" if side == OrderSide.BUY else "sell"
            type_str = order_type.value
            if order_type == OrderType.LIMIT or order_type == OrderType.STOP_LIMIT:
                order = self.exchange.create_order(symbol, type_str, side_str, quantity, price)
            elif order_type == OrderType.STOP:
                order = self.exchange.create_order(symbol, "stop", side_str, quantity, price)
            else:
                order = self.exchange.create_order(symbol, "market", side_str, quantity)
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
            )
        except Exception as e:
            BROKER_ERRORS.inc()
            return Order(
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                status=OrderStatus.REJECTED,
                notes=str(e),
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
                status=(OrderStatus.FILLED if order["status"] == "closed" else OrderStatus.PENDING),
                filled_qty=float(order.get("filled", 0)),
            )
        except Exception:
            BROKER_ERRORS.inc()
            return None

    def get_market_price(self, symbol: str) -> float:
        if not self.connected:
            return 0.0
        if not HAS_CCXT or not self.exchange:
            return 100.0
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
