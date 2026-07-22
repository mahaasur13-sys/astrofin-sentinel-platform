#!/usr/bin/env python3
"""AstroFin Sentinel — HMM Regime Dashboard Generator (Sprint 5).

Generates an interactive HTML dashboard showing:
  - Candlestick chart with HMM regime background coloring
  - Anomaly/STOP markers where RiskEngineV2 would block trades
  - Regime distribution pie chart
  - Monthly regime breakdown

Usage:
    python scripts/generate_hmm_dashboard.py [--data=cached|synthetic] [--output=hmm_dashboard.html]
"""

from __future__ import annotations

import pandas as pd
import argparse
import json
import logging
import os
import sys
from datetime import datetime

import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.WARNING, format="%(message)s")
logger = logging.getLogger(__name__)

# ─── Regime colors ──────────────────────────────────────────────────────────────
REGIME_COLORS = {
    "bull": "rgba(0, 200, 80, 0.12)",      # green
    "sideways": "rgba(128, 128, 128, 0.10)",  # gray
    "bear": "rgba(220, 40, 40, 0.12)",      # red
}


def load_cached_data(cache_path: str) -> list[dict]:
    """Load BTC data from JSONL cache."""
    with open(cache_path) as f:
        return [json.loads(line) for line in f if line.strip()]


def generate_synthetic_data(n_bars: int = 365) -> list[dict]:
    """Generate synthetic OHLCV for testing when cache is unavailable."""
    np.random.seed(42)
    prices = 50000 * np.cumprod(1 + np.random.randn(n_bars) * 0.01)
    return [
        {"close": float(prices[i]), "volume": 1000}
        for i in range(n_bars)
    ]


def detect_regimes(ohlcv: list[dict]) -> tuple[list[str], list[bool], list[float]]:
    """
    Run RegimeDetector HMM on the data.
    Returns (regime_labels, anomaly_flags, log_likelihoods).
    """
    from backtest.regime_detector import RegimeDetector

    detector = RegimeDetector(lookback=120)
    detector.fit(ohlcv)

    regimes = []
    anomalies = []
    log_liks = []

    for i in range(120, len(ohlcv)):
        label, probs, is_anomaly = detector.annotate(i)
        regimes.append(label)
        anomalies.append(is_anomaly)
        # reconstruct log_lik from internal state
        ll = detector._log_lik[i] if i < len(detector._log_lik) else 0.0
        log_liks.append(ll)

    # Pad beginning with sideways/no anomaly
    regimes = ["sideways"] * 120 + regimes
    anomalies = [False] * 120 + anomalies
    log_liks = [0.0] * 120 + log_liks

    return regimes, anomalies, log_liks


