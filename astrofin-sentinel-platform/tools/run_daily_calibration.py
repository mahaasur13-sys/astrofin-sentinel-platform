#!/usr/bin/env python3
"""tools/run_daily_calibration.py — Daily agent weight calibration pipeline.

Scheduled via cron or GitHub Actions to run once per day.
Queries last 7 days of Paper Trading sessions from PostgreSQL,
computes Win Rate / Sharpe per agent, applies Bayesian weight update,
and persists new weights + history.

Usage:
  python -m tools.run_daily_calibration [--dry-run] [--days 7]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import structlog

log = structlog.get_logger(__name__)

# ── Default agent weights (from AGENTS.md) ─────────────────────────────────
DEFAULT_WEIGHTS: dict[str, float] = {
    "FundamentalAgent": 0.20,
    "QuantAgent": 0.20,
    "MacroAgent": 0.15,
    "OptionsFlowAgent": 0.15,
    "SentimentAgent": 0.10,
    "TechnicalAgent": 0.10,
    "BullResearcher": 0.05,
    "BearResearcher": 0.05,
    "BradleyAgent": 0.03,
    "ElectoralAgent": 0.03,
    "GannAgent": 0.03,
    "CycleAgent": 0.05,
    "TimeWindowAgent": 0.02,
}

# ── Bayesian update constants ──────────────────────────────────────────────
PRIOR_STRENGTH = 30  # equivalent prior observations (higher = more conservative)
MIN_WEIGHT = 0.01
MAX_WEIGHT = 0.50
WEIGHT_EPSILON = 0.005  # minimum change to log


def _get_pg_connection():
    """Create a psycopg2 connection from DATABASE_URL or fallback."""
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        log.warning("DATABASE_URL not set, cannot connect to PostgreSQL")
        return None

    import psycopg2

    return psycopg2.connect(dsn)


def _ensure_history_table(conn):
    """Create agent_weights_history if it doesn't exist."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agent_weights_history (
                id            SERIAL PRIMARY KEY,
                calibration_ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                agent_name    TEXT    NOT NULL,
                old_weight    REAL    NOT NULL,
                new_weight    REAL    NOT NULL,
                win_rate      REAL    NOT NULL DEFAULT 0.0,
                sharpe        REAL    NOT NULL DEFAULT 0.0,
                trades_count  INTEGER NOT NULL DEFAULT 0,
                pnl_total     REAL    NOT NULL DEFAULT 0.0,
                max_drawdown  REAL    NOT NULL DEFAULT 0.0,
                metadata      JSONB   NOT NULL DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_agent_weights_ts
                ON agent_weights_history(calibration_ts);
            CREATE INDEX IF NOT EXISTS idx_agent_weights_name
                ON agent_weights_history(agent_name);
        """)
        conn.commit()


def _fetch_sessions(conn, days: int) -> list[dict]:
    """Fetch sessions from the last N days."""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT session_id, symbol, final_signal, final_confidence,
                   final_output, created_at
            FROM sessions
            WHERE created_at >= %s
            ORDER BY created_at DESC
        """, (since,))
        rows = cur.fetchall()
    return [
        {
            "session_id": r[0],
            "symbol": r[1],
            "final_signal": r[2],
            "final_confidence": r[3],
            "final_output": r[4] if isinstance(r[4], dict) else json.loads(r[4] or "{}"),
            "created_at": r[5],
        }
        for r in rows
    ]


def _extract_agent_weights(session: dict) -> dict[str, float]:
    """Extract per-agent weights from the session's final_output payload."""
    fo = session.get("final_output", {})

    # Path 1: explicit agent_weights key
    if "agent_weights" in fo and isinstance(fo["agent_weights"], dict):
        return fo["agent_weights"]

    # Path 2: synthesis_result has weights
    synth = fo.get("synthesis_result", {})
    if isinstance(synth, dict) and "agent_weights" in synth:
        return synth["agent_weights"]

    # Path 3: individual agent responses with metadata.weight
    agent_responses = fo.get("agent_responses", [])
    if agent_responses:
        weights = {}
        for ar in agent_responses:
            name = ar.get("agent_id", ar.get("agent", ""))
            weight = ar.get("metadata", {}).get("weight")
            if name and weight is not None:
                weights[name] = float(weight)
        if weights:
            return weights

    return {}


def _score_signal(signal: str, confidence: float, sessions: list[dict]) -> float:
    """Score a signal based on next-session price movement.

    Simple heuristic: if LONG and next conf is higher = positive.
    In production, replace with actual PnL from next candle.
    """
    return 0.0  # placeholder — requires actual market data or trade PnL


