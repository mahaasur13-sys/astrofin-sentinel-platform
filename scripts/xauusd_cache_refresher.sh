#!/usr/bin/env bash
# Keeps backtest/data_cache/XAUUSD_4h.json fresh: one fetch at start, then at each 4h UTC boundary + 2 min.
set -uo pipefail

WORKDIR=/home/workspace
FETCH="$WORKDIR/scripts/fetch_xauusd_4h.py"
OUT="$WORKDIR/backtest/data_cache/XAUUSD_4h.json"
BOUNDARY_S=14400
OFFSET_S=120
RETRY_S=600
MAX_ATTEMPTS=6

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }

trap 'log "stopped (signal)"; exit 0' TERM INT

nap() { sleep "$1" & wait $!; }

fetch_once() {
  local out rc line bars last
  out=$(python3 "$FETCH" --out "$OUT" 2>&1); rc=$?
  line=$(printf '%s\n' "$out" | head -1)
  bars="${line#*bars=}"; bars="${bars%% *}"
  last="${line##*last=}"
  log "fetch rc=$rc bars=${bars:-?} last_bar=${last:-?}"
  [ "$rc" -ne 0 ] && printf '%s\n' "$out" >&2
  return "$rc"
}

log "refresher start: out=$OUT boundary=4h+${OFFSET_S}s retry=${RETRY_S}s max_attempts=$MAX_ATTEMPTS"

while :; do
  n=0
  until fetch_once; do
    n=$((n + 1))
    if [ "$n" -ge "$MAX_ATTEMPTS" ]; then
      log "giving up after $n attempts, waiting for next boundary"
      break
    fi
    log "retry $n/$MAX_ATTEMPTS in ${RETRY_S}s"
    nap "$RETRY_S"
  done
  s=$(( BOUNDARY_S - $(date -u +%s) % BOUNDARY_S + OFFSET_S ))
  log "sleep ${s}s until next 4h boundary +2min"
  nap "$s"
done
