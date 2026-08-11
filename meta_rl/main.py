"""
Meta-RL Evolution Worker — daemon entrypoint.
Runs the EvolutionEngine in a continuous loop with configurable intervals.

Usage:
    python -m meta_rl.main --loop --interval 300
    python -m meta_rl.main --once --population 10 --generations 3

Architecture:
    EvolutionConfig → MetaAgent → EvolutionEngine.run()
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import threading
import time
from typing import Any

logger = logging.getLogger("evolution_worker")


def run_one_evolution(args: argparse.Namespace) -> int:
    """Execute a single evolution pass, return exit code."""
    try:
        from datetime import datetime, timezone
        from meta_rl.meta_agent import EvolutionConfig, MetaAgent
        from meta_rl.evolution import EvolutionEngine
        from meta_rl.strategy_evaluator import StrategyEvaluator
        from backtest.engine import fetch_range

        cfg = EvolutionConfig(
            population_size=args.population or 20,
            mutation_rate=args.mutation_rate or 0.15,
            crossover_rate=args.crossover_rate or 0.4,
        )

        # Fetch real OHLCV data for strategy evaluation
        start_dt = datetime(2025, 6, 1, tzinfo=timezone.utc)
        end_dt = datetime.now(timezone.utc)
        ohlcv = fetch_range(args.symbol, args.timeframe, start_dt, end_dt)
        market_data = {"ohlcv": ohlcv, "symbol": args.symbol, "timeframe": args.timeframe}
        logger.info(f"fetched {len(ohlcv)} bars for {args.symbol} {args.timeframe}")

        evaluator = StrategyEvaluator()
        agent = MetaAgent(config=cfg, evaluator=evaluator)
        engine = EvolutionEngine(
            agent=agent,
            market_data=market_data,
            max_generations=args.generations or 10,
            walk_forward_enabled=False,
            visualize=False,
        )
        logger.info(f"evolution start: symbol={args.symbol} timeframe={args.timeframe}")
        _results, stats = engine.run(ensemble_seeds=3)
        if stats:
            last = stats[-1]
            logger.info(
                f"evolution complete: gen={last.generation} best={round(last.max_reward, 4)} mean={round(last.mean_reward, 4)} pop_size={last.pool_size} strategies={last.pool_size}"
            )
        return 0
    except Exception:
        logger.exception("evolution failed")
        return 1

def run_loop(args: argparse.Namespace) -> None:
    """Run evolution passes in a loop with configurable interval."""
    shutdown = False

    def _handle_signal(signum: int, _frame: Any) -> None:
        nonlocal shutdown
        logger.info(f"evolution_worker.signal_received: signal={signum}")
        shutdown = True

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    # Start Prometheus metrics HTTP server on dedicated port
    metrics_port = int(args.metrics_port)
    from prometheus_client import start_http_server
    threading.Thread(
        target=start_http_server, args=(metrics_port,),
        kwargs={'addr': '0.0.0.0'}, daemon=True, name='evo-metrics-http'
    ).start()
    logger.info(f"evolution_worker.metrics_server: port={metrics_port}")

    while not shutdown:
        run_one_evolution(args)
        if args.once:
            break
        logger.info(f"evolution_worker.sleep: seconds={args.interval}")
        for _ in range(args.interval):
            if shutdown:
                break
            time.sleep(1)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Meta-RL Evolution Worker")
    p.add_argument("--symbol", default="BTCUSDT", help="Trading symbol")
    p.add_argument("--timeframe", default="1h", help="Timeframe (1h, 4h, 1d)")
    p.add_argument("--population", type=int, default=0, help="Population size (0=EvolutionConfig default)")
    p.add_argument("--generations", type=int, default=0, help="Max generations (0=default 50)")
    p.add_argument("--mutation-rate", type=float, default=0.0, help="Mutation rate (0=default 0.15)")
    p.add_argument("--crossover-rate", type=float, default=0.0, help="Crossover rate (0=default 0.4)")
    p.add_argument("--interval", type=int, default=300, help="Sleep between passes (seconds)")
    p.add_argument("--once", action="store_true", help="Run once and exit")
    p.add_argument("--metrics-port", type=int, default=9192, help="Prometheus metrics HTTP port (default: 9192)")
    p.add_argument("--loop", dest="loop", action="store_true", help="Run in continuous loop")
    p.add_argument("--production", dest="production", action="store_true", help="Use live market data for evaluation (default: backtest data)")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)-8s] %(name)s.%(funcName)-20s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    if args.once:
        return run_one_evolution(args)
    if args.loop:
        run_loop(args)
        return 0
    # Default: run once
    return run_one_evolution(args)


if __name__ == "__main__":
    sys.exit(main())