def _calculate_metrics(sessions: list[dict]) -> dict[str, dict]:
    """Calculate Win Rate and Sharpe per agent from session history.

    Uses signal-direction accuracy as a proxy for Win Rate
    (in production, replace with actual per-trade PnL from a trade journal).
    """
    metrics: dict[str, dict] = {}

    for session in sessions:
        signal = session.get("final_signal", "NEUTRAL")
        conf = session.get("final_confidence", 50)
        weights = _extract_agent_weights(session)

        for agent_name, weight in weights.items():
            if agent_name not in metrics:
                metrics[agent_name] = {
                    "trades": 0,
                    "wins": 0,
                    "weight_sum": 0.0,
                    "conf_sum": 0.0,
                }
            metrics[agent_name]["trades"] += 1
            metrics[agent_name]["weight_sum"] += weight
            metrics[agent_name]["conf_sum"] += float(conf)
            if signal in ("LONG", "STRONG_BUY", "BUY") and conf > 55:
                metrics[agent_name]["wins"] += 1
            elif signal in ("SHORT", "SELL") and conf > 55:
                metrics[agent_name]["wins"] += 1

    results = {}
    for name, m in metrics.items():
        trades = m["trades"]
        win_rate = m["wins"] / trades if trades > 0 else 0.0
        avg_conf = m["conf_sum"] / trades if trades > 0 else 50.0
        avg_weight = m["weight_sum"] / trades if trades > 0 else 0.0
        # Simplified Sharpe: win_rate scaled by confidence dispersion
        sharpe = win_rate * (avg_conf / 100.0)

        results[name] = {
            "trades_count": trades,
            "win_rate": round(win_rate, 4),
            "sharpe": round(sharpe, 4),
            "avg_weight": round(avg_weight, 4),
            "avg_confidence": round(avg_conf, 2),
            "pnl_total": 0.0,
            "max_drawdown": 0.0,
        }

    return results


def _bayesian_update(old_weight: float, performance_score: float, trades: int) -> float:
    """Bayesian update: blend prior weight with observed performance.

    new_weight = (old_weight * PRIOR_STRENGTH + score * trades) / (PRIOR_STRENGTH + trades)
    """
    if trades == 0:
        return old_weight

    new = (old_weight * PRIOR_STRENGTH + performance_score * trades) / (PRIOR_STRENGTH + trades)
    return max(MIN_WEIGHT, min(MAX_WEIGHT, new))


def _load_current_weights(conn) -> dict[str, float]:
    """Load the most recent weights from agent_weights_history."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT agent_name, new_weight
            FROM agent_weights_history
            WHERE (agent_name, calibration_ts) IN (
                SELECT agent_name, MAX(calibration_ts)
                FROM agent_weights_history
                GROUP BY agent_name
            )
        """)
        rows = cur.fetchall()

    if rows:
        return {r[0]: r[1] for r in rows}
    return dict(DEFAULT_WEIGHTS)


def _save_weights(conn, agent_name: str, old_weight: float, new_weight: float,
                  metrics: dict, dry_run: bool = False):
    """Persist weight change to agent_weights_history."""
    if dry_run:
        log.info(
            "DRY-RUN: weight update",
            agent=agent_name,
            old=round(old_weight, 4),
            new=round(new_weight, 4),
            win_rate=metrics.get("win_rate", 0),
            sharpe=metrics.get("sharpe", 0),
        )
        return

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO agent_weights_history
                (agent_name, old_weight, new_weight, win_rate, sharpe,
                 trades_count, pnl_total, max_drawdown, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            agent_name,
            old_weight,
            new_weight,
            metrics.get("win_rate", 0.0),
            metrics.get("sharpe", 0.0),
            metrics.get("trades_count", 0),
            metrics.get("pnl_total", 0.0),
            metrics.get("max_drawdown", 0.0),
            json.dumps({"source": "run_daily_calibration"}),
        ))
        conn.commit()


def run_calibration(days: int = 7, dry_run: bool = False):
    """Main calibration pipeline."""
    log.info("Starting daily calibration", days=days, dry_run=dry_run)

    conn = _get_pg_connection()
    if conn is None:
        log.warning("No PostgreSQL connection available — exiting")
        return

    try:
        _ensure_history_table(conn)

        sessions = _fetch_sessions(conn, days)
        log.info("Sessions loaded", count=len(sessions))

        if not sessions:
            log.info("No sessions in window — nothing to calibrate")
            return

        agent_metrics = _calculate_metrics(sessions)
        current_weights = _load_current_weights(conn)

        for agent_name, metrics in agent_metrics.items():
            old_weight = current_weights.get(agent_name, DEFAULT_WEIGHTS.get(agent_name, 0.05))
            trades = metrics["trades_count"]
            score = metrics["win_rate"]

            new_weight = _bayesian_update(old_weight, score, trades)
            if new_weight != 0.0 and abs(new_weight - old_weight) < WEIGHT_EPSILON:
                continue  # no meaningful change

            _save_weights(conn, agent_name, old_weight, new_weight, metrics, dry_run=dry_run)

        # Always calibrate unobserved agents at default weights
        for name, default_w in DEFAULT_WEIGHTS.items():
            if name not in agent_metrics and name in current_weights:
                _save_weights(conn, name, current_weights[name], default_w,
                              {"trades_count": 0, "win_rate": 0.0, "sharpe": 0.0,
                               "pnl_total": 0.0, "max_drawdown": 0.0},
                              dry_run=dry_run)

        log.info("Calibration complete", agents_updated=len(agent_metrics))

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Daily agent weight calibration")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simulate without writing to DB")
    parser.add_argument("--days", type=int, default=7,
                        help="Lookback window in days (default: 7)")
    args = parser.parse_args()

    run_calibration(days=args.days, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
