#!/usr/bin/env python3
"""
scripts/optimize_lag_blend.py — ATOM-KARL-015 Phase 5: Blend Optimization

Экспериментальный подбор оптимального blend для mature-фазы LagWindow.

Usage:
    # Demo (synthetic data)
    python scripts/optimize_lag_blend.py --demo

    # Real CSV data
    python scripts/optimize_lag_blend.py \
        --data data/confidence_logs.csv \
        --metric reversals \
        --window 50 \
        --blend-min 0.10 --blend-max 0.20 --blend-step 0.01 \
        --output logs/blend_results.json \
        --plot

    # With .env update
    python scripts/optimize_lag_blend.py --data data/logs.csv --update-env
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents._impl.amre.lag_windowing import LagWindow

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("optimize_blend")


# ─── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_WINDOW_SIZE = 50
BLEND_MIN = 0.10
BLEND_MAX = 0.20
BLEND_STEP = 0.01
WARMUP_THRESHOLD = 20  # must match lag_windowing.py


# ─── Data Classes ─────────────────────────────────────────────────────────────


@dataclass
class BlendResult:
    blend: float
    reversals: int
    stability: float
    sharpe: float | None
    mae: float


# ─── Synthetic Data Generator ─────────────────────────────────────────────────


def generate_demo_data(n: int = 500, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic confidence data for testing.

    Creates a random walk around 50, with artificial reversals
    to make the optimization task meaningful.
    """
    np.random.seed(seed)

    # Raw confidence: random walk centered at 50
    raw = 50 + np.cumsum(np.random.normal(0, 2.5, n))
    raw = np.clip(raw, 0, 100).astype(int)

    # True direction: depends on whether price moved up or down
    # Simulate price as random walk with momentum
    price = 100 + np.cumsum(np.random.normal(0, 0.3, n + 1))
    returns = np.diff(price)
    true_direction = np.sign(returns).astype(int)

    # PnL: if we open position at signal and close N bars later
    # Position is determined by raw confidence at bar i
    position_signal = np.where(raw >= 55, 1, np.where(raw <= 45, -1, 0))
    # returns has n elements, position_signal has n elements, align them
    pnl = position_signal * returns[: len(position_signal)]

    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=n, freq="5min"),
            "raw_confidence": raw,
            "true_direction": true_direction,
            "pnl": pnl,
        }
    )

    logger.info(
        f"[Demo] Generated {n} rows, reversals in raw: {sum(np.abs(np.diff(np.sign(raw - 50))) > 0)}"
    )

    return df


