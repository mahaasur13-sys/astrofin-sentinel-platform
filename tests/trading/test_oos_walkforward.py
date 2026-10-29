"""OOS protocol: chronological split, embargo, walk-forward, frozen protocol, contamination, leakage.

Synthetic deterministic data only; no network, no downloads.
"""

from __future__ import annotations

import math
import socket
from datetime import datetime, timedelta, timezone

import pytest

from trading.validation import (
    Bar,
    ChronologyError,
    ContaminationError,
    LeakageError,
    ProtocolError,
    ProtocolStore,
    Segment,
    StrategyDecision,
    ValidationConfig,
    chronological_split,
    evaluate_window,
    run_development,
    run_final_oos,
    walk_forward_windows,
)
from trading.validation.splits import assert_ordered

UTC = timezone.utc
T0 = datetime(2025, 1, 1, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket.socket, "connect", boom)
    monkeypatch.setattr(socket, "getaddrinfo", boom)
    monkeypatch.setattr(socket, "create_connection", boom)


def make_bars(n=400, start=T0):
    return [Bar(start + timedelta(hours=i), round(100 + 10 * math.sin(i / 15) + 0.05 * i, 4)) for i in range(n)]


class SMAStrategy:
    version = "sma-v1"

    def __init__(self, grid=None, leak=False):
        self.param_grid = grid or [{"lookback": 3}, {"lookback": 8}, {"lookback": 20}]
        self.leak = leak
        self.calls: list[tuple[int, datetime, datetime]] = []  # (lookback, last visible ts, decision ts)

    def decide(self, params, history):
        lb = params["lookback"]
        now = history[-1]
        self.calls.append((lb, now.ts, now.ts))
        if len(history) < lb:
            return StrategyDecision("NEUTRAL", features={"sma": (None, now.ts)})
        sma = sum(b.close for b in history[-lb:]) / lb
        fts = now.ts + timedelta(hours=1) if self.leak else now.ts
        return StrategyDecision("LONG" if now.close > sma else "NEUTRAL", features={"sma": (sma, fts)})


CFG = ValidationConfig(embargo_bars=5, wf_train_bars=60, wf_test_bars=20)


# ── split ────────────────────────────────────────────────────────────────────

def test_split_chronological_no_overlap_embargo():
    bars = make_bars()
    s = chronological_split(bars, dev_fraction=0.6, validation_fraction=0.2, embargo_bars=5)
    d, v, o = s.segments()
    assert d.start == 0 and o.end == len(bars)
    assert v.start - d.end == 5 and o.start - v.end == 5
    assert bars[d.end - 1].ts < bars[v.start].ts < bars[v.end - 1].ts < bars[o.start].ts
    idx = [set(range(x.start, x.end)) for x in (d, v, o)]
    assert not (idx[0] & idx[1] or idx[1] & idx[2] or idx[0] & idx[2])
    b = s.boundaries(bars)
    assert b["embargo_bars"] == 5 and [x["name"] for x in b["segments"]] == ["development", "validation", "final_oos"]
    assert b["segments"][2]["last_ts"] == bars[-1].ts.isoformat()


@pytest.mark.parametrize("mutate", ["unsorted", "duplicate", "naive"])
def test_split_refuses_non_chronological(mutate):
    bars = make_bars(100)
    if mutate == "unsorted":
        bars[10], bars[11] = bars[11], bars[10]
    elif mutate == "duplicate":
        bars[11] = Bar(bars[10].ts, 1.0)
    else:
        bars[5] = Bar(datetime(2025, 1, 1, 5), 1.0)
    with pytest.raises(ChronologyError):
        chronological_split(bars, dev_fraction=0.6, validation_fraction=0.2, embargo_bars=2)


def test_split_refuses_bad_fractions_and_tiny_data():
    with pytest.raises(ChronologyError):
        chronological_split(make_bars(100), dev_fraction=0.8, validation_fraction=0.3, embargo_bars=1)
    with pytest.raises(ChronologyError):
        chronological_split(make_bars(8), dev_fraction=0.6, validation_fraction=0.2, embargo_bars=3)


def test_lookahead_in_split_refused():
    with pytest.raises(ChronologyError, match="overlap"):
        assert_ordered([Segment("a", 0, 50), Segment("b", 40, 60)], 0)
    with pytest.raises(ChronologyError, match="embargo"):
        assert_ordered([Segment("a", 0, 50), Segment("b", 52, 60)], 5)
    with pytest.raises(ChronologyError):
        assert_ordered([Segment("a", 0, 50), Segment("b", 55, 120)], 5, n_bars=100)


