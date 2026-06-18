"""scripts/run_backtest.py — ATOM-STEP-8: Backtest Runner"""
from __future__ import annotations

import random
import sys
from datetime import datetime, timedelta

sys.path.insert(0, ".")
from core.council.runner import run_council
from trading.backtester import BacktestConfig, Backtester


def generate_synthetic_data(symbol, days=30, base_price=50000.0):
    random.seed(42)
    prices = []
    dt = datetime(2026, 3, 1)
    p = base_price
    for _ in range(days):
        change = random.gauss(0, 0.02) * p
        p = max(p + change, p * 0.5)
        prices.append((dt, round(p, 2)))
        dt += timedelta(days=1)
    return prices


def generate_signals(symbol, prices):
    random.seed(99)
    signals = []
    for i, (dt, price) in enumerate(prices):
        if i < 5:
            continue
        # Bias LONG when price below fair value, SHORT when above
        fair = price * 1.02
        pred_ret = (fair - price) / price
        rsi = 40.0 if price < fair else 60.0
        macd_bullish = price < fair
        result = run_council(
            symbol=symbol,
            price=price,
            fair_value=fair,
            predicted_return=pred_ret,
            uncertainty=0.05,
            rsi=rsi,
            macd_bullish=macd_bullish,
        )
        signal = result.final_signal.name
        confidence = int(result.confidence)
        signals.append(
            {
                "timestamp": dt,
                "symbol": symbol,
                "signal": signal,
                "confidence": confidence,
                "reasoning": result.deliberation[:80],
            }
        )
    return signals


def main():
    print("=" * 60)
    print("  ASTROFIN BACKTEST RUNNER — ATOM-STEP-8")
    print("=" * 60)
    print()
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    base_prices = [50000.0, 3000.0, 100.0]
    all_results = []
    for symbol, base in zip(symbols, base_prices, strict=False):
        prices = generate_synthetic_data(symbol, days=30, base_price=base)
        lo, hi = min(p for _, p in prices), max(p for _, p in prices)
        print("[%s] %d bars, $%.2f-$%.2f" % (symbol, len(prices), lo, hi))
        signals = generate_signals(symbol, prices)
        sc = {}
        for s in signals:
            sc[s["signal"]] = sc.get(s["signal"], 0) + 1
        print("[%s] %d signals: %s" % (symbol, len(signals), sc))
        prices_dict = {symbol: prices}
        config = BacktestConfig(
            initial_capital=10000.0,
            risk_per_trade_pct=2.0,
            stop_loss_pct=2.0,
            take_profit_pct=4.0,
        )
        bt = Backtester(config)
        result = bt.run(signals, prices_dict)
        result.print_summary()
        if result.trades:
            print(
                "  First trade:",
                result.trades[0].symbol,
                result.trades[0].side,
                "pnl=%+.2f%%" % result.trades[0].pnl_pct,
            )
        print()
        all_results.append(result)
    total_return = sum(r.portfolio_summary["total_return_pct"] for r in all_results)
    print("=" * 60)
    print("  PORTFOLIO SUMMARY")
    print("=" * 60)
    print("  Symbols: %s" % ", ".join(symbols))
    print("  Combined Return: %+.2f%%" % total_return)
    print("=" * 60)


if __name__ == "__main__":
    main()
