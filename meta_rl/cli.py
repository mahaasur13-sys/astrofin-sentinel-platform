#!/usr/bin/env python3
"""
meta_rl/cli.py — CLI entry point for meta_rl evolution runs (ATOM-META-RL-003)

Usage:
    python -m meta_rl.cli                           # 8 gens, pop=20, historical mock
    python -m meta_rl.cli --gens 20 --pop 50      # custom params
    python -m meta_rl.cli --session my_run --load  # resume session
    python -m meta_rl.cli --live --symbol BTC/USDT --timeframe 1h  # live CCXT data
    python -m meta_rl.cli --paper --symbol ETH/USDT --gens 10       # paper mode
"""

import argparse
import logging
import sys
from datetime import datetime

from meta_rl.config import (
    DEFAULT_SYMBOL,
    DEFAULT_TIMEFRAME,
    HISTORICAL_MODE,
    LIVE_MODE,
    PAPER_MODE,
)
from meta_rl.evolution import EvolutionEngine
from meta_rl.meta_agent import EvolutionConfig, MetaAgent
from meta_rl.persistence import get_persistence

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="AstroFin Meta-RL Strategy Discovery")
    parser.add_argument("--gens", type=int, default=8)
    parser.add_argument("--pop", type=int, default=20)
    parser.add_argument("--session", default=None)
    parser.add_argument("--load", action="store_true")
    parser.add_argument("--no-walk-forward", action="store_true")
    parser.add_argument("--walk-forward-splits", type=int, default=5)
    parser.add_argument("--train-window", type=int, default=100)
    parser.add_argument("--test-window", type=int, default=20)
    parser.add_argument("--no-viz", action="store_true")

    # ── ATOM-META-RL-003: Live data options ──────────────────────────────
    parser.add_argument(
        "--mode",
        choices=[HISTORICAL_MODE, LIVE_MODE, PAPER_MODE],
        default=HISTORICAL_MODE,
        help="historical=mock, paper=CCXT sandbox, live=CCXT real",
    )
    parser.add_argument("--live", action="store_true", help="Shorthand for --mode=live")
    parser.add_argument("--paper", action="store_true", help="Shorthand for --mode=paper")
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--timeframe", default=DEFAULT_TIMEFRAME)
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--exchange", default="binance")
    # ── ──────────────────────────────────────────────────────────────────

    parser.add_argument("--visualize", action="store_true", default=False)
    parser.add_argument("--patience", type=int, default=10)
    parser.add_argument("--elite", type=int, default=4)
    parser.add_argument("--mutation-rate", type=float, default=0.15)
    parser.add_argument("--crossover-rate", type=float, default=0.40)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--list-sessions", action="store_true")
    parser.add_argument("--summary", action="store_true")

    return parser.parse_args()


def get_market_data_historical(symbol: str, limit: int) -> dict:
    """Generate historical market data using mock (for --mode=historical)."""
    from data.market_adapter import MarketAdapter
    from meta_rl.live_data import LiveDataProvider

    symbol_clean = symbol.replace("/", "").replace("-", "")
    interval_map = {
        "1m": "1h",
        "5m": "1h",
        "15m": "1h",
        "1h": "1h",
        "4h": "1h",
        "1d": "1d",
        "1w": "1d",
    }
    interval = interval_map.get(symbol, "1h")

    adapter = MarketAdapter(source="mock")
    ohlcv = adapter.fetch_ohlcv(symbol_clean, interval=interval, limit=limit)

    # LiveDataProvider adds regime, signal_strength, momentum, atr
    provider = LiveDataProvider(sandbox=True)
    market_data = provider.to_market_data(ohlcv)
    market_data["symbol"] = symbol_clean
    return market_data


def get_market_data_live(symbol: str, timeframe: str, limit: int, mode: str) -> dict:
    """ATOM-META-RL-003: Fetch live/paper market data via CCXT."""
    from meta_rl.live_data import LiveDataProvider

    sandbox = mode != LIVE_MODE
    provider = LiveDataProvider(
        exchange="binance",
        sandbox=sandbox,
    )

    logger.info(f"[CLI] Fetching {symbol} ({timeframe}) via CCXT mode={'paper/sandbox' if sandbox else 'LIVE'}")
    return provider.get_latest_bars(symbol, timeframe, limit=limit)