# ── walk-forward ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("anchored", [False, True])
def test_walk_forward_windows_inside_region_with_embargo(anchored):
    region = Segment("r", 0, 200)
    ws = walk_forward_windows(region, train_bars=60, test_bars=20, embargo_bars=5, anchored=anchored)
    assert len(ws) == 6
    prev_test_end = 0
    for tr, te in ws:
        assert te.start - tr.end == 5 and te.end <= 200 and te.start >= prev_test_end
        assert (tr.start == 0) if anchored else (len(tr) == 60)
        prev_test_end = te.end


def test_walk_forward_never_touches_final_oos():
    bars = make_bars()
    strat = SMAStrategy()
    rep, _ = run_development(strat, bars, CFG)
    oos_first = rep.split["segments"][2]["first_ts"]
    assert max(ts for _, ts, _ in strat.calls).isoformat() < oos_first
    for w in rep.walk_forward:
        assert w.test["last_ts"] < oos_first


def test_params_selected_only_in_sample():
    """Grid where the in-sample winner differs from the test-window winner: chosen params must be
    the in-sample argmax, and each test window is evaluated with exactly one (the chosen) variant."""
    bars = make_bars()
    strat = SMAStrategy()
    rep, _ = run_development(strat, bars, CFG)
    for w in rep.walk_forward:
        tr = Segment("t", w.train["start_index"], w.train["end_index"])
        te = Segment("e", w.test["start_index"], w.test["end_index"])
        in_sample = {p["lookback"]: evaluate_window(strat, p, bars, tr, CFG)["total_return_pct"]
                     for p in strat.param_grid}
        best_is = max(strat.param_grid, key=lambda p: in_sample[p["lookback"]])  # first wins ties
        assert w.chosen_params == best_is
        strat.calls.clear()
        evaluate_window(strat, w.chosen_params, bars, te, CFG)
        assert {c[0] for c in strat.calls} == {w.chosen_params["lookback"]}


def test_selection_ignores_test_window_content():
    """Changing prices only inside a test window must not change the params chosen for it."""
    bars = make_bars()
    rep1, _ = run_development(SMAStrategy(), bars, CFG)
    w0 = rep1.walk_forward[0]
    s, e = w0.test["start_index"], w0.test["end_index"]
    bars2 = [Bar(b.ts, b.close * (3 if s <= i < e else 1)) for i, b in enumerate(bars)]
    rep2, _ = run_development(SMAStrategy(), bars2, CFG)
    assert rep2.walk_forward[0].chosen_params == w0.chosen_params
    assert rep2.walk_forward[0].train_metrics == w0.train_metrics


def test_strategy_never_sees_future_bars():
    bars = make_bars(200)
    seen = []

    class Spy(SMAStrategy):
        def decide(self, params, history):
            seen.append(len(history))
            return super().decide(params, history)

    evaluate_window(Spy(), {"lookback": 3}, bars, Segment("w", 50, 70), CFG)
    assert seen == list(range(51, 71))


# ── leakage ──────────────────────────────────────────────────────────────────

def test_leakage_refused():
    with pytest.raises(LeakageError, match="lookahead"):
        run_development(SMAStrategy(leak=True), make_bars(), CFG)


def test_feature_without_timestamp_refused():
    class NoTs(SMAStrategy):
        def decide(self, params, history):
            return StrategyDecision("NEUTRAL", features={"x": 1.0})

    with pytest.raises(LeakageError):
        evaluate_window(NoTs(), {"lookback": 3}, make_bars(100), Segment("w", 10, 20), CFG)


# ── report / counts / determinism ────────────────────────────────────────────

def test_report_unverified_counts_and_disclaimers():
    strat = SMAStrategy()
    rep, proto = run_development(strat, make_bars(), CFG)
    assert rep.status == "UNVERIFIED" and rep.final_oos_metrics is None and rep.edge_claimed is False
    assert rep.variants_tried == 3 == proto.variants_tried
    n_w = len(rep.walk_forward)
    assert rep.evaluations == n_w * (3 + 1) + 3 + 1
    assert any("overfitting" in d for d in rep.disclaimers) and any("No trading edge" in d for d in rep.disclaimers)
    assert all(set(w.test_metrics) >= {"total_return_pct", "sharpe_ratio"} for w in rep.walk_forward)


def test_variant_count_grows_with_grid():
    grid = [{"lookback": k} for k in (2, 3, 5, 8, 13)]
    rep, _ = run_development(SMAStrategy(grid=grid), make_bars(), CFG)
    assert rep.variants_tried == 5


def test_deterministic_results():
    a, pa = run_development(SMAStrategy(), make_bars(), CFG)
    b, pb = run_development(SMAStrategy(), make_bars(), CFG)
    assert a.to_json() == b.to_json() and pa.protocol_hash == pb.protocol_hash


# ── frozen protocol / final OOS ──────────────────────────────────────────────

