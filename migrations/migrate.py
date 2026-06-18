#!/usr/bin/env python3
"""
AstroFin Sentinel V5 — Schema Migration Runner
===============================================
Versioned SQL migrations for SQLite databases.

Usage:
    python migrations/migrate.py --help
    python migrations/migrate.py                  # run all pending migrations
    python migrations/migrate.py --status          # show current version
    python migrations/migrate.py --check           # exit 0 if up-to-date
    python migrations/migrate.py --plan            # show pending migrations
    python migrations/migrate.py --rollback 3     # rollback to version N
    python migrations/migrate.py --init-single core/history.db
                                              # bootstrap fresh DB with all migrations

Design:
    - Migrations are numbered SQL files in migrations/
    - Each DB has its own _schema_version table (multi-tenant)
    - Apply in version order; idempotent (INSERT OR IGNORE)
    - No down() needed — SQLite doesn't DROP COLUMN easily;
      instead we mark "archived" rows and add new columns in new migrations
    - Rollback = re-run from scratch for SQLite (pragmatic choice)
    - All DBs in scope: core/history.db, backtest/metrics_history.db
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
MIGRATIONS_DIR = PROJECT_ROOT / "migrations"
DBs = {
    "sessions": PROJECT_ROOT / "core" / "history.db",
    "backtest": PROJECT_ROOT / "backtest" / "metrics_history.db",
}

# ── Version table ────────────────────────────────────────────────────────────

_VERSION_TABLE = "_schema_version"
_VERSION_SQL = f"""CREATE TABLE IF NOT EXISTS {_VERSION_TABLE} (
    version    INTEGER PRIMARY KEY,
    applied_at TEXT    NOT NULL DEFAULT (datetime('now')),
    note       TEXT    NOT NULL DEFAULT ''
);"""

# ── Discovery ────────────────────────────────────────────────────────────────

RE_MIGRATION = re.compile(r"^(?P<ver>\d+)_(?P<name>.+?)\.sql$")


def discover_migrations() -> list[dict]:
    """Return sorted list of migration metadata."""
    migrations = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        m = RE_MIGRATION.match(path.name)
        if not m:
            continue
        migrations.append(
            {
                "version": int(m.group("ver")),
                "name": m.group("name"),
                "path": path,
            }
        )
    return migrations


# ── DB helpers ────────────────────────────────────────────────────────────────


def get_version(db_path: Path) -> int:
    """Current schema version for a DB, or 0 if never seeded."""
    if not db_path.exists():
        return 0
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(_VERSION_SQL)
        row = conn.execute(f"SELECT MAX(version) FROM {_VERSION_TABLE}").fetchone()
        return row[0] or 0
    finally:
        conn.close()


def get_all_versions(db_path: Path) -> list[int]:
    """All applied versions for a DB."""
    if not db_path.exists():
        return []
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(f"SELECT version FROM {_VERSION_TABLE} ORDER BY version").fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


def apply_migration(db_path: Path, migration: dict, simulate: bool = False) -> bool:
    """Apply a single migration. Returns True if successful."""
    sql = migration["path"].read_text()
    applied_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Extract embedded version insert (idempotent via OR IGNORE)
    # Remove the auto-insert so we can control it manually
    clean_sql = re.sub(
        r"INSERT\s+OR\s+IGNORE\s+INTO\s+_schema_version.*?;\s*",
        "",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if simulate:
        print(f"  [SIMULATE] Would apply: v{migration['version']} — {migration['name']}")
        return True

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(_VERSION_SQL)
        conn.execute("BEGIN")
        try:
            conn.executescript(clean_sql)
            conn.execute(
                f"INSERT OR IGNORE INTO {_VERSION_TABLE} (version, applied_at, note) VALUES (?, ?, ?)",
                (migration["version"], applied_at, migration["name"]),
            )
            conn.commit()
            print(f"  ✅ v{migration['version']} — {migration['name']}")
            return True
        except Exception:
            conn.rollback()
            raise
    finally:
        conn.close()


# ── CLI commands ──────────────────────────────────────────────────────────────


def cmd_status() -> None:
    print(f"\n📋 Schema version status\n{'─' * 50}")
    for name, path in DBs.items():
        version = get_version(path)
        applied = get_all_versions(path)
        status_icon = "🟢" if version == _latest() else "🟡"
        print(f"  {status_icon} {name}: v{version} / {_latest()} applied={applied or '—'}")


def cmd_plan() -> None:
    print(f"\n📋 Migration plan\n{'─' * 50}")
    for name, path in DBs.items():
        cur = get_version(path)
        pending = [m for m in discover_migrations() if m["version"] > cur]
        print(f"\n  {name} ({path}):")
        if not pending:
            print(f"    ✅ Already up-to-date (v{cur:d})")
        else:
            for m in pending:
                print(f"    → v{m['version']} — {m['name']}")


def cmd_check() -> None:
    """Exit 0 if all DBs are at latest version."""
    all_ok = True
    for name, path in DBs.items():
        cur = get_version(path)
        if cur < _latest():
            all_ok = False
            print(f"❌ {name} is v{cur}, expected v{_latest()}", file=sys.stderr)
    sys.exit(0 if all_ok else 1)


def cmd_migrate(simulate: bool = False) -> None:
    print(f"\n🔄 Running migrations (simulate={simulate})\n{'─' * 50}")
    for name, path in DBs.items():
        cur = get_version(path)
        pending = [m for m in discover_migrations() if m["version"] > cur]
        print(f"\n  DB: {name} ({path}):")
        if not path.exists():
            print(f"    ⚠️  Database does not exist: {path}")
            if not simulate:
                path.parent.mkdir(parents=True, exist_ok=True)
                print(f"    → Created directory: {path.parent}")
        if not pending:
            print(f"    ✅ Already up-to-date (v{cur})")
            continue
        for m in pending:
            ok = apply_migration(path, m, simulate=simulate)
            if not ok:
                print(f"    ❌ Failed: v{m['version']}")
                sys.exit(1)
    print(f"\n{'─' * 50}")
    print("✅ Migration complete.")


def cmd_init_single(db_key: str) -> None:
    """Bootstrap a fresh DB with all migrations."""
    if db_key not in DBs:
        print(f"Unknown DB: {db_key}. Options: {list(DBs.keys())}", file=sys.stderr)
        sys.exit(1)
    path = DBs[db_key]
    path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n🆕 Initializing {db_key} at {path}\n{'─' * 50}")
    cur = get_version(path)
    if cur > 0:
        print(f"  ⚠️  DB already has schema v{cur}. Re-initialising from scratch.")
        backup = path.with_suffix(".db.backup_{}".format(datetime.now().strftime("%Y%m%d%H%M%S")))
        path.rename(backup)
        print(f"  → Renamed old DB to {backup}")

    # Touch the file so sqlite3 connects
    path.touch()
    for m in discover_migrations():
        apply_migration(path, m)
    print(f"\n{'─' * 50}")
    print(f"✅ {db_key} initialised at v{_latest()}.")


def cmd_rollback(version: int) -> None:
    """
    Rollback: recreate DB from scratch at specified version.
    This is pragmatic for SQLite — no DROP COLUMN support.
    """
    print(f"\n⚠️  Rollback to v{version} for SQLite = re-bootstrap from v0 + apply through v{version}")
    for name, path in DBs.items():
        cur = get_version(path)
        if cur <= version:
            print(f"  {name}: already at v{cur} — nothing to do")
            continue
        # Backup
        backup = path.with_suffix(f".rollback_v{version}_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        if path.exists():
            path.rename(backup)
            print(f"  → Backed up {name} to {backup}")
        path.touch()
        for m in discover_migrations():
            if m["version"] <= version:
                apply_migration(path, m)
    print(f"\n✅ Rollback complete to v{version}.")


# ── Helpers ───────────────────────────────────────────────────────────────────


def _latest() -> int:
    migrations = discover_migrations()
    return max((m["version"] for m in migrations), default=0)


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="AstroFin Sentinel V5 — Schema Migration Runner")
    parser.add_argument("--status", action="store_true", help="Show current schema version per DB")
    parser.add_argument("--check", action="store_true", help="Exit 0 if all DBs are current")
    parser.add_argument("--plan", action="store_true", help="Show pending migrations")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without doing it",
    )
    parser.add_argument(
        "--init-single",
        metavar="DB",
        help="Bootstrap a single DB (sessions|backtest) from scratch",
    )
    parser.add_argument(
        "--rollback",
        type=int,
        metavar="N",
        help="Rollback all DBs to version N (re-applies <=N)",
    )

    args = parser.parse_args()

    if args.status:
        cmd_status()
    elif args.check:
        cmd_check()
    elif args.plan:
        cmd_plan()
    elif args.init_single:
        cmd_init_single(args.init_single)
    elif args.rollback is not None:
        cmd_rollback(args.rollback)
    else:
        cmd_migrate(simulate=args.dry_run)


if __name__ == "__main__":
    main()