def generate_dashboard(
    ohlcv: list[dict],
    regimes: list[str],
    anomalies: list[bool],
    output_path: str = "hmm_dashboard.html",
    title: str = "AstroFin Sentinel — HMM Regime Dashboard",
) -> str:
    """
    Generate interactive Plotly HTML dashboard.
    Returns the absolute path to the output file.
    """
    n = min(len(ohlcv), len(regimes))
    ohlcv = ohlcv[:n]
    regimes = regimes[:n]
    anomalies = anomalies[:n]

    # Build timestamp index from cached data or synthetic
    timestamps = [
        datetime(2026, 7, 18) - pd.Timedelta(days=n - i)
        for i in range(n)
    ]

    closes = [b["close"] for b in ohlcv]
    highs = [b.get("high", c * 1.01) for b, c in zip(ohlcv, closes)]
    lows = [b.get("low", c * 0.99) for b, c in zip(ohlcv, closes)]
    opens = [b.get("open", c) for b, c in zip(ohlcv, closes)]
    volumes = [b.get("volume", 1000) for b in ohlcv]


    df = pd.DataFrame({
        "timestamp": timestamps,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
        "regime": regimes,
        "is_anomaly": anomalies,
    })

    # ── Build dashboard ──────────────────────────────────────────────────────
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.55, 0.25, 0.20],
        vertical_spacing=0.06,
        subplot_titles=(
            "BTC Price & HMM Regimes",
            "Anomaly / STOP Zones",
            "Volume",
        ),
    )

    # Row 1 — Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df["timestamp"],
            open=df["open"], high=df["high"], low=df["low"], close=df["close"],
            name="BTCUSDT",
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ),
        row=1, col=1,
    )

    # Row 1 — Regime background coloring
    for label, color in REGIME_COLORS.items():
        mask = df["regime"] == label
        if not mask.any():
            continue
        regime_df = df[mask]
        for _, row in regime_df.iterrows():
            fig.add_vrect(
                x0=row["timestamp"] - pd.Timedelta(hours=12),
                x1=row["timestamp"] + pd.Timedelta(hours=12),
                fillcolor=color,
                layer="below",
                line_width=0,
                row=1, col=1,
            )

    # Row 2 — Anomaly markers
    anomaly_df = df[df["is_anomaly"]]
    if not anomaly_df.empty:
        fig.add_trace(
            go.Scatter(
                x=anomaly_df["timestamp"],
                y=[1] * len(anomaly_df),
                mode="markers",
                marker=dict(color="red", size=8, symbol="x-thin", line=dict(width=2)),
                name="Anomaly / STOP",
            ),
            row=2, col=1,
        )
    # Add a flat reference line for anomaly zone
    fig.add_hline(y=1, line_dash="dot", line_color="gray", opacity=0.3, row=2, col=1)

    # Row 3 — Volume
    fig.add_trace(
        go.Bar(
            x=df["timestamp"],
            y=df["volume"],
            name="Volume",
            marker_color="rgba(100, 100, 255, 0.4)",
        ),
        row=3, col=1,
    )

    # ── Layout ───────────────────────────────────────────────────────────────
    fig.update_layout(
        title=dict(text=title, font=dict(size=22)),
        height=900,
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_dark",
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
    fig.update_yaxes(title_text="Anomaly", tickvals=[0, 1], ticktext=["Normal", "STOP"], row=2, col=1)
    fig.update_yaxes(title_text="Volume", row=3, col=1)
    fig.update_xaxes(title_text="Date", row=3, col=1)

    # ── Add a summary annotation ─────────────────────────────────────────────
    bull_pct = (sum(1 for r in regimes if r == "bull") / len(regimes)) * 100
    sideways_pct = (sum(1 for r in regimes if r == "sideways") / len(regimes)) * 100
    bear_pct = (sum(1 for r in regimes if r == "bear") / len(regimes)) * 100
    anomaly_count = sum(anomalies)

    summary = (
        f"<b>Regime Distribution:</b><br>"
        f"<span style='color:#26a69a'>Bull: {bull_pct:.1f}%</span> | "
        f"<span style='color:gray'>Sideways: {sideways_pct:.1f}%</span> | "
        f"<span style='color:#ef5350'>Bear: {bear_pct:.1f}%</span><br>"
        f"<b>Anomalies:</b> {anomaly_count} STOP triggers<br>"
        f"<b>Data:</b> {len(ohlcv)} bars, generated {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    fig.add_annotation(
        text=summary,
        xref="paper", yref="paper",
        x=0.01, y=0.98,
        showarrow=False,
        font=dict(size=12, color="#aaa"),
        align="left",
        bgcolor="rgba(0,0,0,0.5)",
    )

    # ── Save ─────────────────────────────────────────────────────────────────
    abs_path = os.path.abspath(output_path)
    fig.write_html(abs_path)
    logger.info(f"✅ Dashboard saved: {abs_path} ({os.path.getsize(abs_path)/1024:.0f} KB)")
    return abs_path


def main():
    parser = argparse.ArgumentParser(description="Generate HMM Regime Dashboard")
    parser.add_argument("--data", choices=["cached", "synthetic"], default="cached",
                        help="Data source (default: cached BTC from CoinGecko)")
    parser.add_argument("--output", default="hmm_dashboard.html",
                        help="Output HTML file path")
    parser.add_argument("--cached-path", default="backtest/data_cache/btc_coingecko_365d.jsonl",
                        help="Path to cached JSONL data")
    args = parser.parse_args()

    # Load data
    if args.data == "cached" and os.path.exists(args.cached_path):
        ohlcv = load_cached_data(args.cached_path)
        print(f"Loaded {len(ohlcv)} bars from {args.cached_path}")
    else:
        ohlcv = generate_synthetic_data(365)
        print(f"Generated {len(ohlcv)} synthetic bars")

    # Detect regimes
    print("Running HMM RegimeDetector...")
    regimes, anomalies, log_liks = detect_regimes(ohlcv)
    print(f"HMM complete: {len(set(regimes))} regimes detected, {sum(anomalies)} anomalies")

    # Generate dashboard
    path = generate_dashboard(ohlcv, regimes, anomalies, args.output)
    print(f"\nOpen with:  firefox {path}  (or any browser)")


if __name__ == "__main__":
    main()
