#!/usr/bin/env bash
# CI guard: the metrics exporter must fail closed — METRICS_BIND_ALL=true without
# a token must raise SystemExit (never continue serving /metrics unauthenticated).
#
# Deterministic: pure grep. No network, no docker.

set -euo pipefail

SRC="${1:-orchestration/sentinel_v5.py}"
fail=0

if ! grep -qE 'raise SystemExit\(1\)' "$SRC"; then
  echo "::error:: $SRC must raise SystemExit when METRICS_BIND_ALL has no token" >&2
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo "metrics bind guard FAILED" >&2
  exit 1
fi

echo "metrics bind guard OK"
