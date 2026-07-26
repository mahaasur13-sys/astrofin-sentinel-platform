#!/bin/bash
# Pre-freeze checklist — run before tagging v1.0.0
set -euo pipefail

echo "=== AstroFin Sentinel — Pre-Freeze Checklist ==="
echo ""

echo "1. CI status (last 5 runs):"
gh run list --limit 5 --json conclusion,displayTitle | python3 -c "
import sys, json
runs = json.load(sys.stdin)
for r in runs:
    print(f'  {r[\"conclusion\"]:>9s} — {r[\"displayTitle\"][:75]}')
"
echo ""

echo "2. Bandit (MEDIUM+ only):"
bandit -r . -ll 2>&1 | tail -5 || true
echo ""

echo "3. Tests:"
python -m pytest tests/ -x --tb=short -q 2>&1 | tail -3
echo ""

echo "4. Docs:"
for f in docs/RELEASE_NOTES_v1.0.0.md docs/DEPLOYMENT.md docs/runbooks/ALERT_*.md; do
    [ -f "$f" ] && echo "  ✅ $f" || echo "  ❌ MISSING: $f"
done
echo ""

echo "5. Tags:"
git describe --tags --abbrev=0 2>/dev/null || echo "  No tags yet"
echo ""

echo "=== Checklist complete ==="
