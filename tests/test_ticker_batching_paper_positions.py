"""Binance valuation: batched tickers + short valuation-only cache; PaperBroker
positions fail-closed. No network (mocked exchange / price source)."""
from __future__ import annotations

from unittest import mock

import pytest

import trading.broker.binance as bmod
import trading.paper_broker as pmod
from trading.broker.base import BalanceUnavailableError, OrderSide, OrderType
from trading.broker.binance import BinanceBroker, MarketPriceUnavailableError
from trading.paper_broker import PaperBroker


def _broker(monkeypatch, ex):
    monkeypatch.setattr(bmod, "HAS_CCXT", True)
    b = BinanceBroker.__new__(BinanceBroker)
    b.paper = False
    b.connected = True
    b.exchange = ex
    return b


PRICES = {"BTC/USDT": 50_000.0, "ETH/USDT": 3_000.0, "SOL/USDT": 150.0}


def _ex(total=None, batch_ok=True):
    ex = mock.MagicMock()
    ex.fetch_balance.return_value = {"total": total or {"USDT": 10.0, "BTC": 0.1, "ETH": 1.0, "SOL": 2.0},
                                     "free": {"USDT": 10.0}}

    def _one(pair):
        if pair not in PRICES:
            raise RuntimeError(f"BadSymbol {pair}")
        return {"last": PRICES[pair]}

    def _many(pairs):
        if not batch_ok:
            raise RuntimeError("fetchTickers not supported")
        return {p: {"last": PRICES[p]} for p in pairs if p in PRICES}

    ex.fetch_ticker.side_effect = _one
    ex.fetch_tickers.side_effect = _many
    return ex


def _calls(ex):
    return ex.fetch_ticker.call_count + ex.fetch_tickers.call_count


def test_cycle_balance_plus_positions_one_batch(monkeypatch):
    ex = _ex()
    b = _broker(monkeypatch, ex)
    bal = b.get_account_balance()
    ps = b.get_positions()
    assert bal.total_equity == pytest.approx(10 + 5_000 + 3_000 + 300)
    assert {p.symbol for p in ps} == {"BTC", "ETH", "SOL"}
    assert ex.fetch_tickers.call_count == 1 and ex.fetch_ticker.call_count == 0
    assert _calls(ex) <= 1  # master: 6 (3 assets x 2 methods)


def test_batch_unsupported_falls_back_per_symbol_once(monkeypatch):
    ex = _ex(batch_ok=False)
    b = _broker(monkeypatch, ex)
    b.get_account_balance()
    b.get_positions()
    assert ex.fetch_ticker.call_count == 3  # once per asset, positions served from cache


def test_batch_missing_symbol_falls_back(monkeypatch):
    ex = _ex(total={"BTC": 0.1, "XYZ": 10.0})
    PRICES_XYZ = {"XYZ/USDC": 2.0}
    orig = ex.fetch_ticker.side_effect

    def _one(pair):
        return {"last": PRICES_XYZ[pair]} if pair in PRICES_XYZ else orig(pair)

    ex.fetch_ticker.side_effect = _one
    bal = _broker(monkeypatch, ex).get_account_balance()
    assert bal.total_equity == pytest.approx(5_000 + 20)


def test_no_valid_price_still_fail_closed(monkeypatch):
    ex = _ex(total={"USDT": 1.0, "DUST": 1.0})
    b = _broker(monkeypatch, ex)
    with pytest.raises(BalanceUnavailableError):
        b.get_account_balance()
    with pytest.raises(MarketPriceUnavailableError):
        b.get_positions()


def test_ttl_expired_refetches(monkeypatch):
    ex = _ex()
    b = _broker(monkeypatch, ex)
    t = [1000.0]
    monkeypatch.setattr(bmod.time, "monotonic", lambda: t[0])
    b.get_account_balance()
    t[0] += bmod.VALUATION_PRICE_TTL_S - 0.5
    b.get_positions()
    assert ex.fetch_tickers.call_count == 1
    t[0] += 1.0  # now beyond TTL
    b.get_positions()
    assert ex.fetch_tickers.call_count == 2


def test_failed_batch_after_ttl_never_serves_stale(monkeypatch):
    ex = _ex()
    b = _broker(monkeypatch, ex)
    t = [1000.0]
    monkeypatch.setattr(bmod.time, "monotonic", lambda: t[0])
    b.get_account_balance()
    t[0] += bmod.VALUATION_PRICE_TTL_S + 1
    ex.fetch_tickers.side_effect = RuntimeError("down")
    ex.fetch_ticker.side_effect = RuntimeError("down")
    with pytest.raises(BalanceUnavailableError):
        b.get_account_balance()


def test_market_price_and_order_not_from_cache(monkeypatch):
    ex = _ex()
    b = _broker(monkeypatch, ex)
    b.get_account_balance()  # fills valuation cache
    PRICES_NEW = {"BTC/USDT": 51_000.0}
    ex.fetch_ticker.side_effect = lambda pair: {"last": PRICES_NEW[pair]}
    assert b.get_market_price("BTC/USDT") == 51_000.0
    assert ex.fetch_ticker.call_count == 1
    ex.create_order.return_value = {"id": "1", "status": "closed", "filled": 0.01, "amount": 0.01, "average": 51_000.0}
    b.place_order("BTC/USDT", OrderSide.BUY, OrderType.MARKET, 0.01, client_order_id="af-c1")
    assert ex.fetch_ticker.call_count == 1  # place_order does not use valuation prices


# ── PaperBroker ───────────────────────────────────────────────────────────────

def _paper(monkeypatch, price):
    monkeypatch.setattr(pmod, "fetch_current_price", lambda s: price if not callable(price) else price(s))
    pb = PaperBroker()
    pb._positions = {"BTCUSDT": 0.5}
    return pb


def test_paper_unknown_entry_is_none(monkeypatch):
    ps = _paper(monkeypatch, 50_000.0).get_positions()
    assert ps[0].avg_entry_price is None and ps[0].current_price == 50_000.0
    assert ps[0].unrealized_pnl is None and ps[0].unrealized_pnl_pct is None


def test_paper_known_entry_pnl(monkeypatch):
    pb = _paper(monkeypatch, 50_000.0)
    pb._avg_entry = {"BTCUSDT": 40_000.0}
    p = pb.get_positions()[0]
    assert p.avg_entry_price == 40_000.0 and p.unrealized_pnl == pytest.approx(5_000.0)


def _boom(_s):
    raise RuntimeError("no data")


@pytest.mark.parametrize("price", [0.0, None, float("nan"), -1.0, _boom])
def test_paper_invalid_price_raises(monkeypatch, price):
    with pytest.raises(MarketPriceUnavailableError):
        _paper(monkeypatch, price).get_positions()
