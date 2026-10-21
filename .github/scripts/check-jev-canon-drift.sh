#!/usr/bin/env bash
# Guard: the ROMA groups mirrored into this repo must stay identical to the ROMA
# canon (roma-execution-bridge/deploy/monitoring/alert-rules-roma.yml):
# roma-jev-shadow, roma-critical, roma-warning, roma-billing.
#
# Both sides are canonicalised to JSON with sorted keys, so YAML comments and
# key order can never show up as drift. The single tolerated difference is the
# "Runbook:" line of annotations.description: prod carries the absolute GitHub
# URL, the canon keeps the repo-relative path.
#
# Exit codes: 0 match, 1 drift, 2 setup error (canon unreachable, group absent).
set -euo pipefail

CANON_URL="${JEV_CANON_URL:-https://raw.githubusercontent.com/mahaasur13-sys/roma-execution-bridge/master/deploy/monitoring/alert-rules-roma.yml}"
LOCAL_FILE="${1:-deploy/monitoring/alert_rules.yml}"
GROUP_LIST="${CANON_GROUPS:-roma-jev-shadow roma-critical roma-warning roma-billing}"
YQ="${YQ:-yq}"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

command -v "$YQ" >/dev/null 2>&1 || { echo "ERROR: yq not found (set YQ=)" >&2; exit 2; }
command -v jq >/dev/null 2>&1 || { echo "ERROR: jq not found" >&2; exit 2; }
[ -r "$LOCAL_FILE" ] || { echo "ERROR: $LOCAL_FILE not readable" >&2; exit 2; }

curl -fsSL "$CANON_URL" -o "$tmp/canon.yml" || {
  echo "ERROR: cannot fetch canon ($CANON_URL)" >&2
  exit 2
}

canonicalise() {
  "$YQ" -o=json ".groups | map(select(.name == \"$GROUP\")) | .[0]" "$1" \
    | jq -S 'walk(if type == "string"
              then split("\n") | map(select(test("^\\s*Runbook:") | not)) | join("\n")
              else . end)' > "$2"
}

rc=0
for GROUP in $GROUP_LIST; do
  canonicalise "$tmp/canon.yml" "$tmp/canon.json"
  canonicalise "$LOCAL_FILE" "$tmp/local.json"

  for side in canon local; do
    if [ "$(cat "$tmp/$side.json")" = "null" ] || [ ! -s "$tmp/$side.json" ]; then
      echo "ERROR: group '$GROUP' not found on the $side side" >&2
      exit 2
    fi
    if [ "$(jq '.rules | length' "$tmp/$side.json")" -eq 0 ]; then
      echo "ERROR: group '$GROUP' has no rules on the $side side" >&2
      exit 2
    fi
  done

  if diff -u --label "canon ($CANON_URL#$GROUP)" --label "local ($LOCAL_FILE#$GROUP)" \
       "$tmp/canon.json" "$tmp/local.json"; then
    echo "OK: '$GROUP' matches ROMA canon ($(jq '.rules | length' "$tmp/local.json") rules)"
  else
    echo "::error::'$GROUP' drifted from ROMA canon"
    rc=1
  fi
done

exit "$rc"