def load_data(path: str) -> pd.DataFrame:
    """Load CSV with required columns."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")

    df = pd.read_csv(path)
    required = {"timestamp", "raw_confidence"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required columns: {missing}. Found: {list(df.columns)}"
        )

    if len(df) < 50:
        logger.warning(f"Only {len(df)} rows — statistics may be unreliable.")

    # Ensure types
    df["raw_confidence"] = df["raw_confidence"].astype(int)

    logger.info(f"[Data] Loaded {len(df)} rows from {path}")
    return df


# ─── Metrics Computation ───────────────────────────────────────────────────────


def compute_reversals(adjusted: list[float]) -> int:
    """
    Count sign reversals relative to neutral level 50.

    A reversal is when (adj[i] - 50) and (adj[i-1] - 50) have opposite signs.
    """
    reversals = 0
    prev_diff = None
    for val in adjusted:
        diff = val - 50
        if prev_diff is not None:
            if (diff > 0) != (prev_diff > 0) and diff != 0 and prev_diff != 0:
                reversals += 1
        prev_diff = diff
    return reversals


def compute_stability(adjusted: list[float]) -> float:
    """
    Compute stability score = -std(diff), where diff = adj[i] - adj[i-1].

    Higher (less negative) = more stable.
    """
    if len(adjusted) < 2:
        return 0.0
    arr = np.array(adjusted)
    diffs = np.diff(arr)
    return -float(np.std(diffs))


def compute_sharpe(df: pd.DataFrame, adjusted: list[float]) -> float | None:
    """
    Compute Sharpe ratio if PnL column is available.

    Position: adj > 60 → LONG (+1), adj < 40 → SHORT (-1), else FLAT (0).
    """
    if "pnl" not in df.columns:
        return None

    adj = np.array(adjusted[: len(df)])
    pos_signal = np.where(adj > 60, 1, np.where(adj < 40, -1, 0))
    pnl_arr = df["pnl"].values[: len(pos_signal)]

    # Align lengths
    min_len = min(len(pos_signal), len(pnl_arr))
    pos_signal = pos_signal[:min_len]
    pnl_arr = pnl_arr[:min_len]

    strategy_returns = pos_signal * pnl_arr
    mean_ret = np.mean(strategy_returns)
    std_ret = np.std(strategy_returns)

    if std_ret == 0:
        return None

    sharpe = mean_ret / std_ret * np.sqrt(252 * 78)  # 5-min bars, annualized
    return round(sharpe, 4)


def compute_mae(raw_list: list[int], adjusted: list[float]) -> float:
    """Mean Absolute Error between raw and adjusted."""
    arr = np.array(adjusted[: len(raw_list)])
    raw_arr = np.array(raw_list)
    return round(float(np.mean(np.abs(arr - raw_arr))), 4)


# ─── Core Evaluation ───────────────────────────────────────────────────────────


def evaluate_blend(
    blend: float,
    df: pd.DataFrame,
    window_size: int = DEFAULT_WINDOW_SIZE,
    adaptive_enabled: bool = False,
) -> tuple[int, float, float | None, float]:
    """
    Simulate LagWindow with a fixed blend value and compute metrics.

    Returns: (reversals, stability, sharpe, mae)
    """
    # Patch the module constant for this evaluation
    import agents._impl.amre.lag_windowing as lw_module

    original_mature = lw_module.BLEND_MATURE
    lw_module.BLEND_MATURE = blend

    try:
        window = LagWindow(
            base_window_size=window_size,
            adaptive_window_enabled=adaptive_enabled,
        )
        # Override the instance blend (the class uses a module-level constant in add())
        # We need to patch at class level

        adjusted_list = []
        raw_list = df["raw_confidence"].tolist()

        for raw in raw_list:
            result = window.add(confidence=raw, volatility=None)
            adjusted_list.append(result["final_confidence"])

    finally:
        lw_module.BLEND_MATURE = original_mature

    reversals = compute_reversals(adjusted_list)
    stability = compute_stability(adjusted_list)
    sharpe = compute_sharpe(df, adjusted_list)
    mae = compute_mae(raw_list, adjusted_list)

    return reversals, stability, sharpe, mae


def run_optimization(
    df: pd.DataFrame,
    metric: str,
    window_size: int,
    blend_min: float,
    blend_max: float,
    blend_step: float,
) -> tuple[list[BlendResult], BlendResult]:
    """
    Grid-search over blend values and find the optimal one.
    """
    blend_values = np.arange(blend_min, blend_max + blend_step / 2, blend_step)
    blend_values = np.round(blend_values, 2)

    results: list[BlendResult] = []

    for blend in blend_values:
        reversals, stability, sharpe, mae = evaluate_blend(
            blend=blend,
            df=df,
            window_size=window_size,
            adaptive_enabled=False,
        )
        results.append(
            BlendResult(
                blend=round(blend, 2),
                reversals=reversals,
                stability=stability,
                sharpe=sharpe,
                mae=mae,
            )
        )

    # Select optimal
    if metric == "reversals":
        best = min(results, key=lambda r: r.reversals)
    elif metric == "stability":
        best = max(results, key=lambda r: r.stability)
    elif metric == "sharpe":
        # Filter out None sharpe values
        valid = [r for r in results if r.sharpe is not None]
        if not valid:
            raise ValueError("Cannot optimize 'sharpe': PnL column missing or invalid.")
        best = max(valid, key=lambda r: r.sharpe)
    else:
        raise ValueError(
            f"Unknown metric: {metric}. Use: reversals, stability, sharpe."
        )

    return results, best


# ─── Output ────────────────────────────────────────────────────────────────────


def print_table(results: list[BlendResult], best: BlendResult, metric: str):
    """Print ASCII table to console."""
    has_sharpe = any(r.sharpe is not None for r in results)

    header = f"{'Blend':>6}  {'Reversals':>10}  {'Stability':>10}"
    if has_sharpe:
        header += f"  {'Sharpe':>10}"
    header += f"  {'MAE':>8}"
    separator = "-" * len(header)

    logger.info(f"\n{'=' * 60}")
    logger.info(f"Metric optimized: {metric.upper()}")
    logger.info(f"{'=' * 60}")
    logger.info(header)
    logger.info(separator)

    for r in results:
        row = f"{r.blend:>6.2f}  {r.reversals:>10}  {r.stability:>10.4f}"
        if has_sharpe:
            row += f"  {str(r.sharpe) if r.sharpe is not None else 'N/A':>10}"
        row += f"  {r.mae:>8.4f}"
        logger.info(row)

    logger.info(separator)
    marker = ">>>" if metric != "stability" else "<<<"
    best_row = f"{best.blend:>6.2f}  {best.reversals:>10}  {best.stability:>10.4f}"
    if best.sharpe is not None:
        best_row += f"  {best.sharpe:>10.4f}"
    best_row += f"  {best.mae:>8.4f}"
    logger.info(f"{marker} Optimal: {best_row}")
    logger.info("")


def save_json(
    results: list[BlendResult],
    best: BlendResult,
    metric: str,
    window_size: int,
    output_path: str,
):
    """Save results to JSON file."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    data = {
        "metric": metric,
        "window_size": window_size,
        "best_blend": best.blend,
        "best_value": (
            best.reversals
            if metric == "reversals"
            else best.stability if metric == "stability" else best.sharpe
        ),
        "results": [asdict(r) for r in results],
    }

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved: {output_path}")


