#!/usr/bin/env bash
# CI guard: GitHub Actions must be pinned by commit SHA, not a floating tag.
#
# Fail closed (exit 1) if any .github/workflows/*.yml uses:
#   owner/repo@vN | @main | @master   (without a 40-hex SHA)
# Local uses (uses: ./) are allowed. Deterministic: pure grep. No network.

set -euo pipefail

fail=0

# Moving refs: @vN, @main, @master (no 40-hex commit SHA).
if grep -rnE 'uses:[[:space:]]*[^[:space:]#]+@(v[0-9]+|main|master)([[:space:]]|#|$)' \
    .github/workflows/ 2>/dev/null; then
  echo "::error:: floating action ref detected (must be owner/repo@<40hexSHA>)" >&2
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo "action pins guard FAILED" >&2
  exit 1
fi

echo "action pins guard OK"