def run_evolution(args) -> int:
    mode = args.mode
    if args.live:
        mode = LIVE_MODE
    elif args.paper:
        mode = PAPER_MODE

    # ── Market data ───────────────────────────────────────────────────────
    if mode == HISTORICAL_MODE:
        market_data = get_market_data_historical(args.symbol, args.limit)
    else:
        market_data = get_market_data_live(args.symbol, args.timeframe, args.limit, mode)

    # ── Agent ─────────────────────────────────────────────────────────────
    cfg = EvolutionConfig(
        population_size=args.pop,
        elite_count=args.elite,
        mutation_rate=args.mutation_rate,
        crossover_rate=args.crossover_rate,
        random_seed=args.seed,
        max_generations_no_improve=args.patience,
    )
    agent = MetaAgent(config=cfg)

    # ── Engine ────────────────────────────────────────────────────────────
    session_id = args.session or (f"{mode}_{args.symbol.replace('/', '')}_{datetime.now():%Y%m%d_%H%M%S}")

    engine = EvolutionEngine(
        agent=agent,
        market_data=market_data,
        max_generations=args.gens,
        early_stopping_patience=args.patience,
        walk_forward_enabled=not args.no_walk_forward,
        n_splits=args.walk_forward_splits,
        train_window=args.train_window,
        test_window=args.test_window,
        session_id=session_id if args.load else None,
        visualize=args.visualize and not args.no_viz,
    )

    logger.info("=" * 70)
    logger.info("  meta_rl EVOLUTION  " + f"mode={mode}".ljust(50) + f"gen={args.gens}  pop={args.pop}")
    logger.info(f"  symbol={args.symbol}  tf={args.timeframe}  walk_forward={not args.no_walk_forward}")
    logger.info(f"  session={session_id}")
    logger.info("=" * 70)

    # ── Run ───────────────────────────────────────────────────────────────
    if args.load:
        logger.info("[CLI] Resuming session...")

    elites, history = engine.run()

    # ── Report ────────────────────────────────────────────────────────────
    best = engine.get_best_strategy()
    print()
    print("=" * 60)
    print("  FINAL RESULTS")
    print("=" * 60)

    if best:
        c = best.strategy.chromosome
        print(f"  Best reward:    {best.reward:+.4f}")
        print(f"  Sharpe:         {best.evaluation.sharpe:.3f}")
        print(f"  PnL:            {best.evaluation.pnl:+.3f}")
        print(f"  Max DD:         {best.evaluation.max_drawdown:.4f}")
        print(f"  Trades:         {best.evaluation.trades}")
        print()
        print(f"  conf={c['confidence_threshold']:.0f}  pos={c['position_size_pct']:.0f}%")
        print(f"  regime={c['regime_filter']}  atr={c['atr_multiplier']:.1f}")
        print(f"  mom={'Y' if c['use_momentum'] else 'N'}  rev={'Y' if c['use_mean_reversion'] else 'N'}")
    else:
        print("  No elite found")

    # ── Persistence summary ───────────────────────────────────────────────
    try:
        persist = get_persistence()
        summary = persist.get_sessions_summary()
        print()
        print(f"  Persistence: {summary['total_sessions']} sessions, {summary['total_strategies']} strategies")
        print(f"  Max reward: {summary['max_reward']:+.4f}")
        if args.visualize and not args.no_viz:
            from pathlib import Path

            out = Path(__file__).parent / "data" / "meta_rl"
            charts = list(Path(out).glob("*.png"))
            if charts:
                print(f"  Charts saved: {len(charts)}")
    except Exception as e:
        logger.warning(f"Summary failed: {e}")

    return 0


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-5s | %(message)s",
        datefmt="%H:%M:%S",
    )

    args = parse_args()

    # ── Meta commands ──────────────────────────────────────────────────────
    if args.list_sessions:
        persist = get_persistence()
        sessions = persist.list_sessions()
        print(f"\n  Sessions ({len(sessions)}):")
        for s in sessions[:20]:
            print(f"    {s}")
        return 0

    if args.summary:
        persist = get_persistence()
        summary = persist.get_sessions_summary()
        print("\n  Sessions summary:")
        for k, v in summary.items():
            print(f"    {k}: {v}")
        return 0

    return run_evolution(args)


if __name__ == "__main__":
    sys.exit(main())
