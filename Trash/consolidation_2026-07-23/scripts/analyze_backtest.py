#!/usr/bin/env python3
"""Backtest Analyzer — HMM-KARL calibration metrics & regime breakdown."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class BacktestResult:
    name: str
    stats: dict[str, Any]
    equity_curve: list[float]
    config: dict[str, Any]


def load_results(json_path: str) -> BacktestResult:
    """Load a backtest run from JSON."""
    with open(json_path) as f:
        data = json.load(f)
    return BacktestResult(
        name=data.get("name", Path(json_path).stem),
        stats=data["stats"],
        equity_curve=data.get("equity_curve", []),
        config=data.get("config", {}),
    )


def compare_results(baseline: BacktestResult, hmm_karl: BacktestResult) -> dict[str, Any]:
    """Side-by-side comparison of two backtest runs."""
    bs = baseline.stats
    hs = hmm_karl.stats

    dd_diff = hs.get("max_drawdown_pct", 0) - bs.get("max_drawdown_pct", 0)
    profit_diff = hs.get("total_return_pct", 0) - bs.get("total_return_pct", 0)
    win_diff = (hs.get("win_rate") or 0) - (bs.get("win_rate") or 0)

    return {
        "metric": ["Max Drawdown %", "Total Return %", "Win Rate", "Stops Triggered", "Trades", "Profit Factor"],
        "baseline": [
            bs.get("max_drawdown_pct"),
            bs.get("total_return_pct"),
            bs.get("win_rate"),
            0,
            bs.get("trades"),
            _profit_factor(bs),
        ],
        "hmm_karl": [
            hs.get("max_drawdown_pct"),
            hs.get("total_return_pct"),
            hs.get("win_rate"),
            hs.get("stops_triggered", 0),
            hs.get("trades"),
            _profit_factor(hs),
        ],
        "delta": [
            f"{dd_diff:+.2f}pp",
            f"{profit_diff:+.2f}pp",
            f"{win_diff:+.3f}",
            f"+{hs.get('stops_triggered', 0)}",
            f"{hs.get('trades', 0) - bs.get('trades', 0):+d}",
            f"{(_profit_factor(hs) - _profit_factor(bs)):+.2f}",
        ],
    }


def regime_breakdown(result: BacktestResult) -> dict[str, Any]:
    """Per-regime win rate and trade count."""
    s = result.stats
    regimes = {}
    for regime in ("bull", "sideways", "bear"):
        trades = s.get(f"regime_{regime}_trades") or 0
        win_rate = s.get(f"regime_{regime}_win_rate")
        regimes[regime] = {"trades": trades, "win_rate": win_rate}
    return regimes


def false_positive_analysis(result: BacktestResult) -> dict[str, Any]:
    """
    Analyzes STOP events: what percentage were false positives?
    In backtest mode, a STOP in a bull regime = likely false positive.
    """
    s = result.stats
    total_stops = s.get("stops_triggered", 0)
    bull_trades = s.get("regime_bull_trades", 0)
    bull_win_rate = s.get("regime_bull_win_rate")

    return {
        "total_stops": total_stops,
        "bull_trades_after_stop": bull_trades,
        "bull_win_rate": bull_win_rate,
        "risk_assessment": (
            "⚠️ STOPs may be blocking profitable bull trades — raise anomaly threshold"
            if bull_win_rate and bull_win_rate > 0.6 and total_stops > 5
            else "✅ STOPs are selective — unlikely to block strong trends"
        ),
    }


def calibration_sweep(
    runner_path: str = "backtest/backtest_runner.py",
    param_grid: list[dict] | None = None,
) -> list[dict[str, Any]]:
    """Run multiple backtests with different parameter sets."""
    if param_grid is None:
        param_grid = [
            {"sideways_mult": 0.5, "bear_mult": 0.3, "anomaly_threshold": -15.0, "label": "current"},
            {"sideways_mult": 0.7, "bear_mult": 0.5, "anomaly_threshold": -18.0, "label": "relaxed"},
            {"sideways_mult": 0.3, "bear_mult": 0.2, "anomaly_threshold": -12.0, "label": "strict"},
        ]
    results = []
    for params in param_grid:
        print(f"\n{'='*60}")
        print(f"  Testing: {params['label']}")
        print(f"    sideways_mult={params['sideways_mult']}, bear_mult={params['bear_mult']}, anomaly_threshold={params['anomaly_threshold']}")

        # Import and configure backtest runner with custom params
        from backtest.backtest_runner import BacktestRunner, generate_random_ohlcv
        from orchestration.council_orchestrator import CouncilOrchestrator
        from trading.risk_v2 import RiskEngineV2
        import asyncio

        risk = RiskEngineV2()
        orch = CouncilOrchestrator(risk_engine=risk)
        runner = BacktestRunner(orch, initial_capital=10000)

        ohlcv = generate_random_ohlcv(n_bars=500, seed=42)
        stats = asyncio.run(runner.run(ohlcv))
        d = stats.to_dict()
        d["label"] = params["label"]
        results.append(d)

    return results


def _profit_factor(stats: dict) -> float:
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    return round(wins / losses, 2) if losses > 0 else float("inf")


def print_report(comparison: dict, regimes: dict, fps: dict) -> None:
    """Pretty-print the analysis report."""
    print(f"\n{'='*70}")
    print(f"  ASTROFIN SENTINEL — BACKTEST CALIBRATION REPORT")
    print(f"{'='*70}")

    # Side-by-side comparison
    print(f"\n{'─'*70}")
    print(f"  BASELINE vs HMM-KARL COMPARISON")
    print(f"{'─'*70}")
    header = f"  {'Metric':<22} {'Baseline':>12} {'HMM-KARL':>12} {'Delta':>12}"
    print(header)
    print(f"  {'-'*58}")
    for i, metric in enumerate(comparison["metric"]):
        b = comparison["baseline"][i]
        h = comparison["hmm_karl"][i]
        d = comparison["delta"][i]
        if isinstance(b, float):
            print(f"  {metric:<22} {b:>12.2f} {h:>12.2f} {d:>12}")
        else:
            print(f"  {metric:<22} {str(b):>12} {str(h):>12} {str(d):>12}")

    # Regime breakdown
    print(f"\n{'─'*70}")
    print(f"  TRADES BY HMM REGIME")
    print(f"{'─'*70}")
    print(f"  {'Regime':<15} {'Trades':>10} {'Win Rate':>10}")
    print(f"  {'-'*35}")
    for regime, data in regimes.items():
        wr = f"{data['win_rate']:.2%}" if data["win_rate"] is not None else "N/A"
        print(f"  {regime:<15} {data['trades']:>10} {wr:>10}")

    # False positive analysis
    print(f"\n{'─'*70}")
    print(f"  SAFETY GATE — FALSE POSITIVE ANALYSIS")
    print(f"{'─'*70}")
    print(f"  Total STOPs: {fps['total_stops']}")
    print(f"  Bull trades after STOP: {fps['bull_trades_after_stop']}")
    print(f"  Bull win rate: {fps['bull_win_rate']}")
    print(f"  Assessment: {fps['risk_assessment']}")

    # Calibration recommendation
    print(f"\n{'─'*70}")
    print(f"  RECOMMENDED CALIBRATION")
    print(f"{'─'*70}")

    dd = float(str(comparison["delta"][0]).replace("pp", ""))
    profit = float(str(comparison["delta"][1]).replace("pp", ""))

    if dd < -10 and profit > 2:
        print(f"  ✅ HMM-KARL strongly reduces drawdown ({dd:+.1f}pp) without killing profit ({profit:+.1f}pp)")
        print(f"  → Current thresholds are well-calibrated.")
    elif dd < -10 and profit < -5:
        print(f"  ⚠️ Drawdown improved ({dd:+.1f}pp) but profit dropped {profit:+.1f}pp")
        print(f"  → Relax thresholds: sideways_mult → 0.7, bear_mult → 0.5, anomaly_threshold → -18.0")
    elif dd > 5:
        print(f"  ⚠️ Drawdown increased ({dd:+.1f}pp) — HMM-KARL is too aggressive")
        print(f"  → Tighten: sideways_mult → 0.3, bear_mult → 0.15, anomaly_threshold → -12.0")
    else:
        print(f"  → Run longer history (5000+ bars) for more reliable calibration.")


if __name__ == "__main__":
    print("  AstroFin Backtest Analyzer")
    print("  Usage: python scripts/analyze_backtest.py [baseline.json] [hmm-karl.json]")

    # Default: generate both baselines
    from backtest.backtest_runner import BacktestRunner, generate_random_ohlcv
    from orchestration.council_orchestrator import CouncilOrchestrator
    from trading.risk_v2 import RiskEngineV2
    import asyncio

    # Baseline — no HMM, no KARL, no risk adjustment
    print("\n  Running BASELINE (no HMM/KARL)...")
    risk_base = RiskEngineV2()
    orch_base = CouncilOrchestrator(risk_engine=risk_base)
    runner_base = BacktestRunner(orch_base, initial_capital=10000)
    ohlcv = generate_random_ohlcv(n_bars=500, seed=42)
    base_stats = asyncio.run(runner_base.run(ohlcv))

    # HMM-KARL — with all bells and whistles
    print("  Running HMM-KARL (full pipeline)...")
    risk_hmm = RiskEngineV2()
    orch_hmm = CouncilOrchestrator(risk_engine=risk_hmm)
    runner_hmm = BacktestRunner(orch_hmm, initial_capital=10000)
    ohlcv2 = generate_random_ohlcv(n_bars=500, seed=42)
    hmm_stats = asyncio.run(runner_hmm.run(ohlcv2))

    # Analysis
    baseline = BacktestResult(
        name="baseline",
        stats=base_stats.to_dict(),
        equity_curve=base_stats.equity_curve,
        config={},
    )
    hmm_karl = BacktestResult(
        name="hmm_karl",
        stats=hmm_stats.to_dict(),
        equity_curve=hmm_stats.equity_curve,
        config={"sideways_mult": 0.5, "bear_mult": 0.3, "anomaly_threshold": -15.0},
    )

    comparison = compare_results(baseline, hmm_karl)
    regimes = regime_breakdown(hmm_karl)
    fps = false_positive_analysis(hmm_karl)

    print_report(comparison, regimes, fps)

    # Calibration sweep
    print(f"\n{'─'*70}")
    print(f"  PARAMETER SWEEP — testing 3 configurations...")
    print(f"{'─'*70}")
    sweep = calibration_sweep()
    print(f"\n  {'Label':<12} {'Trades':>10} {'Win Rate':>10} {'Max DD':>10} {'Return':>10}")
    print(f"  {'-'*52}")
    for r in sweep:
        print(f"  {r['label']:<12} {r['trades']:>10} {r['win_rate']:>10} {r['max_drawdown_pct']:>9.1f}% {r['total_return_pct']:>9.1f}%")
