"""
tools/migrate_postgres.py — Apply PostgreSQL migrations idempotently.

Walks migrations_postgres/*.sql in lexical order, applies each via asyncpg,
records success in `_schema_version`. Skips versions already applied.

Usage:
    export AFS_PG_DSN="postgresql://astrofin:<pass>@localhost:5432/astrofin"
    python tools/migrate_postgres.py                # apply all pending
    python tools/migrate_postgres.py --status       # show applied / pending
    python tools/migrate_postgres.py --version 9   # apply up to (and incl.) 9
    python tools/migrate_postgres.py --dry-run     # show plan, no DB writes

Dependencies:
    asyncpg >= 0.29  (added in this commit: pyproject.toml)
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import re
import sys
from pathlib import Path

import asyncpg

logger = logging.getLogger(__name__)
REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = REPO_ROOT / "migrations_postgres"
VERSION_RE = re.compile(r"^(\d{4})_.+\.sql$")


def split_sql_script(sql):
    """Split SQL script into statements (commas, comments, blanks)."""
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    stmts = []
    for raw in sql.split(";"):
        s = raw.strip()
        if s:
            stmts.append(s)
    return stmts


def discover_migrations() -> list[tuple[int, Path]]:
    """Return [(version, path), ...] sorted by version ascending."""
    out: list[tuple[int, Path]] = []
    for p in sorted(MIGRATIONS_DIR.glob("*.sql")):
        m = VERSION_RE.match(p.name)
        if m:
            out.append((int(m.group(1)), p))
    return out


async def get_applied_versions(conn: asyncpg.Connection) -> set[int]:
    """Read _schema_version. Returns empty set if table does not exist yet."""
    try:
        rows = await conn.fetch("SELECT version FROM _schema_version")
        return {r["version"] for r in rows}
    except asyncpg.UndefinedTableError:
        return set()


async def apply_one(conn: asyncpg.Connection, version: int, path: Path) -> None:
    """Run a single .sql file in a transaction. Skip if already applied."""
    sql = path.read_text(encoding="utf-8")
    logger.info("applying %s (%d bytes)", path.name, len(sql))
    # The migration file already does BEGIN/COMMIT, but asyncpg's `execute` runs
    # in autocommit. We wrap in an explicit transaction so a syntax error rolls
    # back cleanly without poisoning the connection.
    async with conn.transaction():
        statements = split_sql_script(sql)
        for stmt in statements:
            await conn.execute(stmt)
    logger.info("✅ %s applied", path.name)


async def run(args: argparse.Namespace) -> int:
    dsn = os.environ.get("AFS_PG_DSN")
    if not dsn:
        logger.error("AFS_PG_DSN env var is not set")
        return 2

    migrations = discover_migrations()
    if not migrations:
        logger.warning("no migrations found in %s", MIGRATIONS_DIR)
        return 0

    conn = await asyncpg.connect(dsn)
    try:
        applied = await get_applied_versions(conn)
        pending = [(v, p) for v, p in migrations if v not in applied]

        if args.status:
            print(f"Applied ({len(applied)}): {sorted(applied)}")
            print(f"Pending ({len(pending)}): {[v for v, _ in pending]}")
            return 0

        if args.dry_run:
            for v, p in pending:
                if args.version is None or v <= args.version:
                    print(f"  would apply {p.name}")
            return 0

        n_applied = 0
        for v, p in pending:
            if args.version is not None and v > args.version:
                break
            await apply_one(conn, v, p)
            n_applied += 1
        logger.info("Done. %d migration(s) applied.", n_applied)
        return 0
    finally:
        await conn.close()


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--status", action="store_true", help="show applied/pending and exit"
    )
    ap.add_argument(
        "--version", type=int, default=None, help="apply up to this version (inclusive)"
    )
    ap.add_argument("--dry-run", action="store_true", help="print plan, do not execute")
    return ap.parse_args()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    return asyncio.run(run(parse_args()))


if __name__ == "__main__":
    sys.exit(main())
