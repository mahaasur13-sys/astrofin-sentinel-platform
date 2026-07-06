#!/usr/bin/env bash
# gh-auth-fix.sh — PAT-based GitHub auth fix (non-interactive, deterministic)
# Usage: GITHUB_TOKEN=ghp_xxx ./gh-auth-fix.sh

set -euo pipefail

# ─── Guard ────────────────────────────────────────────────────────────────────
if [[ -z "${GITHUB_TOKEN:-}" ]]; then
    echo "ERROR: GITHUB_TOKEN env var not set"
    echo "Generate a PAT at: https://github.com/settings/tokens"
    echo "Required scopes: repo, workflow, read:org"
    echo ""
    echo "  export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    exit 1
fi

# ─── Logout old OAuth ─────────────────────────────────────────────────────────
echo "==> Logging out existing GitHub auth..."
gh auth logout --hostname github.com --yes 2>/dev/null || true
rm -rf ~/.config/gh/hosts.yml

# ─── Login with PAT ───────────────────────────────────────────────────────────
echo "==> Logging in with PAT..."
echo "$GITHUB_TOKEN" | gh auth login --hostname github.com --with-token

# ─── Verify scopes ───────────────────────────────────────────────────────────
echo "==> Verifying scopes..."
STATUS=$(gh auth status 2>&1)
echo "$STATUS"

if ! echo "$STATUS" | grep -q "workflow"; then
    echo ""
    echo "ERROR: 'workflow' scope MISSING"
    echo "Your PAT needs 'repo' and 'workflow' scopes."
    echo "Regenerate at: https://github.com/settings/tokens"
    echo "  → Fine-grained tokens → Generate new token (classic)"
    echo "  → Scopes: repo (full), workflow (full)"
    exit 1
fi

echo ""
echo "✓ Auth valid with workflow scope"

# ─── Restore workflow (if present) ───────────────────────────────────────────
WF_SRC="/tmp/ci.yml"
WF_DST=".github/workflows/ci.yml"

if [[ -f "$WF_SRC" ]]; then
    echo "==> Restoring workflow..."
    mkdir -p .github/workflows
    cp "$WF_SRC" "$WF_DST"
    git add "$WF_DST"
    git commit -m "restore: CI workflow after PAT auth fix" --allow-empty
    echo "✓ Workflow restored"
fi

echo ""
echo "==> Ready to push. Run: git push origin clean-main"
