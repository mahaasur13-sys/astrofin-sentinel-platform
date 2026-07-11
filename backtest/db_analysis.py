#!/usr/bin/env python3
"""
AstroFin Sentinel V5 — Database Analysis Script
Run: python backtest/db_analysis.py
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime

DB_HISTORY = "core/history.db"
DB_BELIEF = "core/belief.db"
DB_METRICS = "backtest/metrics_history.db"


def run_query(db_path, query, params=None):
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute(query, params or ())
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        con.close()
        return cols, rows
    except Exception as e:  # noqa: BLE001
        return [str(e)], []


def safe_json(val):
    if not val:
        return {}
    if isinstance(val, dict):
        return val
    try:
        return json.loads(val)
    except Exception:  # noqa: BLE001
        return {}


def print_table(headers, rows, title=""):
    if title:
        print(f"\n### {title}")
    if not rows:
        print("  (no data)")
        return
    col_widths = [
        max(len(str(h)), max(len(str(r[i])) for r in rows)) if i < len(headers) else 10 for i, h in enumerate(headers)
    ]
    sep = "  "
    header_line = sep.join(f"{h:<w}" for h, w in zip(headers, col_widths, strict=False))
    print(f"  {header_line}")
    print(f"  {'─' * len(header_line)}")
    for row in rows:
        print(f"  {sep.join(f'{str(row[i]):<w}' for i, w in enumerate(col_widths))}")


def main():
    print("=" * 70)
    print("  ASTROFIN SENTINEL V5 — DATABASE RESEARCH")
    print("=" * 70)
    print(f"\nGenerated: {datetime.now().isoformat()}")

    # ── 1. Basic stats ──────────────────────────────────────────────────
    print("\n## 1. BASIC STATS")

    cols, rows = run_query(DB_HISTORY, "SELECT COUNT(*) FROM sessions")
    sessions_count = rows[0][0] if rows else 0
    print(f"  Total sessions: {sessions_count}")

    cols, rows = run_query(DB_METRICS, "SELECT COUNT(*) FROM backtest_runs")
    backtest_count = rows[0][0] if rows else 0
    print(f"  Total backtest runs: {backtest_count}")

    # ── 2. Signal distribution ───────────────────────────────────────────
    print("\n## 2. SIGNAL DISTRIBUTION")
    cols, rows = run_query(
        DB_HISTORY,
        """
        SELECT final_signal, COUNT(*) as count,
               ROUND(AVG(final_confidence), 1) as avg_conf,
               MIN(final_confidence) as min_conf,
               MAX(final_confidence) as max_conf
        FROM sessions GROUP BY final_signal ORDER BY count DESC
    """,
    )
    print_table(cols, rows, "Signal counts")

    # ── 3. Symbol / timeframe distribution ─────────────────────────────
    print("\n## 3. SYMBOL / TIMEFRAME")
    cols, rows = run_query(
        DB_HISTORY,
        """
        SELECT symbol, timeframe, COUNT(*) as sessions,
               ROUND(AVG(final_confidence), 1) as avg_conf
        FROM sessions GROUP BY symbol, timeframe ORDER BY sessions DESC
    """,
    )
    print_table(cols, rows)

    # ── 4. Thompson Beliefs ──────────────────────────────────────────────
    print("\n## 4. THOMPSON BELIEFS (Beta distributions)")
    cols, rows = run_query(
        DB_BELIEF,
        """
        SELECT agent_name, alpha, beta,
               ROUND(alpha / (alpha + beta), 3) as mean,
               ROUND(alpha + beta - 2, 0) as trials
        FROM agent_beliefs ORDER BY mean DESC
    """,
    )
    print_table(cols, rows)

    # ── 5. Agent belief history ─────────────────────────────────────────
    print("\n## 5. BELIEF HISTORY")
    cols, rows = run_query(
        DB_BELIEF,
        """
        SELECT agent_name, is_success, COUNT(*) as count
        FROM agent_belief_history GROUP BY agent_name, is_success
    """,
    )
    print_table(cols, rows)

    # ── 6. Thompson Selection Log ──────────────────────────────────────
    print("\n## 6. THOMPSON SELECTION COVERAGE")
    cols, rows = run_query(
        DB_BELIEF,
        """
        SELECT agent_name, pool_name,
               SUM(was_called) as called,
               SUM(CAST(success_flag AS INTEGER)) as successes,
               COUNT(*) as total
        FROM agent_selection_log GROUP BY agent_name
    """,
    )
    if rows:
        print_table(cols, rows)
    else:
        print("  (no data in agent_selection_log)")

    # ── 7. Backtest performance ─────────────────────────────────────────
    print("\n## 7. BACKTEST PERFORMANCE")
    cols, rows = run_query(
        DB_METRICS,
        """
        SELECT symbol, timeframe, COUNT(*) as runs,
               ROUND(AVG(win_rate)*100, 1) as avg_wr,
               ROUND(AVG(sharpe_ratio), 2) as avg_sr,
               SUM(total_trades) as trades,
               ROUND(MAX(total_return_pct), 1) as best_ret,
               ROUND(MIN(total_return_pct), 1) as worst_ret,
               ROUND(AVG(max_drawdown_pct), 1) as avg_mdd
        FROM backtest_runs GROUP BY symbol, timeframe
    """,
    )
    print_table(cols, rows)

    # ── 8. Sessions over time ────────────────────────────────────────────
    print("\n## 8. SESSIONS OVER TIME (last 10 days)")
    cols, rows = run_query(
        DB_HISTORY,
        """
        SELECT DATE(created_at) as day, COUNT(*) as sessions,
               ROUND(AVG(final_confidence), 1) as avg_conf,
               SUM(CASE WHEN final_signal IN ('BUY','LONG') THEN 1 ELSE 0 END) as buy,
               SUM(CASE WHEN final_signal IN ('SELL','SHORT') THEN 1 ELSE 0 END) as sell
        FROM sessions GROUP BY day ORDER BY day DESC LIMIT 10
    """,
    )
    print_table(cols, rows)

    # ── 9. JSON quality check ────────────────────────────────────────────
    print("\n## 9. DATA QUALITY")

    # Check JSON fields
    cols, rows = run_query(
        DB_HISTORY,
        """
        SELECT session_id, final_signal,
               LENGTH(final_output) as output_len,
               LENGTH(thompson_selections) as thompson_len
        FROM sessions
        WHERE final_output IS NULL OR final_output = '' OR final_output = '{}'
    """,
    )
    null_output = len(rows)
    print(f"  Sessions with NULL/empty final_output: {null_output}")

    cols, rows = run_query(
        DB_HISTORY,
        """
        SELECT COUNT(*) FROM sessions WHERE final_confidence < 0 OR final_confidence > 100
    """,
    )
    bad_conf = rows[0][0] if rows else 0
    print(f"  Sessions with invalid confidence (0 or >100): {bad_conf}")

    # ── 10. Deep analysis: extract signals from final_output ─────────────
    print("\n## 10. AGENT SIGNALS IN FINAL_OUTPUT")

    # Sample some sessions to see what agents actually return
    cols, rows = run_query(
        DB_HISTORY,
        """
        SELECT session_id, final_signal, final_confidence,
               substr(final_output, 1, 500) as output_preview
        FROM sessions ORDER BY created_at DESC LIMIT 3
    """,
    )
    print_table(cols, rows, "Last 3 sessions (preview)")

    # ── Critical Findings ─────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  🚨 CRITICAL FINDINGS")
    print("=" * 70)

    # Check if all signals are NEUTRAL
    cols, rows = run_query(
        DB_HISTORY,
        """
        SELECT final_signal, COUNT(*) * 100.0 / (SELECT COUNT(*) FROM sessions) as pct
        FROM sessions GROUP BY final_signal
    """,
    )
    neutral_pct = 0
    for row in rows:
        if row[0] == "NEUTRAL":
            neutral_pct = row[1]

    if neutral_pct > 80:
        print(f"\n  ⚠️  {neutral_pct:.0f}% of sessions = NEUTRAL (expected ~50% max)")
        print("  → Root cause: Agents not giving directional signals")
        print("  → Check: Are FundamentalAgent, QuantAgent, OptionsFlowAgent running?")
        print("  → Check: Is MACRO_POOL included in run_sentinel_v5?")

    # Check belief tracking
    cols, rows = run_query(DB_BELIEF, "SELECT COUNT(*) FROM agent_beliefs")
    belief_count = rows[0][0] if rows else 0
    if belief_count < 5:
        print(f"\n  ⚠️  Only {belief_count} agents tracked in belief.db")
        print("  → Should be 8+ agents (all Thompson-sampled)")

    # Check selection log
    cols, rows = run_query(DB_BELIEF, "SELECT COUNT(*) FROM agent_selection_log")
    sel_count = rows[0][0] if rows else 0
    if sel_count == 0:
        print("\n  ⚠️  agent_selection_log is EMPTY (0 rows)")
        print("  → Thompson sampling decisions not being logged")
        print("  → Check: update_beliefs_from_session() called?")

    print("\n" + "=" * 70)
    print("  Analysis complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
