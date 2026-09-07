#!/usr/bin/env bash
# CI guard: WAL-G backup config must not fake a live S3/encryption setup.
#
# Fail closed (exit 1) if:
#   - the live deploy/wal-g/wal-g.env is committed (only the .example template
#     may be in git), or
#   - any committed file under deploy/wal-g/ has a literal secret/endpoint:
#       minioadmin, AWS_ACCESS_KEY_ID=/AWS_SECRET_ACCESS_KEY= (non-placeholder),
#       WALG_S3_PREFIX=s3://, or WALG_LIBSODIUM_KEY=<literal>, or
#   - docs/RUNBOOK.md claims WAL-G is enabled when it is out of compose.
#
# Deterministic: grep + git ls-files. No network, no docker daemon.

set -euo pipefail

DIR="${1:-deploy/wal-g}"
fail=0

# 1. The live env must not be committed — only the .example template.
if git ls-files -- "$DIR/wal-g.env" | grep -q .; then
  echo "::error:: $DIR/wal-g.env must not be committed (use wal-g.env.example)" >&2
  fail=1
fi

# 2. No committed file under DIR may carry a literal secret/endpoint
#    (must be ${VAR:?}/file form, never a literal key or credential).
for f in $(git ls-files -- "$DIR"); do
  if grep -n 'minioadmin' "$f"; then
    echo "::error:: $f has a literal 'minioadmin' credential" >&2
    fail=1
  fi
  if grep -nE '^[[:space:]]*AWS_SECRET_ACCESS_KEY=[^$#[:space:]]' "$f"; then
    echo "::error:: $f has a literal AWS_SECRET_ACCESS_KEY (must be \${VAR:?})" >&2
    fail=1
  fi
  if grep -nE '^[[:space:]]*AWS_ACCESS_KEY_ID=[^$#[:space:]]' "$f"; then
    echo "::error:: $f has a literal AWS_ACCESS_KEY_ID (must be \${VAR:?})" >&2
    fail=1
  fi
  if grep -nE '^[[:space:]]*WALG_S3_PREFIX=s3://' "$f"; then
    echo "::error:: $f has an uncommented literal WALG_S3_PREFIX=s3://" >&2
    fail=1
  fi
  if grep -nE '^[[:space:]]*WALG_LIBSODIUM_KEY=[^$#[:space:]]' "$f"; then
    echo "::error:: $f has an uncommented literal WALG_LIBSODIUM_KEY" >&2
    fail=1
  fi
done

# 3. RUNBOOK must not claim WAL-G is enabled while it is out of compose.
if grep -nE 'WAL-G (is )?(enabled|active|configured|running)' docs/RUNBOOK.md 2>/dev/null; then
  echo "::error:: docs/RUNBOOK.md must not claim WAL-G is enabled (out of compose)" >&2
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo "wal-g config guard FAILED" >&2
  exit 1
fi

echo "wal-g config guard OK"
