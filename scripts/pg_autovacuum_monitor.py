#!/usr/bin/env python3
"""Monitor autovacuum on TimescaleDB catalog tables.
Writes Prometheus textfile: /tmp/pg_autovacuum_metrics.prom
Run via cron every 60s.
"""
import os, time, logging
from datetime import datetime, timezone

DB_URL = os.environ.get("DATABASE_URL", "postgresql://astrofin:astrofin@localhost:5432/astrofin?sslmode=disable")
OUTFILE = os.environ.get("PG_AUTOVACUUM_METRICS_FILE", "/tmp/pg_autovacuum_metrics.prom")
LOG_FILE = "/dev/shm/pg_autovacuum_monitor.log"

logging.basicConfig(filename=LOG_FILE, level=logging.WARNING,
                    format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

TABLES = [
    ("_timescaledb_catalog", "continuous_aggs_invalidation_threshold"),
    ("_timescaledb_catalog", "continuous_aggs_materialization_invalidation_log"),
    ("_timescaledb_catalog", "continuous_aggs_jobs_refresh_ranges"),
]

def collect():
    try:
        import psycopg2
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        metrics = []

        for schema, table in TABLES:
            cur.execute("""
                SELECT n_live_tup, n_dead_tup,
                       n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0) AS dead_ratio,
                       EXTRACT(EPOCH FROM (NOW() - COALESCE(last_autovacuum, last_vacuum, '1970-01-01'))) AS seconds_since_vacuum,
                       autovacuum_count
                       n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0) AS dead_ratio,
                       EXTRACT(EPOCH FROM (NOW() - COALESCE(last_autovacuum, last_vacuum, '1970-01-01'))) AS seconds_since_vacuum,
                       autovacuum_count
                FROM pg_stat_all_tables
                WHERE schemaname = %s AND relname = %s
            """, (schema, table))
            row = cur.fetchone()
            if row:
                live, dead, ratio, since_sec, av_count = row
                ratio_val = float(ratio or 0)
                since_val = float(since_sec or 0)
                labels = f'schema="{schema}",table="{table}"'
                metrics.append(f'pg_autovacuum_live_tuples{{{labels}}} {live or 0}')
                metrics.append(f'pg_autovacuum_dead_tuples{{{labels}}} {dead or 0}')
                metrics.append(f'pg_autovacuum_dead_ratio{{{labels}}} {ratio_val:.4f}')
                metrics.append(f'pg_autovacuum_seconds_since_last{{{labels}}} {since_val:.0f}')
                metrics.append(f'pg_autovacuum_run_count{{{labels}}} {av_count or 0}')

        # Overall health gauge: 1 = OK (all tables < 20% dead), 0 = WARNING
        cur.execute("""
            SELECT CASE WHEN MAX(
                n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0)
            ) > 0.2 THEN 0 ELSE 1 END AS health
            FROM pg_stat_all_tables
            WHERE (schemaname, relname) IN (
                ('_timescaledb_catalog', 'continuous_aggs_invalidation_threshold'),
                ('_timescaledb_catalog', 'continuous_aggs_materialization_invalidation_log'),
                ('_timescaledb_catalog', 'continuous_aggs_jobs_refresh_ranges')
            )
        """)
        health = cur.fetchone()
        metrics.append(f'pg_autovacuum_tsdb_catalog_health {health[0] if health else 0}')

        cur.close()
        conn.close()

        # Atomic write
        tmpfile = OUTFILE + ".tmp"
        with open(tmpfile, 'w') as f:
            f.write("# HELP pg_autovacuum_tsdb_catalog_health 1=OK 0=dead_tuples>20%\n")
            f.write("# TYPE pg_autovacuum_tsdb_catalog_health gauge\n")
            f.write("\n".join(metrics) + "\n")
        os.rename(tmpfile, OUTFILE)

    except Exception as e:
        log.error(f"Collection failed: {e}")
        # Write stale marker
        try:
            with open(OUTFILE + ".tmp", 'w') as f:
                f.write(f"pg_autovacuum_tsdb_catalog_health 0\n")
            os.rename(OUTFILE + ".tmp", OUTFILE)
        except:
            pass

if __name__ == "__main__":
    collect()
    print(f"✅ Metrics written to {OUTFILE}")
