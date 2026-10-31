"""Stage 2 of the validation protocol: DSR with variants_tried, buy-and-hold benchmark,
hypothesis pre-registration, backtester slippage, SMA200 reference reproduction.

Offline only. The SMA200 reproduction reads the external reference study
(``$SMA200_REFERENCE_DIR``, default /workspace/research/sma200) and is SKIPPED when it is absent.
"""

from __future__ import annotations

import math
import os
import stat
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from trading.backtester import BacktestConfig, Backtester
from trading.validation import (
    Bar,
    HypothesisRegistry,
    ProtocolError,
    ValidationConfig,
    ValidationError,
    buy_and_hold_metrics,
    buy_and_hold_returns,
    deflated_sharpe_ratio,
    expected_max_sharpe,
    performance_metrics,
    run_development,
    spec_sha256,
)
from trading.validation.splits import Segment
from trading.validation.vectorized import run_position_backtest, sma_signal

UTC = timezone.utc
T0 = datetime(2025, 1, 1, tzinfo=UTC)


# ── Deflated Sharpe ──────────────────────────────────────────────────────────


def _rets(seed=0, n=1000, mu=0.0005, sd=0.01):
    return np.random.default_rng(seed).normal(mu, sd, n)


def test_expected_max_sharpe_matches_formula():
    n, v = 4, 2.5e-4
    g = 0.5772156649
    from statistics import NormalDist

    nd = NormalDist()
    want = math.sqrt(v) * ((1 - g) * nd.inv_cdf(1 - 1 / n) + g * nd.inv_cdf(1 - 1 / (n * math.e)))
    assert expected_max_sharpe(n, v) == pytest.approx(want, rel=1e-12)
    assert expected_max_sharpe(100, v) > expected_max_sharpe(4, v)  # more trials → higher bar


def test_dsr_decreases_with_more_variants_tried():
    x = _rets()
    rng = np.random.default_rng(1)
    few = list(rng.normal(0.03, 0.02, 4))
    many = few + list(rng.normal(0.03, 0.02, 96))
    d4 = deflated_sharpe_ratio(x, few, variants_tried=4)
    d100 = deflated_sharpe_ratio(x, many, variants_tried=100)
    assert d4.n_trials == 4 and d100.n_trials == 100
    assert d100.sr0 > d4.sr0 and d100.dsr < d4.dsr
    assert 0.0 <= d100.dsr <= 1.0


def test_dsr_refuses_fewer_trial_sharpes_than_variants_tried():
    with pytest.raises(ValidationError, match="variants_tried"):
        deflated_sharpe_ratio(_rets(), [0.01, 0.02, 0.03], variants_tried=10)


def test_dsr_rejects_degenerate_input():
    with pytest.raises(ValidationError):
        deflated_sharpe_ratio([0.01], [0.1, 0.2])
    with pytest.raises(ValidationError):
        deflated_sharpe_ratio(_rets(), [0.1])  # N < 2
    with pytest.raises(ValidationError):
        deflated_sharpe_ratio([0.01, float("nan"), 0.0], [0.1, 0.2])


# ── Buy-and-hold benchmark ───────────────────────────────────────────────────


def test_buy_and_hold_returns_and_metrics():
    r = buy_and_hold_returns([100, 110, 99, 120])
    assert np.allclose(r, [0.1, -0.1, 120 / 99 - 1])
    m = performance_metrics(r, 252)
    assert m["MaxDD"] == pytest.approx(-0.1)
    with pytest.raises(ValidationError):
        buy_and_hold_returns([100, 0, 50])


def test_runner_report_includes_buy_and_hold_benchmark():
    bars = [Bar(T0 + timedelta(hours=i), 100 + 10 * math.sin(i / 15) + 0.05 * i) for i in range(400)]

    class S:
        version = "bh-test"
        param_grid = [{"lb": 5}]

        def decide(self, params, history):
            from trading.validation import StrategyDecision

            return StrategyDecision("NEUTRAL", features={})

    rep, _ = run_development(S(), bars, ValidationConfig(embargo_bars=5, wf_train_bars=60, wf_test_bars=20))
    bm = rep.benchmark_metrics["SYNTH"]
    v = rep.split["segments"][1]
    seg = Segment("validation", v["start_index"], v["end_index"])
    assert bm == buy_and_hold_metrics(bars, seg)["SYNTH"]
    first, last = bars[seg.start].close, bars[seg.end - 1].close
    assert bm["total_return_pct"] == pytest.approx((last / first - 1) * 100)
    assert "benchmark_metrics" in rep.to_dict()


def test_vectorized_backtest_benchmark_and_no_lookahead():
    idx = pd.date_range("2020-01-01", periods=300, freq="D")
    px = pd.Series(np.linspace(100, 200, 300), index=idx)
    bt = run_position_backtest(px, sma_signal(px, 200), periods_per_year=365, cost_per_side=0.001)
    f = bt.frame
    assert f.index[0] == idx[200]  # first position at t+1 after first valid signal (shift(1))
    assert (f["benchmark"] == f["r"]).all()
    assert f["strategy"].iloc[0] == pytest.approx(f["r"].iloc[0] - 0.001)  # entry cost charged


