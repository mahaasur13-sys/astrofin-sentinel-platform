#!/usr/bin/env bash
# CI guard: EMAIL_DOMAINS=* is forbidden outside dev/local oauth2 overlays.
#
# Fail closed (exit 1) if a deploy/docker/*oauth2* overlay sets a wildcard
# email domain (allows any authenticated Google/OIDC account) in a profile
# whose filename does not mark it as dev/local.
#
# Deterministic: pure grep. No network, no docker daemon.

set -euo pipefail

DIR="${1:-deploy/docker}"
fail=0

for f in "$DIR"/*oauth2*; do
  [ -e "$f" ] || continue
  if grep -qE 'EMAIL_DOMAINS[=:][[:space:]]*"?\*' "$f"; then
    base="$(basename "$f")"
    if ! [[ "$base" == *dev* || "$base" == *local* ]]; then
      echo "::error:: $f sets EMAIL_DOMAINS=* in a non-dev/local overlay" >&2
      fail=1
    fi
  fi
done

if [ "$fail" -ne 0 ]; then
  echo "oauth2 email domains guard FAILED" >&2
  exit 1
fi

echo "oauth2 email domains guard OK"
