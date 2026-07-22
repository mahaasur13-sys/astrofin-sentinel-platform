#!/usr/bin/env python3
"""Sprint 7-8: Vedic Backtest Runner — synthetic 6-month BTC backtest.

Usage:
    cd /home/workspace/astrofin-sentinel-platform
    source venv/bin/activate
    PYTHONPATH=. python tools/run_vedic_backtest.py              # 90-day default
    PYTHONPATH=. python tools/run_vedic_backtest.py --days 180   # 6 months
    PYTHONPATH=. python tools/run_vedic_backtest.py --min-muhurta 70
"""

import argparse, random, sys
from datetime import datetime, timedelta, timezone

def main():
    p = argparse.ArgumentParser(description="Vedic Backtest Runner")
    p.add_argument("--days", type=int, default=90)
    p.add_argument("--symbol", default="BTCUSDT")
    p.add_argument("--base-price", type=float, default=50000.0)
    p.add_argument("--min-muhurta", type=int, default=50)
    p.add_argument("--exclude-dangerous", action="store_true", default=True)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    random.seed(args.seed)

    from trading.backtester import BacktestConfig, Backtester
    from backtest.vedic_backtest import annotate_trade, vedic_filter, VedicPerformanceMatrix

    TZ = timezone(timedelta(hours=4))
    start = datetime(2026, 1, 19, 6, 0, tzinfo=TZ)
    SYM = args.symbol

    print("=" * 72)
    print(f"  VEDIC BACKTEST — {SYM} {args.days}d @ ${args.base_price:,.0f}")
    print(f"  Filter: Muhurta ≥ {args.min_muhurta}, exclude_dangerous={args.exclude_dangerous}, seed={args.seed}")
    print("=" * 72)

    prices_raw, signals_raw = [], []
    p_price = args.base_price
    for i in range(args.days):
        dt = start + timedelta(days=i)
        ret = random.gauss(0.0003, 0.025) + random.gauss(0.0002, 0.03)
        p_price = max(p_price * (1 + ret), p_price * 0.5)
        prices_raw.append((dt, round(p_price, 2)))
        if i >= 3:
            r = random.random()
            sig = "LONG" if r < 0.35 else ("SHORT" if r < 0.60 else "NEUTRAL")
            signals_raw.append({"timestamp": dt, "symbol": SYM, "signal": sig,
                                "confidence": random.randint(45, 95)})

    prices = {SYM: prices_raw}
    config = BacktestConfig(initial_capital=10000.0, risk_per_trade_pct=2.0,
                            stop_loss_pct=5.0, take_profit_pct=10.0)

    # ALL (unfiltered)
    bt = Backtester(config)
    all_sigs = [s for s in signals_raw if s["signal"] != "NEUTRAL"]
    res_all = bt.run(all_sigs, prices)
    print(f"\n  UNFILTERED: {len(res_all.trades)} trades")

    # VEDIC-filtered
    filtered = vedic_filter(res_all.trades, min_muhurta=args.min_muhurta,
                            exclude_dangerous=args.exclude_dangerous)
    print(f"  VEDIC (≥{args.min_muhurta} Muhurta): {len(filtered)} passed")

    # Nakshatra Matrix
    matrix = VedicPerformanceMatrix()
    for t in res_all.trades:
        try:
            vt = annotate_trade(t, t.entry_time)
            matrix.add_trade(vt)
        except Exception:
            pass

    print()
    print(matrix.summary())

    # Comparison
    def stats(label, trades):
        if not trades:
            return f"  {label}: 0 trades"
        wins = sum(1 for t in trades if t.pnl_pct > 0)
        pnl = sum(t.pnl_pct for t in trades)
        wr = wins / len(trades) * 100
        avg = pnl / len(trades)
        return (f"  {label:30s} {len(trades):4d} trades  "
                f"W:{wr:5.1f}%  Avg:{avg*100:+6.2f}%  Σ:{pnl*100:+7.2f}%")

    print("\n📊 COMPARISON:")
    print(stats("ALL (unfiltered)", res_all.trades))
    vedic_trades = [t for t in res_all.trades if t in filtered]
    print(stats("VEDIC (≥70 Muhurta)", vedic_trades))

    if matrix.best_nakshatra():
        print(f"\n  🏆 Best Nakshatra:  {matrix.best_nakshatra()}")
    if matrix.worst_nakshatra():
        print(f"  📉 Worst Nakshatra: {matrix.worst_nakshatra()}")
    print()

if __name__ == "__main__":
    main()
