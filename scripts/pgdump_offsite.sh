#!/usr/bin/env bash
# Offsite copy of the newest pg_dump + state.json to Backblaze B2 (S3 API).
# Credentials come from a 600 root file via env only — never argv, never logs.
set -euo pipefail

CREDS=${B2_CREDS:-/root/.sealed/b2-pgdump.env}
OUT_DIR=${PGDUMP_DIR:-/root/.sealed/pgdump}
STATE="$OUT_DIR/offsite_state.json"
LOCK_FILE=${OFFSITE_LOCK:-/run/pgdump_offsite.lock}
BUCKET=${B2_BUCKET:-astrofin-mx13}
ENDPOINT=${B2_ENDPOINT:-https://s3.us-east-005.backblazeb2.com}
REGION=${B2_REGION:-us-east-005}
RCLONE=${RCLONE:-/usr/local/bin/rclone}
PREFIX=pgdump

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }

write_state() {
  python3 - "$STATE" "$1" "$2" "$3" <<'PY'
import json, os, sys, time

path, result, nbytes, obj = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
try:
    prev = json.load(open(path))
except Exception:
    prev = {}
now = int(time.time())
state = {
    "last_attempt_ts": now,
    "last_success_ts": now if result == "ok" else prev.get("last_success_ts", 0),
    "last_result": result,
    "bytes": nbytes,
    "object": obj,
}
tmp = path + ".tmp"
with open(tmp, "w") as f:
    json.dump(state, f)
    f.flush()
    os.fsync(f.fileno())
os.replace(tmp, path)
PY
  chmod 600 "$STATE" 2>/dev/null || true
}

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  log "another offsite run holds the lock — skipping"
  exit 0
fi

if [ ! -r "$CREDS" ]; then
  log "creds file not readable: $CREDS"
  write_state fail 0 ""
  exit 1
fi
set -a
# shellcheck disable=SC1090
. "$CREDS"
set +a
export RCLONE_CONFIG_B2_TYPE=s3 \
  RCLONE_CONFIG_B2_PROVIDER=Other \
  RCLONE_CONFIG_B2_ENDPOINT="$ENDPOINT" \
  RCLONE_CONFIG_B2_REGION="$REGION" \
  RCLONE_CONFIG_B2_ACCESS_KEY_ID="$B2_KEY_ID" \
  RCLONE_CONFIG_B2_SECRET_ACCESS_KEY="$B2_APP_KEY" \
  RCLONE_CONFIG_B2_NO_CHECK_BUCKET=true

dump=$(ls -1t "$OUT_DIR"/roma-*.dump 2>/dev/null | head -1 || true)
if [ -z "$dump" ]; then
  log "no roma-*.dump in $OUT_DIR"
  write_state fail 0 ""
  exit 1
fi

ym=$(date -u +%Y/%m)
key="$PREFIX/$ym/$(basename "$dump")"
key_state="$PREFIX/$ym/state.json"
local_sha=$(sha256sum "$dump" | cut -d' ' -f1)
local_size=$(stat -c %s "$dump")

log "offsite start file=$(basename "$dump") size=$local_size sha256=$local_sha target=b2:$BUCKET/$key"

upload() {
  "$RCLONE" copyto --checksum --stats 0 --log-level ERROR "$dump" "b2:$BUCKET/$key"
  "$RCLONE" copyto --checksum --stats 0 --log-level ERROR "$OUT_DIR/state.json" "b2:$BUCKET/$key_state"
}
if ! upload; then
  log "result=fail stage=upload file=$(basename "$dump")"
  write_state fail "$local_size" "$key"
  exit 1
fi

remote_size=$("$RCLONE" lsjson "b2:$BUCKET/$key" 2>/dev/null | python3 -c 'import json,sys; d=json.load(sys.stdin); d=d if isinstance(d,list) else [d]; print(d[0]["Size"] if d else "")' || true)
remote_sha=$("$RCLONE" cat "b2:$BUCKET/$key" 2>/dev/null | sha256sum | cut -d' ' -f1 || true)

if [ "$remote_size" != "$local_size" ] || [ "$remote_sha" != "$local_sha" ]; then
  log "result=fail stage=verify remote_size=$remote_size remote_sha256=$remote_sha local_size=$local_size local_sha256=$local_sha"
  write_state fail "$local_size" "$key"
  exit 1
fi

write_state ok "$local_size" "$key"
log "result=ok file=$(basename "$dump") bytes=$local_size sha256=$local_sha object=b2:$BUCKET/$key state_object=b2:$BUCKET/$key_state"
