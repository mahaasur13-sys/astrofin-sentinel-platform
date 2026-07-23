#!/usr/bin/env python3
"""Self-contained BTC calibration with RegimeDetector + production pipeline."""
from __future__ import annotations
import os

import sys, os, json, asyncio, logging
sys.path.insert(0, "/home/workspace")

logging.basicConfig(level=logging.WARNING, format="%(message)s")
logger = logging.getLogger("calibrate")
logger.setLevel(logging.INFO)

from backtest.backtest_runner import BacktestRunner, BacktestStats, generate_random_ohlcv
from backtest.regime_detector import RegimeDetector
from orchestration.council_orchestrator import CouncilOrchestrator
from trading.risk_v2 import RiskEngineV2

CACHE = "/home/workspace/astrofin-sentinel-platform/backtest/data_cache/btc_coingecko_365d.jsonl"

def load_ohlcv(path: str) -> list[dict]:
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]

async def run_sweep(label: str, sideways_mult: float, bear_mult: float, anomaly_threshold: float) -> dict:
    """Run one calibration pass."""
    ohlcv = load_ohlcv(CACHE) if os.path.exists(CACHE) else generate_random_ohlcv(500, seed=42)
    n = len(ohlcv)
    detector = RegimeDetector(lookback=120)
    detector.fit(ohlcv)
    
    risk = RiskEngineV2()
    risk.sideways_mult = sideways_mult
    risk.bear_mult = bear_mult
    risk.anomaly_threshold = anomaly_threshold
    
    orch = CouncilOrchestrator(risk_engine=risk)
    runner = BacktestRunner(orch, initial_capital=10000)
    stats = await runner.run(ohlcv, regime_detector=detector)
    
    d = stats.to_dict()
    d["label"] = label
    d["sideways_mult"] = sideways_mult
    d["bear_mult"] = bear_mult
    d["anomaly_threshold"] = anomaly_threshold
    return d

async def main():
    param_grid = [
        ("current",  0.5, 0.3, -15.0),
        ("relaxed",  0.7, 0.5, -18.0),
        ("strict",   0.3, 0.1, -12.0),
    ]
    results = []
    for label, sm, bm, ath in param_grid:
        logger.info(f"Calibrating: {label} (sideways={sm}, bear={bm}, anomaly={ath})")
        d = await run_sweep(label, sm, bm, ath)
        results.append(d)
    
    # Print table
    header = f"{'Config':<12} {'Trades':>8} {'WinRate':>8} {'MaxDD':>8} {'Return':>8} {'PF':>8}"
    print("=" * 70)
    print(header)
    print("-" * 70)
    pf = lambda d: round(d["wins"]/d["losses"],2) if d.get("losses",0) > 0 else float("inf")
    for r in results:
        wr = r['win_rate'] * 100
        print(f"{r['label']:<12} {r['trades']:>8} {wr:>7.1f}% {r['max_drawdown_pct']:>7.1f}% {r['total_return_pct']:>7.1f}% {pf(r):>8.2f}")
    
    # Pick best by return
    best = max(results, key=lambda r: r["total_return_pct"])
    print(f"\nBest config: {best['label']} (return={best['total_return_pct']:.1f}%)")
    
    # Save report
    report_path = "/home/workspace/astrofin-sentinel-platform/backtest/data_cache/CALIBRATION_REPORT.md"
    with open(report_path, "w") as f:
        f.write(f"# HMM-KARL Calibration Report\n\n")
        f.write(f"| Config | Trades | WinRate | MaxDD | Return | PF |\n")
        f.write(f"|--------|--------|---------|-------|--------|----|\n")
        for r in results:
            f.write(f"| {r['label']} | {r['trades']} | {r["win_rate"]*100:.1f}% | {r['max_drawdown_pct']:.1f}% | {r['total_return_pct']:.1f}% | {pf(r):.2f} |\n")
        f.write(f"\n**Recommended:** `{best['label']}` (sideways_mult={best['sideways_mult']}, bear_mult={best['bear_mult']}, anomaly_threshold={best['anomaly_threshold']})\n")
    
    print(f"\nReport saved: {report_path}")

asyncio.run(main())
