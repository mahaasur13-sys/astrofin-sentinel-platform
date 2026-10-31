"""trading/broker/binance.py — ATOM-STEP-9: Binance broker adapter"""

from __future__ import annotations

import math
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


def _finite_pos_or_none(v, allow_zero: bool = False):
    """float(v) if finite and > 0 (or >= 0 with allow_zero), else None."""
    if v is None or isinstance(v, bool):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f) or f < 0 or (f == 0 and not allow_zero):
        return None
    return f


# ccxt unified order type -> internal OrderType. Unknown/missing -> None (never MARKET by default).
_CCXT_ORDER_TYPES = {
    "market": OrderType.MARKET,
    "limit": OrderType.LIMIT,
    "limit_maker": OrderType.LIMIT,
    "stop": OrderType.STOP,
    "stop_market": OrderType.STOP,
    "stop_loss": OrderType.STOP,
    "take_profit": OrderType.STOP,
    "take_profit_market": OrderType.STOP,
    "stop_limit": OrderType.STOP_LIMIT,
    "stop_loss_limit": OrderType.STOP_LIMIT,
    "take_profit_limit": OrderType.STOP_LIMIT,
}
_CCXT_SIDES = {"buy": OrderSide.BUY, "sell": OrderSide.SELL}

# Quote stablecoins: not positions (cash-like). Also the fallback quotes used to price
# an asset that has no X/USDT market (priced ~1:1 to USDT — see get_positions).
STABLECOINS = ("USDT", "USDC", "FDUSD", "BUSD")


