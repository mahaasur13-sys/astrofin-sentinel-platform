#!/usr/bin/env bash
# CI guard for the fail-closed Postgres data-plane (audit P0).
#
# Fail closed (exit 1) if any runtime path reintroduces a silent SQLite
# fallback: the "falling back to SQLite" log must only exist in db/session.py,
# gated by allow_sqlite_fallback(), and logged at ERROR (never warning).
# is_postgres_available() must be defined exactly once (a real SELECT 1 check,
# not a weak engine-is-not-None check).
#
# Deterministic: pure grep. No network, no docker daemon.

set -euo pipefail

DIR="${1:-db}"
fail=0

# 1. The only runtime fallback string must live in db/session.py.
if grep -rn "falling back to SQLite" --include="*.py" \
    db core orchestration agents knowledge 2>/dev/null \
    | grep -v '^db/session.py:'; then
  echo "::error:: 'falling back to SQLite' found in runtime outside db/session.py" >&2
  fail=1
fi

# 2. The fallback must be gated by allow_sqlite_fallback().
if ! grep -qE 'sqlite_session_factory.*and allow_sqlite_fallback\(\)' "$DIR/session.py"; then
  echo "::error:: SQLite fallback is not gated by allow_sqlite_fallback()" >&2
  fail=1
fi

# 3. The fallback must log at ERROR, not WARNING.
if grep -qE 'logger\.warning\([^)]*falling back to SQLite' "$DIR/session.py"; then
  echo "::error:: SQLite fallback must log at ERROR (not warning)" >&2
  fail=1
fi
if ! grep -qE 'logger\.error\([^)]*falling back to SQLite' "$DIR/session.py"; then
  echo "::error:: SQLite fallback must log at ERROR" >&2
  fail=1
fi

# 4. Single is_postgres_available() definition (P0 duplicate removed).
count=$(grep -cE '^def is_postgres_available' "$DIR/session.py" || true)
if [ "$count" -ne 1 ]; then
  echo "::error:: is_postgres_available must be defined exactly once (got $count)" >&2
  fail=1
fi

# 5. allow_sqlite_fallback must be restricted to dev/test + explicit flag.
if ! grep -q 'ALLOW_SQLITE_FALLBACK' "$DIR/session.py"; then
  echo "::error:: ALLOW_SQLITE_FALLBACK gate missing" >&2
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo "DB fail-closed guard FAILED" >&2
  exit 1
fi

echo "DB fail-closed guard OK"
