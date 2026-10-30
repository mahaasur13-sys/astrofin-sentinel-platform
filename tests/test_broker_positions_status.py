"""BinanceBroker.get_positions / get_order_status: fail-closed, no invented prices (no network)."""
from unittest import mock

import pytest

import trading.broker.binance as bmod
from trading.broker.base import BalanceUnavailableError, OrderStatus
from trading.broker.binance import BinanceBroker

MPU = getattr(bmod, "MarketPriceUnavailableError", RuntimeError)


def _broker(monkeypatch, ex):
    monkeypatch.setattr(bmod, "HAS_CCXT", True)
    b = BinanceBroker.__new__(BinanceBroker)
    b.paper = False
    b.connected = True
    b.exchange = ex
    return b


def _ex(last=50000.0, total=None):
    ex = mock.MagicMock()
    ex.fetch_balance.return_value = {"total": total if total is not None else {"USDT": 10.0, "BTC": 0.5}}
    ex.fetch_ticker.return_value = {"last": last}
    return ex


def test_positions_valid_price_entry_unknown(monkeypatch):
    ps = _broker(monkeypatch, _ex()).get_positions()
    assert len(ps) == 1
    p = ps[0]
    assert p.symbol == "BTC" and p.quantity == 0.5 and p.current_price == 50000.0
    assert p.avg_entry_price is None  # spot balance has no entry price — never 0
    assert p.unrealized_pnl is None and p.unrealized_pnl_pct is None


@pytest.mark.parametrize("last", [None, 0, -1, float("nan"), float("inf"), "x"])
def test_positions_invalid_ticker_raises(monkeypatch, last):
    with pytest.raises(MPU):
        _broker(monkeypatch, _ex(last=last)).get_positions()


def test_positions_ticker_error_raises(monkeypatch):
    ex = _ex()
    ex.fetch_ticker.side_effect = RuntimeError("boom")
    with pytest.raises(MPU):
        _broker(monkeypatch, ex).get_positions()


def test_positions_balance_error_raises(monkeypatch):
    ex = _ex()
    ex.fetch_balance.side_effect = RuntimeError("boom")
    with pytest.raises(BalanceUnavailableError):
        _broker(monkeypatch, ex).get_positions()


def test_positions_skips_zero_and_bad_qty(monkeypatch):
    ps = _broker(monkeypatch, _ex(total={"USDT": 1, "ETH": 0, "XRP": None, "BTC": 1})).get_positions()
    assert [p.symbol for p in ps] == ["BTC"]


def _order(**kw):
    o = {"id": "1", "symbol": "BTC/USDT", "side": "buy", "amount": 1.0,
         "price": 100.0, "status": "closed", "filled": 1.0, "average": 100.0}
    o.update(kw)
    return o


def _status(monkeypatch, order):
    ex = mock.MagicMock()
    ex.fetch_order.return_value = order
    return _broker(monkeypatch, ex).get_order_status("1")


@pytest.mark.parametrize("price", [None, "abc", float("nan")])
def test_order_status_bad_price_keeps_status(monkeypatch, price):
    o = _status(monkeypatch, _order(price=price, status="open", filled=0.0))
    assert o is not None
    assert o.status == OrderStatus.PENDING
    assert o.price is None


def test_order_status_market_closed_price_none(monkeypatch):
    o = _status(monkeypatch, _order(price=None))
    assert o.status == OrderStatus.FILLED and o.filled_qty == 1.0
    assert o.avg_fill_price == 100.0 and o.price is None


@pytest.mark.parametrize("avg", [None, "x", 0])
def test_order_status_bad_average(monkeypatch, avg):
    o = _status(monkeypatch, _order(average=avg))
    assert o.status == OrderStatus.FILLED and o.avg_fill_price == 0.0


@pytest.mark.parametrize("filled", [None, "x"])
def test_order_status_unknown_filled_closed_is_unknown(monkeypatch, filled):
    o = _status(monkeypatch, _order(filled=filled))
    assert o.status == OrderStatus.UNKNOWN and o.filled_qty == 0.0


def test_order_status_unknown_filled_canceled_kept(monkeypatch):
    o = _status(monkeypatch, _order(filled=None, status="canceled"))
    assert o.status == OrderStatus.CANCELLED


def test_order_status_partial(monkeypatch):
    o = _status(monkeypatch, _order(filled=0.4))
    assert o.status == OrderStatus.PARTIAL and o.filled_qty == 0.4


def test_order_status_fetch_error_none(monkeypatch):
    ex = mock.MagicMock()
    ex.fetch_order.side_effect = RuntimeError("boom")
    assert _broker(monkeypatch, ex).get_order_status("1") is None