class MarketPriceUnavailableError(RuntimeError):
    """No valid market price (not connected, ticker error, or invalid last). Never 0.0."""


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
            # Fail-closed: a disconnected broker has an UNKNOWN balance, not a zero one.
            raise BalanceUnavailableError("broker not connected — balance unknown")
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
        """Spot holdings from fetch_balance, priced by fetch_ticker.

        Fail-closed:
          * fetch_balance error -> BalanceUnavailableError (not [] = "no positions");
          * invalid ticker (error/None/<=0/nan/inf) -> MarketPriceUnavailableError
            (no position priced at 0, no silent skip that hides exposure);
          * spot balance carries no entry price -> avg_entry_price/unrealized_* = None.
        """
        if not self.connected:
            return []
        if not HAS_CCXT or not self.exchange:
            return []
        try:
            balance = self.exchange.fetch_balance()
        except Exception as e:
            BROKER_ERRORS.inc()
            raise BalanceUnavailableError(f"fetch_balance failed: {type(e).__name__}") from e
        totals = balance.get("total") if isinstance(balance, dict) else None
        positions = []
        for symbol, data in (totals or {}).items():
            qty = _finite_pos_or_none(data)
            if qty is None or str(symbol).upper() in STABLECOINS:
                continue  # zero/invalid qty, or a stablecoin (cash, not a position)
            price = self._price_in_usd_quote(symbol)
            positions.append(
                Position(
                    symbol=symbol,
                    quantity=qty,
                    avg_entry_price=None,
                    current_price=price,
                    unrealized_pnl=None,
                    unrealized_pnl_pct=None,
                )
            )
        return positions

    def _price_in_usd_quote(self, asset: str) -> float:
        """Last price of `asset` against USDT, else the first other stablecoin quote
        that has a market (X/USDC, X/FDUSD, X/BUSD; approximated 1:1 to USDT).
        No valid price on any of them -> MarketPriceUnavailableError (exposure is
        never hidden: an asset with a balance but no price fails the whole call)."""
        errors = []
        for quote in STABLECOINS:
            pair = f"{asset}/{quote}"
            try:
                ticker = self.exchange.fetch_ticker(pair)
            except Exception as e:
                errors.append(f"{pair}: {type(e).__name__}")
                continue
            last = ticker.get("last") if isinstance(ticker, dict) else None
            price = _finite_pos_or_none(last)
            if price is not None:
                if quote != "USDT":
                    log.warning("[BinanceBroker] %s priced via %s (no valid %s/USDT)", asset, pair, asset)
                return price
            errors.append(f"{pair}: invalid last={last!r}")
        BROKER_ERRORS.inc()
        raise MarketPriceUnavailableError(f"no valid price for {asset}: " + "; ".join(errors))

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
            return self._order_from_create_response(
                order, order_id, symbol, side, order_type, quantity, price, cid
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

    @staticmethod
    def _order_from_create_response(order, fallback_id, symbol, side, order_type, quantity, price, cid) -> Order:
        """Build Order from a ccxt create_order response WITHOUT inventing fills.

        * status via _map_ccxt_status (closed & filled<amount → PARTIAL, open → PENDING, ...);
        * filled missing/invalid → filled_qty=0 and, unless the order is plainly not filled
          (open/canceled/rejected with nothing reported), status UNKNOWN: the exchange may have
          filled any amount, so the caller must reconcile by clientOrderId, never assume quantity;
        * closed with filled == 0 is contradictory → UNKNOWN;
        * avg price only from average/price of the response, else 0.0 (= not known).
        """
        order = order if isinstance(order, dict) else {}
        filled = _finite_pos_or_none(order.get("filled"), allow_zero=True)
        amount = order.get("amount")
        if _finite_pos_or_none(amount) is None:
            amount = quantity
        raw_status = str(order.get("status") or "").lower()
        notes = ""
        if filled is None:
            status = _map_ccxt_status(raw_status, 0.0, amount)
            if status not in (OrderStatus.PENDING, OrderStatus.CANCELLED, OrderStatus.REJECTED):
                status = OrderStatus.UNKNOWN
                notes = f"exchange response has no valid 'filled' (status={raw_status or None}) — reconcile by clientOrderId"
            filled = 0.0
        else:
            status = _map_ccxt_status(raw_status, filled, amount)
            if raw_status == "closed" and filled == 0:
                status = OrderStatus.UNKNOWN
                notes = "exchange reports closed with filled=0 — reconcile by clientOrderId"
            elif status is OrderStatus.UNKNOWN:
                notes = f"unrecognised exchange status {raw_status or None!r} — reconcile by clientOrderId"
        avg = _finite_pos_or_none(order.get("average"))
        if avg is None and filled > 0:
            avg = _finite_pos_or_none(order.get("price"))
        fee = order.get("fee") if isinstance(order.get("fee"), dict) else {}
        commission = _finite_pos_or_none(fee.get("cost"), allow_zero=True) or 0.0
        ts = _finite_pos_or_none(order.get("timestamp"))
        return Order(
            order_id=str(order.get("id") or fallback_id),
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            status=status,
            filled_qty=filled,
            avg_fill_price=avg or 0.0,
            commission=commission,
            created_at=(ts / 1000) if ts else time.time(),
            notes=notes,
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
        except Exception:
            BROKER_ERRORS.inc()
            return None
        if not isinstance(order, dict):
            BROKER_ERRORS.inc()
            return None
        amount = _finite_pos_or_none(order.get("amount"))
        filled = _finite_pos_or_none(order.get("filled"), allow_zero=True)
        notes = ""
        if filled is None:
            # Unknown executed volume: keep terminal no-fill states, else UNKNOWN.
            status = _map_ccxt_status(order.get("status"), 0.0, amount)
            if status not in (OrderStatus.PENDING, OrderStatus.CANCELLED, OrderStatus.REJECTED):
                status = OrderStatus.UNKNOWN
            notes = f"filled unknown ({order.get('filled')!r})"
            filled = 0.0
        else:
            status = _map_ccxt_status(order.get("status"), filled, amount)
        if amount is None:
            notes = (notes + "; " if notes else "") + f"amount unknown ({order.get('amount')!r})"
        side = _CCXT_SIDES.get(str(order.get("side") or "").lower())
        if side is None:
            # Fail-closed: an order of unknown direction must not be reported as SELL.
            BROKER_ERRORS.inc()
            log.warning("[BinanceBroker] order %s has unknown side %r — status not reported", order_id, order.get("side"))
            return None
        raw_type = str(order.get("type") or "").lower()
        order_type = _CCXT_ORDER_TYPES.get(raw_type)
        if order_type is None:
            notes = (notes + "; " if notes else "") + f"order type unknown ({order.get('type')!r})"
        return Order(
            order_id=str(order.get("id") or order_id),
            symbol=str(order.get("symbol") or ""),
            side=side,
            order_type=order_type,  # None = unknown, never assumed MARKET
            quantity=amount if amount is not None else 0.0,
            price=_finite_pos_or_none(order.get("price")),  # None = unknown, never invented
            status=status,
            filled_qty=filled,
            avg_fill_price=_finite_pos_or_none(order.get("average")) or 0.0,  # 0.0 = unknown (#492)
            notes=notes,
        )

    def get_market_price(self, symbol: str) -> float:
        """Last price; fail-closed: raises MarketPriceUnavailableError, never returns 0.0."""
        if not self.connected:
            raise MarketPriceUnavailableError("broker not connected — market price unknown")
        if not HAS_CCXT or not self.exchange:
            # Fail-closed: never invent a price.
            raise MarketPriceUnavailableError("ccxt/exchange unavailable — market price unknown")
        try:
            ticker = self.exchange.fetch_ticker(symbol)
        except Exception as e:
            BROKER_ERRORS.inc()
            raise MarketPriceUnavailableError(f"fetch_ticker failed: {type(e).__name__}") from e
        last = ticker.get("last") if isinstance(ticker, dict) else None
        price = _finite_pos_or_none(last)
        if price is None:
            BROKER_ERRORS.inc()
            raise MarketPriceUnavailableError(f"invalid ticker last={last!r}")
        return price

    def __repr__(self) -> str:
        status = "connected" if self.connected else "disconnected"
        mode = "PAPER" if self.paper else "LIVE"
        return f"BinanceBroker({mode}, {status})"