# ── Hypothesis pre-registration ──────────────────────────────────────────────


def test_registry_records_hash_before_test_and_rejects_mismatch(tmp_path):
    spec = tmp_path / "hypothesis.yaml"
    spec.write_text("id: h1\nrule: sma200\n")
    reg = HypothesisRegistry(tmp_path / "reg")
    h = reg.register(spec, "h1")
    assert h == spec_sha256(spec)
    rec_path = tmp_path / "reg" / "hypotheses" / f"{h}.json"
    assert rec_path.exists() and not (rec_path.stat().st_mode & stat.S_IWUSR)
    assert reg.require_registered(spec, h)["hypothesis_id"] == "h1"
    assert reg.register(spec, "h1") == h  # idempotent
    spec.write_text("id: h1\nrule: sma150\n")  # spec edited after registration
    with pytest.raises(ProtocolError, match="changed after registration"):
        reg.require_registered(spec, h)


def test_registry_rejects_unregistered_spec(tmp_path):
    spec = tmp_path / "h.yaml"
    spec.write_text("id: never-registered\n")
    with pytest.raises(ProtocolError, match="not pre-registered"):
        HypothesisRegistry(tmp_path / "reg").require_registered(spec, spec_sha256(spec))


# ── Backtester slippage ──────────────────────────────────────────────────────


def _bt_run(cfg):
    ts = [T0 + timedelta(days=i) for i in range(4)]
    prices = {"X": list(zip(ts, [100.0, 101.0, 102.0, 103.0]))}
    sigs = [
        {"timestamp": ts[0], "symbol": "X", "signal": "LONG", "confidence": 50},
        {"timestamp": ts[2], "symbol": "X", "signal": "NEUTRAL", "confidence": 50},
    ]
    return Backtester(cfg).run(sigs, prices)


def test_slippage_default_zero_keeps_results():
    assert BacktestConfig().slippage_pct == 0.0
    a, b = _bt_run(BacktestConfig()), _bt_run(BacktestConfig(slippage_pct=0.0))
    assert a.portfolio_summary == b.portfolio_summary
    t = a.trades[0]
    assert (t.entry_price, t.exit_price) == (100.0, 102.0)


def test_slippage_worsens_fills_both_sides():
    r = _bt_run(BacktestConfig(slippage_pct=0.5))
    t = r.trades[0]
    assert t.entry_price == pytest.approx(100.5) and t.exit_price == pytest.approx(102.0 * 0.995)
    assert r.portfolio_summary["total_return_pct"] < _bt_run(BacktestConfig()).portfolio_summary["total_return_pct"]


@pytest.mark.parametrize("bad", [-0.1, float("nan"), float("inf"), 100.0])
def test_slippage_invalid_rejected(bad):
    with pytest.raises(ValueError):
        BacktestConfig(slippage_pct=bad)


def test_config_hash_unchanged_at_default_slippage():
    # Golden hashes computed on 7dc1f7a3 (before slippage_pct existed): frozen protocols stay valid.
    assert ValidationConfig().config_hash() == "407f107f14d472f50623726ffb52451d4dfc273933146f029ae1b3d45498a220"
    assert ValidationConfig(backtest=BacktestConfig(commission_pct=0.1)).config_hash() == (
        "654d6567adfe340e5bae081ed802eaac80377ffc0e17044c92b9d3df54bee68e"
    )
    assert (
        ValidationConfig(backtest=BacktestConfig(slippage_pct=0.05)).config_hash() != ValidationConfig().config_hash()
    )


# ── SMA200 reference reproduction (acceptance, ±0.1 p.p.) ────────────────────

REF = Path(os.environ.get("SMA200_REFERENCE_DIR", "/workspace/research/sma200"))


@pytest.mark.skipif(not (REF / "results.csv").exists(), reason=f"SMA200 reference study not present at {REF}")
def test_sma200_reference_reproduces_within_0_1pp(tmp_path):
    from trading.validation import reference_sma200 as mod

    m = mod.compare(mod.reproduce(REF, tmp_path), REF / "results.csv")
    assert len(m) == 12
    for c in ("S_CAGR", "S_vol", "S_MaxDD", "S_in_mkt", "BH_CAGR", "BH_vol", "BH_MaxDD", "DSR"):
        assert m[f"d_{c}"].max() <= 0.001, c  # 0.1 percentage point
    for c in ("S_Sharpe", "BH_Sharpe"):
        assert m[f"d_{c}"].max() <= 0.001, c
    assert (m["d_S_trades"] == 0).all() and (m["d_S_n"] == 0).all()
    assert m.eq_S_start.all() and m.eq_S_end.all()
