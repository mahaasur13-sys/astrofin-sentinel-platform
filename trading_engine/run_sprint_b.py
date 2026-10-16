"""Sprint B — Production Trading Engine with verified strategies.
XAUUSD 4H Improved (70%) + Multi-TF WFA Gate (30%) + dynamic risk."""

import argparse
import logging
import time
import sys
import os

import psycopg2
from prometheus_client import Gauge
from psycopg2.extras import Json

trading_engine_up = Gauge("trading_engine_up", "1 if trading engine process is running")

DB_URL = os.getenv("DATABASE_URL", "postgresql://astrofin:astrofin@localhost:5432/astrofin")

from datetime import datetime

sys.path.insert(0, "/home/workspace")

from trading_engine.signals.production_strategy import ProductionStrategy
from trading_engine.risk.manager import RiskManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("trading_engine.sprint_b")


def run_once(args) -> dict:
    """Generate a single trading signal using the production strategy."""
    strategy = ProductionStrategy(
        xau_weight=args.xau_weight / 100.0,
        wfa_weight=args.wfa_weight / 100.0,
    )
    risk = RiskManager(max_position_pct=args.max_position, max_drawdown_pct=args.max_drawdown)

    signal = strategy.compute()
    if signal.get("price_source") == "unavailable":
        logger.error("Skipping cycle, nothing persisted: %s", signal.get("error"))
        return signal

    direction = signal.get("direction", "NEUTRAL")
    confidence = signal.get("confidence", 50.0)
    price = signal.get("price", 0.0)
    regime = signal.get("regime", "NORMAL")
    risk_pct = risk.compute_risk_pct(regime, confidence)

    result = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "direction": direction,
        "confidence": confidence,
        "price": price,
        "regime": regime,
        "risk_pct": risk_pct,
        "xau_weight": args.xau_weight,
        "wfa_weight": args.wfa_weight,
        "max_position": args.max_position,
    }

    logger.info(
        "SIGNAL: %s | confidence=%.1f | risk=%.1f%% | regime=%s",
        direction, confidence, risk_pct, regime,
    )

    if args.db_save:
        _save_to_db(result)

    return result


def _save_to_db(signal_data: dict):
    """Persist signal to TimescaleDB hypertable trading_signals."""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO trading_signals
               (time, symbol, signal, confidence, risk_pct, regime, metadata)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                signal_data["timestamp"],
                "XAUUSD",
                signal_data["direction"],
                signal_data["confidence"],
                signal_data["risk_pct"],
                signal_data["regime"],
                Json(signal_data),
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as exc:
        logger.error("Failed to persist signal: %s", exc)


def run_live_loop(args):
    """Continuously generate signals at the configured interval."""
    trading_engine_up.set(1)
    logger.info("Starting live loop | interval=%ds | XAU=%.0f%% | WFA=%.0f%%",
                 args.interval, args.xau_weight, args.wfa_weight)
    try:
        while True:
            run_once(args)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("Live loop interrupted by user")
    finally:
        trading_engine_up.set(0)


def main():
    p = argparse.ArgumentParser(description="AstroFin Sprint B — Production Engine")
    p.add_argument("--live", action="store_true", help="Run live signal loop")
    p.add_argument("--once", action="store_true", help="Single signal, exit")
    p.add_argument("--interval", type=int, default=300, help="Live loop interval in seconds")
    p.add_argument("--xau-weight", type=float, default=70.0, help="XAUUSD weight %% (default: 70)")
    p.add_argument("--wfa-weight", type=float, default=30.0, help="Multi-TF WFA weight %% (default: 30)")
    p.add_argument("--max-position", type=float, default=10.0, help="Max position pct (default: 10)")
    p.add_argument("--max-drawdown", type=float, default=15.0, help="Max drawdown pct (default: 15)")
    p.add_argument("--db-save", action="store_true", help="Persist signals to TimescaleDB")
    args = p.parse_args()

    if args.live:
        run_live_loop(args)
    else:
        run_once(args)


if __name__ == "__main__":
    main()
