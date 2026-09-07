#!/usr/bin/env bash
# =============================================================================
# Prod Go gate — one-shot git-level production-readiness check.
#
# Orchestrates the already-green guards (no copy-paste of their logic) and adds
# the two gaps they don't cover: deploy.yml must not push :latest and must not
# use key-based cosign signing.
#
# Deterministic: pure grep / guard invocation. No network, no docker.
# This is the *git* gate. It does NOT mean "production ready" — operational
# No-Go items (external vault, real AWS S3, PITR on live pg_data, cosign on the
# alpine base stack, CodeRabbit App) remain (see docs/RUNBOOK.md §Prod Go gate).
# =============================================================================
set -euo pipefail

fail=0

run() {
  local label="$1"; shift
  if bash "$@" >/dev/null 2>&1; then
    echo "  OK   $label"
  else
    echo "  FAIL $label" >&2
    fail=1
  fi
}

echo "== Prod gate (git) =="

run "wal-g restore guard (no pg_ctl stop / backup-fetch PGDATA)" scripts/ci_validate_walg_restore_guard.sh
run "postgres-user guard (no POSTGRES_USER:-postgres)"         scripts/ci_validate_postgres_user_required.sh
run "image digests guard (python/uv FROM @sha256)"             scripts/ci_validate_image_digests.sh
run "metrics bind guard (BIND_ALL requires token)"             scripts/ci_validate_metrics_bind.sh
run "action pins guard (no floating @vN)"                      scripts/ci_validate_action_pins.sh

# --- Gaps not covered by the guards above -------------------------------
DEPLOY_YML=".github/workflows/deploy.yml"

# deploy.yml must not push :latest (actual tag, not a comment/placeholder).
if grep -vE '^[[:space:]]*#' "$DEPLOY_YML" | grep -nE ':latest([[:space:]]|$)'; then
  echo "::error:: deploy.yml must not push :latest" >&2
  fail=1
fi

# deploy.yml must be keyless (no cosign sign --key / COSIGN_PRIVATE_KEY).
if grep -vE '^[[:space:]]*#' "$DEPLOY_YML" | grep -nE 'cosign sign[[:space:]]+--key|secrets\.COSIGN_PRIVATE_KEY|COSIGN_PRIVATE_KEY:'; then
  echo "::error:: deploy.yml must not use key-based cosign signing" >&2
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo "prod gate FAILED" >&2
  exit 1
fi

echo "prod gate OK"
