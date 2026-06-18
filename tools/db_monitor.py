#!/usr/bin/env python3
"""DB Row Count Monitor — AstroFin Sentinel V5"""
from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent.parent
DBs = {
    "sessions (history)": BASE / "core" / "history.db",
    "backtest_runs": BASE / "backtest" / "metrics_history.db",
}

SNAPSHOT_TBL = BASE / "backtest" / "metrics_history.db"


def get_counts():
    rows = []
    for name, db_path in DBs.items():
        if not db_path.exists():
            rows.append((name, "DB NOT FOUND", 0))
            continue
        try:
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            # detect table name
            if "sessions" in name:
                cur.execute("SELECT COUNT(*) FROM sessions")
            else:
                cur.execute("SELECT COUNT(*) FROM backtest_runs")
            count = cur.fetchone()[0]
            # sample signal distribution
            if "sessions" in name:
                cur.execute("""
                    SELECT final_signal, COUNT(*)
                    FROM sessions
                    GROUP BY final_signal
                """)
                dist = dict(cur.fetchall())
            else:
                cur.execute("SELECT symbol, COUNT(*) FROM backtest_runs GROUP BY symbol")
                dist = dict(cur.fetchall())
            con.close()
            rows.append((name, count, dist))
        except Exception as e:
            rows.append((name, f"ERROR: {e}", 0))
    return rows


def save_snapshot(rows):
    """Append a snapshot row to the backtest DB for trend tracking."""
    if not SNAPSHOT_TBL.exists():
        print(f"  [monitor] {SNAPSHOT_TBL} not found — skipping snapshot")
        return
    try:
        con = sqlite3.connect(SNAPSHOT_TBL)
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS _row_count_snapshots (
                ts TEXT NOT NULL DEFAULT (datetime('now')),
                source TEXT NOT NULL,
                count INTEGER NOT NULL,
                distribution TEXT  -- JSON
            )
        """)
        for name, count, dist in rows:
            import json

            cur.execute(
                "INSERT INTO _row_count_snapshots (source, count, distribution) VALUES (?, ?, ?)",
                (name, count if isinstance(count, int) else -1, json.dumps(dist)),
            )
        con.commit()
        con.close()
    except Exception as e:
        print(f"  [monitor] snapshot failed: {e}")


def main():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f"\n=== DB Monitor {now} ===\n")

    rows = get_counts()
    for name, count, dist in rows:
        emoji = "✅" if isinstance(count, int) else "❌"
        print(f"  {emoji} {name}: {count}")
        if dist:
            for k, v in sorted(dist.items(), key=lambda x: -x[1]):
                print(f"       ├─ {k}: {v}")

    save_snapshot(rows)

    # Trend from snapshots
    if SNAPSHOT_TBL.exists():
        try:
            con = sqlite3.connect(SNAPSHOT_TBL)
            cur = con.cursor()
            cur.execute("""
                SELECT source,
                       MIN(count) as min_c,
                       MAX(count) as max_c,
                       COUNT(*) as snaps
                FROM _row_count_snapshots
                GROUP BY source
                ORDER BY source
            """)
            print("\n  --- Trend (from snapshots) ---")
            for row in cur.fetchall():
                src, mn, mx, n = row
                delta = mx - mn
                print(f"    {src}: min={mn} max={mx} delta=+{delta} ({n} snapshots)")
            con.close()
        except Exception as e:
            print(f"  [monitor] trend query failed: {e}")

    print()
    return 0 if all(isinstance(c, int) for _, c, _ in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