def _freeze(tmp_path, strat=None, bars=None, cfg=CFG):
    strat = strat or SMAStrategy()
    bars = bars or make_bars()
    rep, proto = run_development(strat, bars, cfg)
    store = ProtocolStore(tmp_path, clock=lambda: T0)
    return store, store.freeze(proto), strat, bars, rep


def test_final_oos_requires_frozen_protocol(tmp_path):
    store = ProtocolStore(tmp_path)
    with pytest.raises(ProtocolError, match="no frozen protocol"):
        run_final_oos(store, "a" * 64, SMAStrategy(), make_bars(), CFG)
    assert not list((tmp_path / "final_oos").iterdir())


def test_final_oos_runs_once(tmp_path):
    store, h, strat, bars, rep = _freeze(tmp_path)
    out = run_final_oos(store, h, strat, bars, CFG, development_report=rep)
    assert out.status == "FINAL_OOS_EVALUATED" and out.protocol_hash == h and out.edge_claimed is False
    assert out.final_oos_metrics and out.variants_tried == 3
    assert (tmp_path / "final_oos" / f"{h}.accessed").exists()
    with pytest.raises(ContaminationError, match="already viewed"):
        run_final_oos(store, h, strat, bars, CFG)
    events = [e["event"] for e in store.access_log()]
    assert events == ["FINAL_OOS_ACCESS", "FINAL_OOS_RESULT", "REFUSED"]


def test_final_oos_marker_persists_across_store_instances(tmp_path):
    store, h, strat, bars, _ = _freeze(tmp_path)
    run_final_oos(store, h, strat, bars, CFG)
    with pytest.raises(ContaminationError):
        run_final_oos(ProtocolStore(tmp_path), h, strat, bars, CFG)


def test_change_after_viewing_is_contamination(tmp_path):
    store, h, strat, bars, _ = _freeze(tmp_path)
    run_final_oos(store, h, strat, bars, CFG)
    # tweak params / grid after seeing OOS → new protocol for same strategy_version refused at freeze
    _, proto2 = run_development(SMAStrategy(grid=[{"lookback": 5}]), bars, CFG)
    with pytest.raises(ContaminationError):
        store.freeze(proto2)
    # changed config after viewing → refused as contamination, not just mismatch
    with pytest.raises(ContaminationError):
        run_final_oos(store, h, strat, bars, ValidationConfig(embargo_bars=6))


def test_mismatch_before_viewing_is_protocol_error_and_not_consumed(tmp_path):
    store, h, strat, bars, _ = _freeze(tmp_path)
    bars2 = bars[:-1] + [Bar(bars[-1].ts, bars[-1].close + 1)]
    with pytest.raises(ProtocolError, match="data"):
        run_final_oos(store, h, strat, bars2, CFG)

    class Other(SMAStrategy):
        version = "sma-v2"

    with pytest.raises(ProtocolError, match="strategy_version"):
        run_final_oos(store, h, Other(), bars, CFG)
    assert not (tmp_path / "final_oos" / f"{h}.accessed").exists()
    assert run_final_oos(store, h, strat, bars, CFG).status == "FINAL_OOS_EVALUATED"


def test_tampered_protocol_refused(tmp_path):
    store, h, strat, bars, _ = _freeze(tmp_path)
    p = tmp_path / "protocols" / f"{h}.json"
    p.chmod(0o644)
    p.write_text(p.read_text().replace('"lookback":', '"lookback":1'))
    with pytest.raises(ProtocolError):
        run_final_oos(store, h, strat, bars, CFG)


def test_freeze_is_idempotent_and_write_once(tmp_path):
    store, h, strat, bars, _ = _freeze(tmp_path)
    _, proto = run_development(SMAStrategy(), bars, CFG)
    assert store.freeze(proto) == h


def test_final_oos_deterministic(tmp_path):
    s1, h1, st1, b1, _ = _freeze(tmp_path / "a")
    s2, h2, st2, b2, _ = _freeze(tmp_path / "b")
    assert h1 == h2
    assert run_final_oos(s1, h1, st1, b1, CFG).to_json() == run_final_oos(s2, h2, st2, b2, CFG).to_json()


def test_settings_defaults_inert():
    from core.settings import Settings

    f = Settings.model_fields
    assert f["oos_wf_anchored"].default is False
    cfg = ValidationConfig.from_settings(Settings())
    assert cfg.embargo_bars == 5 and cfg.dev_fraction == 0.6


def test_not_wired_into_live():
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[2]
    bad = []
    for p in root.rglob("*.py"):
        rel = p.relative_to(root).as_posix()
        if rel.startswith(("tests/", "trading/validation/", ".venv/", "venv/")) or "/site-packages/" in rel:
            continue
        if "trading.validation" in p.read_text(errors="ignore"):
            bad.append(rel)
    assert bad == []
