#!/usr/bin/env python3
"""Sprint 7: Vedic Backtest Runner.

Usage:
    cd /home/workspace/astrofin-sentinel-platform
    source venv/bin/activate
    python tools/run_vedic_backtest.py                    # synthetic 60-day BTC
    python tools/run_vedic_backtest.py --days 90 --symbol ETHUSDT
    python tools/run_vedic_backtest.py --min-muhurta 70 --exclude-dangerous
"""

import argparse
import random
import sys
from datetime import datetime, timedelta

def main():
    parser = argparse.ArgumentParser(description="Vedic Backtest Runner")
    parser.add_argument("--days", type=int, default=60, help="Number of backtest days")
    parser.add_argument("--symbol", default="BTCUSDT", help="Trading symbol")
    parser.add_argument("--base-price", type=float, default=50000.0)
    parser.add_argument("--min-muhurta", type=int, default=50, help="Minimum Muhurta score")
    parser.add_argument("--exclude-dangerous", action="store_true", default=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    from trading.backtester import BacktestConfig, Backtester
    from backtest.vedic_backtest import (
        annotate_trade, vedic_filter, VedicPerformanceMatrix,
    )

    print("═" * 75)
    print(f"  VEDIC BACKTEST — {args.symbol} {args.days}d @ ${args.base_price:,.0f}")
    print(f"  Filter: min Muhurta ≥ {args.min_muhurta}, exclude dangerous: {args.exclude_dangerous}")
    print("═" * 75)

    # Generate synthetic price data
    dt = datetime(2026, 6, 1)
    prices = []
    p = args.base_price
    for i in range(args.days):
        change = random.gauss(0, 0.025) * p
        p = max(p + change, p * 0.3)
        prices.append((dt + timedelta(days=i), round(p, 2)))

    print(f"\n  Generated {len(prices)} daily candles")

    # Generate synthetic signals (alternating LONG/SHORT with random conf)
    signals = []
    for i, (day_dt, price) in enumerate(prices):
        if i < 3:
            continue
        bias = random.choice(["LONG", "SHORT", "NEUTRAL"])
        conf = random.randint(30, 95)
        signals.append((day_dt, bias, conf, price))

    print(f"  Generated {len(signals)} synthetic signals\n")

    # Run standard backtest
    config = BacktestConfig(
        initial_capital=10000.0,
        risk_per_trade_pct=2.0,
        stop_loss_pct=5.0,
        take_profit_pct=10.0,
    )
    bt = Backtester(config)

    for day_dt, signal, conf, price in signals:
        if signal == "NEUTRAL":
            continue
        side = "LONG" if signal == "LONG" else "SHORT"
        bt.on_signal(args.symbol, side, price, day_dt, conf / 100.0 * config.risk_per_trade_pct)

    result = bt.finalize()
    all_trades = result.trades

    print(result.print_summary() if hasattr(result, 'print_summary') else f"  Total trades: {len(all_trades)}")

    # ── Vedic annotation ──
    vedic_trades = [annotate_trade(t, t.entry_time) for t in all_trades]
    print(f"\n  📿 Annotated {len(vedic_trades)} trades with Vedic metadata")

    # ── Vedic filter ──
    filtered = vedic_filter(all_trades, min_muhurta=args.min_muhurta, exclude_dangerous=args.exclude_dangerous)
    print(f"  🔍 Vedic filter: {len(filtered)}/{len(all_trades)} trades passed")

    # ── Performance matrix ──
    matrix = VedicPerformanceMatrix()
    for vt in vedic_trades:
        matrix.add_trade(vt)

    print()
    print(matrix.summary())

    # ── Compare: all vs Vedic-filtered ──
    if filtered and len(filtered) < len(all_trades):
        bt2 = Backtester(config)
        for day_dt, signal, conf, price in signals:
            if signal == "NEUTRAL":
                continue
            side = "LONG" if signal == "LONG" else "SHORT"
            bt2.on_signal(args.symbol, side, price, day_dt, conf / 100.0 * config.risk_per_trade_pct)
        result2 = bt2.finalize()
        # Re-filter
        result2.trades = [t for t in result2.trades if t in filtered]
        print(f"\n  📊 COMPARISON: All vs Vedic-filtered")
        print(f"     All trades: {len(all_trades)} | Filtered: {len(filtered)} ({(1-len(filtered)/max(len(all_trades),1))*100:.0f}% removed)")

    if matrix.best_nakshatra():
        print(f"\n  🏆 Best Nakshatra:  {matrix.best_nakshatra()}")
    if matrix.worst_nakshatra():
        print(f"  📉 Worst Nakshatra: {matrix.worst_nakshatra()}")


if __name__ == "__main__":
    main()
