#!/usr/bin/env bash
# scripts/hotfix.sh — fast-track hotfix flow
# Usage: ./scripts/hotfix.sh <name> [--no-tests]
#
# Does:
#   1. Create hotfix/<name> from main
#   2. Run minimal sanity check
#   3. Push branch
#   4. Open PR via gh (if available)
#
# This is intentionally lean: hotfixes skip architecture linter
# and full tests; the PR CI re-runs everything before merge.

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <name> [--no-tests]" >&2
    echo "  <name> — kebab-case short id (e.g. agent-leak, twap-div0)" >&2
    exit 64
fi

NAME="$1"
SKIP_TESTS="false"
if [[ "${2:-}" == "--no-tests" ]]; then SKIP_TESTS="true"; fi

if ! [[ "$NAME" =~ ^[a-z0-9][a-z0-9-]{1,40}$ ]]; then
    echo "::error::Invalid name: must be kebab-case, 2-41 chars" >&2
    exit 64
fi

BRANCH="hotfix/${NAME}"
echo "Hotfix branch: $BRANCH"

# 1. Update main and create branch
git fetch origin main:main
git switch main
git pull --ff-only origin main || true
git switch -c "$BRANCH"

# 2. Minimal sanity check (skip on --no-tests)
if ! $SKIP_TESTS; then
    echo "--- Smoke import check ---"
    python3 -c "import orchestration.sentinel_v5" 2>&1 | tail -3 || true
fi

# 3. Push branch
git push -u origin "$BRANCH"

# 4. Open PR via gh
if command -v gh >/dev/null; then
    echo "--- Opening PR via gh ---"
    gh pr create \
        --base main \
        --head "$BRANCH" \
        --title "hotfix(${NAME}): <fill me in>" \
        --body "## Hotfix
- Issue:
- Root cause:
- Fix:
- Risk: low (minimal change)
- Tests:

## Checklist
- [ ] Reverted/cherry-picked from main
- [ ] Local smoke test passed
- [ ] Will deploy to staging first" || true
else
    echo "gh CLI not installed; create PR manually at:"
    echo "  https://github.com/\$OWNER/\$REPO/compare/main...${BRANCH}"
fi

echo ""
echo "Hotfix branch $BRANCH is ready."
