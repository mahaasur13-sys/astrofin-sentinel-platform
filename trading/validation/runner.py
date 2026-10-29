"""Walk-forward + validation + single final-OOS run, wired onto trading.backtester.Backtester."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Protocol, Sequence

from trading.backtester import BacktestConfig, Backtester

from .errors import ProtocolError, ValidationError
from .leakage import Bar, StrategyDecision, assert_chronological, assert_no_feature_leakage
from .protocol import FrozenProtocol, ProtocolStore, canonical, data_fingerprint, params_hash, _sha
from .splits import Segment, chronological_split, walk_forward_windows

STATUS_UNVERIFIED = "UNVERIFIED"
STATUS_FINAL = "FINAL_OOS_EVALUATED"

DISCLAIMERS = (
    "No trading edge is claimed by this report.",
    "Walk-forward and validation results alone do not exclude overfitting.",
    "Multiple testing: every parameter variant tried inflates the chance of a spurious result; "
    "see variants_tried.",
    "Status stays UNVERIFIED unless the final OOS ran exactly once on a frozen protocol.",
)

METRIC_KEYS = ("total_return_pct", "sharpe_ratio", "max_drawdown_pct", "total_trades", "win_rate_pct")


class Strategy(Protocol):
    version: str
    param_grid: Sequence[Mapping[str, Any]]

    def decide(self, params: Mapping[str, Any], history: Sequence[Bar]) -> StrategyDecision: ...


@dataclass(frozen=True)
class ValidationConfig:
    dev_fraction: float = 0.6
    validation_fraction: float = 0.2
    embargo_bars: int = 5
    wf_train_bars: int = 60
    wf_test_bars: int = 20
    wf_anchored: bool = False
    objective: str = "total_return_pct"
    backtest: BacktestConfig = field(default_factory=BacktestConfig)

    def __post_init__(self) -> None:
        if self.objective not in METRIC_KEYS:
            raise ValidationError(f"objective must be one of {METRIC_KEYS}")

    @classmethod
    def from_settings(cls, settings: Any = None) -> "ValidationConfig":
        if settings is None:
            from core.settings import get_settings

            settings = get_settings()
        return cls(
            dev_fraction=settings.oos_dev_fraction,
            validation_fraction=settings.oos_validation_fraction,
            embargo_bars=settings.oos_embargo_bars,
            wf_train_bars=settings.oos_wf_train_bars,
            wf_test_bars=settings.oos_wf_test_bars,
            wf_anchored=settings.oos_wf_anchored,
        )

    def config_hash(self) -> str:
        return _sha(canonical(asdict(self)))


@dataclass(frozen=True)
class WindowResult:
    name: str
    train: dict | None
    test: dict
    chosen_params: dict
    chosen_params_hash: str
    train_metrics: dict | None
    test_metrics: dict


@dataclass
class ValidationReport:
    strategy_version: str
    status: str
    split: dict
    walk_forward: list[WindowResult]
    selected_params: dict
    development_metrics: dict
    validation_metrics: dict
    final_oos_metrics: dict | None
    variants_tried: int
    evaluations: int
    protocol_hash: str | None
    disclaimers: tuple[str, ...] = DISCLAIMERS
    edge_claimed: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return canonical(self.to_dict())


class _Counter:
    def __init__(self) -> None:
        self.variants: set[str] = set()
        self.evaluations = 0


def evaluate_window(
    strategy: Strategy, params: Mapping[str, Any], bars: Sequence[Bar], seg: Segment, cfg: ValidationConfig,
    counter: _Counter | None = None,
) -> dict:
    """Run the existing Backtester on one window. The strategy only ever sees bars[: i + 1]."""
    if seg.end > len(bars):
        raise ValidationError(f"window {seg.name} beyond data")
    signals = []
    for i in range(seg.start, seg.end):
        decision_ts = bars[i].ts
        d = strategy.decide(params, tuple(bars[: i + 1]))
        assert_no_feature_leakage(d, decision_ts)
        signals.append({"timestamp": decision_ts, "symbol": bars[i].symbol, "signal": d.signal,
                        "confidence": d.confidence})
    prices: dict[str, list] = {}
    for b in bars[seg.start:seg.end]:
        prices.setdefault(b.symbol, []).append((b.ts, b.close))
    summary = Backtester(cfg.backtest).run(signals, prices).portfolio_summary
    if counter is not None:
        counter.variants.add(params_hash(params))
        counter.evaluations += 1
    return {k: summary[k] for k in METRIC_KEYS}


def _select(strategy, bars, seg, cfg, counter) -> tuple[dict, dict]:
    """Pick params by objective on ``seg`` only (ties → first in grid order)."""
    if not strategy.param_grid:
        raise ValidationError("empty param_grid")
    best = None
    for p in strategy.param_grid:
        m = evaluate_window(strategy, p, bars, seg, cfg, counter)
        if best is None or m[cfg.objective] > best[1][cfg.objective]:
            best = (dict(p), m)
    return best


def _build_protocol(strategy, params, split, bars, cfg, counter) -> FrozenProtocol:
    return FrozenProtocol(
        strategy_version=strategy.version,
        params=dict(params),
        params_hash=params_hash(params),
        split=split.boundaries(bars),
        config_hash=cfg.config_hash(),
        data_fingerprint=data_fingerprint(bars),
        variants_tried=len(counter.variants),
    )


def run_development(strategy: Strategy, bars: Sequence[Bar], cfg: ValidationConfig | None = None
                    ) -> tuple[ValidationReport, FrozenProtocol]:
    """Walk-forward on Dev+Validation, select on Development, check on Validation. Never touches final OOS.

    Returns the UNVERIFIED report and a protocol candidate to freeze before final OOS."""
    cfg = cfg or ValidationConfig()
    assert_chronological(bars)
    split = chronological_split(bars, dev_fraction=cfg.dev_fraction,
                                validation_fraction=cfg.validation_fraction, embargo_bars=cfg.embargo_bars)
    region = Segment("dev+validation", 0, split.validation.end)
    counter = _Counter()
    windows = []
    for tr, te in walk_forward_windows(region, train_bars=cfg.wf_train_bars, test_bars=cfg.wf_test_bars,
                                       embargo_bars=cfg.embargo_bars, anchored=cfg.wf_anchored):
        params, train_m = _select(strategy, bars, tr, cfg, counter)
        test_m = evaluate_window(strategy, params, bars, te, cfg, counter)
        windows.append(WindowResult(tr.name[:-6], tr.boundaries(bars), te.boundaries(bars), params,
                                    params_hash(params), train_m, test_m))
    params, dev_m = _select(strategy, bars, split.development, cfg, counter)
    val_m = evaluate_window(strategy, params, bars, split.validation, cfg, counter)
    protocol = _build_protocol(strategy, params, split, bars, cfg, counter)
    report = ValidationReport(
        strategy_version=strategy.version, status=STATUS_UNVERIFIED, split=split.boundaries(bars),
        walk_forward=windows, selected_params=params, development_metrics=dev_m, validation_metrics=val_m,
        final_oos_metrics=None, variants_tried=len(counter.variants), evaluations=counter.evaluations,
        protocol_hash=None,
    )
    return report, protocol


def run_final_oos(
    store: ProtocolStore, protocol_hash: str, strategy: Strategy, bars: Sequence[Bar],
    cfg: ValidationConfig | None = None, *, development_report: ValidationReport | None = None,
) -> ValidationReport:
    """Run the final OOS exactly once for a frozen protocol. Mismatch → ProtocolError (nothing viewed);
    re-run or a different protocol for an already-viewed strategy → ContaminationError."""
    cfg = cfg or ValidationConfig()
    protocol = store.load(protocol_hash)
    assert_chronological(bars)
    split = chronological_split(bars, dev_fraction=cfg.dev_fraction,
                                validation_fraction=cfg.validation_fraction, embargo_bars=cfg.embargo_bars)
    problems = []
    if strategy.version != protocol.strategy_version:
        problems.append("strategy_version")
    if cfg.config_hash() != protocol.config_hash:
        problems.append("config")
    if data_fingerprint(bars) != protocol.data_fingerprint:
        problems.append("data")
    if canonical(split.boundaries(bars)) != canonical(protocol.split):
        problems.append("split")
    if params_hash(protocol.params) != protocol.params_hash:
        problems.append("params")
    if problems:
        # still subject to the contamination rule if this strategy already viewed final OOS
        if store.viewed_protocols(strategy.version):
            store.claim_final_oos(protocol)  # raises ContaminationError
        store.refuse(protocol_hash, strategy.version, f"protocol mismatch: {problems}")
        raise ProtocolError(f"run does not match frozen protocol {protocol_hash}: {problems}")
    store.claim_final_oos(protocol)  # marker + log BEFORE any OOS computation
    oos_m = evaluate_window(strategy, protocol.params, bars, split.final_oos, cfg)
    store.record_result(protocol_hash, strategy.version, oos_m)
    base = development_report
    return ValidationReport(
        strategy_version=strategy.version, status=STATUS_FINAL, split=split.boundaries(bars),
        walk_forward=base.walk_forward if base else [], selected_params=dict(protocol.params),
        development_metrics=base.development_metrics if base else {},
        validation_metrics=base.validation_metrics if base else {},
        final_oos_metrics=oos_m, variants_tried=protocol.variants_tried,
        evaluations=(base.evaluations if base else 0) + 1, protocol_hash=protocol_hash,
    )
