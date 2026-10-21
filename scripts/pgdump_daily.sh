#!/usr/bin/env bash
# Daily logical backup of the AstroFin databases + state.json for the walg_backup_* gauges.
# Dump at start, then every day at 03:30Z; up to 3 attempts per day (retry in 30 min).
set -uo pipefail

OUT_DIR=/root/.sealed/pgdump
STATE="$OUT_DIR/state.json"
DBS="astrofin astrofin_db roma roma_test"
TARGET="today 03:30"
RETRY_S=1800
MAX_ATTEMPTS=3
KEEP_DAYS=14

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }
trap 'log "stopped (signal)"; exit 0' TERM INT
nap() { sleep "$1" & wait $!; }

write_state() {
  python3 - "$STATE" "$1" "$2" <<'PY'
import json, os, sys, time

path, result, nbytes = sys.argv[1], sys.argv[2], int(sys.argv[3])
try:
    prev = json.load(open(path))
except Exception:
    prev = {}
now = int(time.time())
state = {
    "last_success_ts": now if result == "ok" else prev.get("last_success_ts", 0),
    "last_attempt_ts": now,
    "last_result": result,
    "bytes": nbytes,
}
tmp = path + ".tmp"
with open(tmp, "w") as f:
    json.dump(state, f)
    f.flush()
    os.fsync(f.fileno())
os.replace(tmp, path)
PY
}

dump_all() {
  local stamp="$1" ok=1 total=0 db rc lines sz sha tmp dst
  for db in $DBS; do
    tmp="/tmp/pgdump_${db}.dump.tmp"
    dst="$OUT_DIR/${db}-${stamp}.dump"
    rm -f "$tmp"
    su postgres -c "pg_dump -Fc --no-owner -d $db -f $tmp" 2>"/tmp/pgdump_${db}.err"
    rc=$?
    if [ "$rc" -ne 0 ]; then
      log "db=$db pg_dump rc=$rc err=$(head -1 "/tmp/pgdump_${db}.err")"
      ok=0
      continue
    fi
    lines=$(pg_restore --list "$tmp" 2>/dev/null | wc -l)
    if [ "$lines" -eq 0 ]; then
      log "db=$db pg_restore --list rc=1 toc_lines=0"
      ok=0
      rm -f "$tmp"
      continue
    fi
    sz=$(stat -c %s "$tmp")
    sha=$(sha256sum "$tmp" | cut -d' ' -f1)
    mv "$tmp" "$dst"
    chmod 600 "$dst"
    chown root:root "$dst"
    total=$((total + sz))
    log "db=$db rc=0 toc_lines=$lines size=$sz sha256=$sha file=$(basename "$dst")"
  done
  if [ "$ok" -eq 1 ]; then
    write_state ok "$total"
    log "run result=ok bytes=$total state=written"
    return 0
  fi
  write_state fail "$total"
  log "run result=fail bytes=$total state=written"
  return 1
}

rotate() {
  local cutoff db newest f m
  cutoff=$(( $(date -u +%s) - KEEP_DAYS * 86400 ))
  for db in $DBS; do
    newest=$(ls -1t "$OUT_DIR/${db}-"*.dump 2>/dev/null | head -1)
    for f in "$OUT_DIR/${db}-"*.dump; do
      [ -e "$f" ] || continue
      [ "$f" = "$newest" ] && continue
      m=$(stat -c %Y "$f")
      if [ "$m" -lt "$cutoff" ]; then
        rm -f "$f"
        log "rotated $(basename "$f") age>$(( ( $(date -u +%s) - m ) / 86400 ))d"
      fi
    done
  done
}

next_run_sleep() {
  local now target diff
  now=$(date -u +%s)
  target=$(date -u -d "$TARGET" +%s)
  diff=$((target - now))
  [ "$diff" -le 0 ] && diff=$((diff + 86400))
  printf '%s' "$diff"
}

mkdir -p "$OUT_DIR"
chmod 700 "$OUT_DIR"
cd /tmp || exit 1

log "pgdump start: dbs=[$DBS] out=$OUT_DIR schedule=03:30Z retry=${RETRY_S}s max_attempts=$MAX_ATTEMPTS keep=${KEEP_DAYS}d"

while :; do
  attempts=0
  while :; do
    attempts=$((attempts + 1))
    if dump_all "$(date -u +%Y%m%dT%H%MZ)"; then
      rotate
      break
    fi
    if [ "$attempts" -ge "$MAX_ATTEMPTS" ]; then
      log "giving up after $attempts attempts, waiting for next 03:30Z"
      break
    fi
    log "retry after ${RETRY_S}s (attempt $attempts/$MAX_ATTEMPTS)"
    nap "$RETRY_S"
  done
  s=$(next_run_sleep)
  log "sleep ${s}s until next 03:30Z"
  nap "$s"
done
