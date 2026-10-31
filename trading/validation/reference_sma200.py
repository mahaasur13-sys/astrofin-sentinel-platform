"""Reproduce the SMA200 reference study (research/sma200) with trading.validation code.

Offline: reads the reference CSVs only (no downloads). Usage:
  python -m trading.validation.reference_sma200 [REFERENCE_DIR]   (default: $SMA200_REFERENCE_DIR or
  /workspace/research/sma200). Prints the max absolute delta per column vs results.csv.

The hypothesis spec is pre-registered (sha256 recorded) before anything is computed.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pandas as pd

from .registry import HypothesisRegistry, spec_sha256
from .stats import deflated_sharpe_ratio
from .vectorized import run_position_backtest, sma_signal

ASSETS = {"BTC-USD": (0.001, 365), "SPY": (0.0005, 252)}  # cost per side (from hypothesis.yaml), periods/yr
PERIODS = {"full": (None, None), "IS..2018": (None, "2018-12-31"), "OOS2019..": ("2019-01-01", None)}
COMPARE = [
    "S_CAGR",
    "S_vol",
    "S_Sharpe",
    "S_MaxDD",
    "S_trades",
    "S_in_mkt",
    "S_n",
    "BH_CAGR",
    "BH_vol",
    "BH_Sharpe",
    "BH_MaxDD",
    "DSR",
    "SR0_daily",
]


def default_reference_dir() -> Path:
    return Path(os.environ.get("SMA200_REFERENCE_DIR", "/workspace/research/sma200"))


def reproduce(ref: Path, registry_root: Path) -> pd.DataFrame:
    spec = ref / "hypothesis.yaml"
    reg = HypothesisRegistry(registry_root)
    h = reg.register(spec, "sma200-btc-spy-2026-10-31")
    reg.require_registered(spec, h)  # gate: spec unchanged since registration
    runs = {}
    for t, (c, ppy) in ASSETS.items():
        px = pd.read_csv(ref / "data" / f"{t}.csv", index_col=0, parse_dates=True)["Close"].dropna()
        sig = sma_signal(px, 200)
        for cost in (c, 0.0):
            runs[(t, cost)] = run_position_backtest(px, sig, periods_per_year=ppy, cost_per_side=cost)
    rows = []
    for per, (a, b) in PERIODS.items():
        trial_srs = []
        for bt in runs.values():
            s = bt.frame["strategy"].loc[a:b]
            trial_srs.append(s.mean() / s.std())
        for (t, cost), bt in runs.items():
            m = bt.metrics(a, b)
            s = bt.frame["strategy"].loc[a:b].to_numpy()
            d = deflated_sharpe_ratio(s, trial_srs, variants_tried=4)  # N=4 per hypothesis.yaml
            st, bh = m["strategy"], m["buy_and_hold"]
            rows.append(
                {
                    "asset": t,
                    "cost": cost,
                    "period": per,
                    "S_CAGR": st["CAGR"],
                    "S_vol": st["vol"],
                    "S_Sharpe": st["Sharpe"],
                    "S_MaxDD": st["MaxDD"],
                    "S_trades": st["trades"],
                    "S_in_mkt": st["in_mkt"],
                    "S_start": m["start"],
                    "S_end": m["end"],
                    "S_n": st["n"],
                    "BH_CAGR": bh["CAGR"],
                    "BH_vol": bh["vol"],
                    "BH_Sharpe": bh["Sharpe"],
                    "BH_MaxDD": bh["MaxDD"],
                    "DSR": d.dsr,
                    "SR0_daily": d.sr0,
                    "spec_sha256": h,
                }
            )
    return pd.DataFrame(rows)


def compare(ours: pd.DataFrame, ref_csv: Path) -> pd.DataFrame:
    ref = pd.read_csv(ref_csv)
    key = ["asset", "cost", "period"]
    m = ours.merge(ref, on=key, suffixes=("", "_ref"), validate="one_to_one")
    if len(m) != len(ref):
        raise SystemExit(f"row mismatch: {len(m)} vs {len(ref)}")
    for c in COMPARE:
        m[f"d_{c}"] = (m[c] - m[f"{c}_ref"]).abs()
    for c in ("S_start", "S_end"):
        m[f"eq_{c}"] = m[c] == m[f"{c}_ref"]
    return m


def main(argv: list[str]) -> int:
    ref = Path(argv[1]) if len(argv) > 1 else default_reference_dir()
    print("reference:", ref, "spec_sha256:", spec_sha256(ref / "hypothesis.yaml"))
    with tempfile.TemporaryDirectory() as tmp:
        m = compare(reproduce(ref, Path(tmp)), ref / "results.csv")
    for c in COMPARE:
        print(f"max |delta| {c:10s} = {m[f'd_{c}'].max():.3e}")
    print("dates equal:", bool(m.eq_S_start.all() and m.eq_S_end.all()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
