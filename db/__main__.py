"""db/__main__.py — Entry point for: python -m db.init

ATOM-DB-MIGRATION-002
Usage:
    python -m db.init              # init schema
    python -m db.init --status     # show DB status
    python -m db.init --migrate    # migrate from SQLite
    python -m db.init --reset      # reset schema (DROP + CREATE)
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(prog="python -m db.init")
    parser.add_argument("--status", action="store_true", help="Show database status")
    parser.add_argument("--migrate", action="store_true", help="Migrate data from SQLite")
    parser.add_argument("--reset", action="store_true", help="Reset schema (DROP all tables)")
    parser.add_argument("--force", action="store_true", help="Force operation without confirmation")
    args = parser.parse_args()

    if args.status:
        _show_status()
    elif args.migrate:
        _migrate()
    elif args.reset:
        _reset(force=args.force)
    else:
        _init_schema()


def _show_status():
    from db import get_all_stats, get_db_status

    status = get_db_status()
    print(f"\n{'=' * 50}")
    print("  AstroFin Sentinel V5 — DB Status")
    print(f"{'=' * 50}")
    print(f"  Backend:     {status.get('backend', 'unknown')}")
    print(f"  PG Ready:    {status.get('postgres_available', False)}")
    print(f"  PG Version:  {status.get('postgres_version', 'N/A')}")
    print(f"  TimescaleDB: {status.get('timescaledb_available', False)}")
    print(f"  pgvector:    {status.get('pgvector_available', False)}")

    try:
        stats = get_all_stats()
        print("\n  Records:")
        for key, val in stats.items():
            if key != "db_pool":
                print(f"    {key}: {val}")
        pool = stats.get("db_pool", {})
        if isinstance(pool, dict):
            print("\n  Connection Pool:")
            for k, v in pool.items():
                print(f"    {k}: {v}")
    except Exception as e:
        print(f"\n  Stats error: {e}")

    print(f"\n{'=' * 50}\n")


def _init_schema():
    from db import init_db_if_needed

    print("Initializing database schema...")
    result = init_db_if_needed()

    if result.get("postgres_available"):
        print("  ✅ PostgreSQL available")
        print(f"  ✅ Tables created: {result.get('tables_created')}")
        print(f"  ✅ Backend: {result.get('backend', 'unknown')}")
    else:
        print("  ⚠️  PostgreSQL not available — using SQLite fallback")
        print(f"  ✅ Tables created: {result.get('tables_created', False)} (SQLite)")

    if result.get("error"):
        print(f"  ❌ Error: {result['error']}")
        sys.exit(1)
    else:
        print("\n✅ Database ready!")


def _migrate():
    print("Migrating data from SQLite to PostgreSQL...")
    try:
        from db.migrate_from_sqlite import migrate_all

        migrated = migrate_all()
        print(f"  ✅ Migrated {migrated.get('total', 0)} records total")
        for table, count in migrated.items():
            if table != "total":
                print(f"     {table}: {count}")
    except Exception as e:
        print(f"  ❌ Migration failed: {e}")
        sys.exit(1)


def _reset(force=False):
    from db import is_postgres_available

    if not is_postgres_available():
        print("❌ PostgreSQL not available. Cannot reset.")
        sys.exit(1)

    if not force:
        confirm = input("⚠️  This will DROP ALL tables. Are you sure? [y/N]: ")
        if confirm.lower() != "y":
            print("Aborted.")
            sys.exit(0)

    print("Resetting schema...")
    try:
        from db.session import get_engine

        engine = get_engine()
        with engine.connect() as conn:
            # Drop all TimescaleDB hypertables first
            conn.exec_driver_sql(
                """
                SELECT drop_chunks('_timescaledb_cache.background_job', older_than => NULL);
                DROP TABLE IF EXISTS sessions CASCADE;
                DROP TABLE IF EXISTS agent_signals CASCADE;
                DROP TABLE IF EXISTS agent_beliefs CASCADE;
                DROP TABLE IF EXISTS agent_belief_history CASCADE;
                DROP TABLE IF EXISTS agent_selection_log CASCADE;
                DROP TABLE IF EXISTS karl_decision_records CASCADE;
                DROP TABLE IF EXISTS oap_validation_history CASCADE;
                DROP TABLE IF EXISTS kpi_metrics CASCADE;
                DROP TABLE IF EXISTS reward_calibration CASCADE;
                DROP TABLE IF EXISTS backtest_runs CASCADE;
                DROP TABLE IF EXISTS rag_embeddings CASCADE;
                DROP TABLE IF EXISTS audit_log CASCADE;
                DROP TABLE IF EXISTS astro_positions CASCADE;
                DROP TABLE IF EXISTS karl_trajectories CASCADE;
                DROP TABLE IF EXISTS karl_trajectory_steps CASCADE;
            """
            )
        print("✅ Schema reset complete. Run without --reset to reinitialize.")
    except Exception as e:
        print(f"❌ Reset failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