def plot_results(
    results: list[BlendResult], best: BlendResult, metric: str, output_path: str
):
    """Plot metric vs blend and save as PNG."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib not installed — skipping plot.")
        return

    blends = [r.blend for r in results]
    if metric == "reversals":
        values = [r.reversals for r in results]
        label = "Reversals (lower is better)"
        best_val = best.reversals
    elif metric == "stability":
        values = [r.stability for r in results]
        label = "Stability (higher is better)"
        best_val = best.stability
    else:
        values = [r.sharpe for r in results if r.sharpe is not None]
        label = "Sharpe Ratio (higher is better)"
        best_val = best.sharpe

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(blends[: len(values)], values, "b-o", linewidth=2, markersize=5)
    ax.axvline(
        x=best.blend, color="r", linestyle="--", label=f"Optimal blend={best.blend:.2f}"
    )
    ax.scatter(
        [best.blend],
        [best_val],
        color="red",
        s=120,
        zorder=5,
        label=f"{label}={best_val}",
    )

    ax.set_xlabel("Blend (mature phase)")
    ax.set_ylabel(label)
    ax.set_title(f"LagWindow Blend Optimization — {label}")
    ax.grid(True, alpha=0.3)
    ax.legend()

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved plot: {output_path}")


# ─── CLI ──────────────────────────────────────────────────────────────────────


def parse_args():
    parser = argparse.ArgumentParser(
        description="Optimize LagWindow blend_mature parameter.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--data",
        type=str,
        default=None,
        help="Path to CSV file with columns: timestamp, raw_confidence, true_direction, pnl (optional).",
    )
    parser.add_argument(
        "--demo", action="store_true", help="Use synthetic demo data (500 rows)."
    )
    parser.add_argument(
        "--metric",
        type=str,
        default="reversals",
        choices=["reversals", "stability", "sharpe"],
        help="Metric to optimize. Default: reversals.",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=DEFAULT_WINDOW_SIZE,
        help=f"LagWindow base window size. Default: {DEFAULT_WINDOW_SIZE}.",
    )
    parser.add_argument(
        "--blend-min",
        type=float,
        default=BLEND_MIN,
        help=f"Minimum blend value. Default: {BLEND_MIN}.",
    )
    parser.add_argument(
        "--blend-max",
        type=float,
        default=BLEND_MAX,
        help=f"Maximum blend value. Default: {BLEND_MAX}.",
    )
    parser.add_argument(
        "--blend-step",
        type=float,
        default=BLEND_STEP,
        help=f"Blend step size. Default: {BLEND_STEP}.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="logs/blend_results.json",
        help="Output JSON path. Default: logs/blend_results.json",
    )
    parser.add_argument(
        "--plot", action="store_true", help="Generate and save PNG plot."
    )
    parser.add_argument(
        "--update-env",
        action="store_true",
        help="Print LAG_BLEND_MATURE=<value> to stdout for .env update.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Load or generate data
    if args.demo:
        df = generate_demo_data(n=500, seed=42)
        data_label = "demo (synthetic)"
    elif args.data:
        df = load_data(args.data)
        data_label = args.data
    else:
        logger.info("Error: specify --data <path.csv> or --demo")
        logger.info(__doc__)
        sys.exit(1)

    logger.info(
        f"[Run] metric={args.metric}, window={args.window}, blend=[{args.blend_min}, {args.blend_max}] step={args.blend_step}, data={data_label}"
    )

    results, best = run_optimization(
        df=df,
        metric=args.metric,
        window_size=args.window,
        blend_min=args.blend_min,
        blend_max=args.blend_max,
        blend_step=args.blend_step,
    )

    print_table(results, best, args.metric)

    save_json(results, best, args.metric, args.window, args.output)

    if args.plot:
        plot_path = args.output.replace(".json", ".png")
        plot_results(results, best, args.metric, plot_path)

    if args.update_env:
        logger.info("\n# Add to .env:")
        logger.info(f"LAG_BLEND_MATURE={best.blend}")

    # Summary
    metric_key = args.metric
    best_val = (
        best.reversals
        if args.metric == "reversals"
        else best.stability if args.metric == "stability" else best.sharpe
    )
    logger.info(
        f"Optimal blend for metric '{args.metric}': {best.blend} ({metric_key}={best_val})"
    )


if __name__ == "__main__":
    main()
