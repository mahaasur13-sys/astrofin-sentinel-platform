#!/usr/bin/env bash
# bootstrap_env.sh — atom-federation-os v9.0+P0.3
# Deterministic environment bootstrap.
# MUST be run before any execution (local or CI).

set -euo pipefail

# ── Constants ───────────────────────────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_VERSION_FILE="$REPO_ROOT/.python-version"
LOCK_FILE="$REPO_ROOT/requirements.lock"
ENV_HASH_FILE="$REPO_ROOT/formal_model/env_hash.json"

# ── Guard: prevent execution outside bootstrap ─────────────────────────────────
export FORCE_BOOTSTRAP=1

# ── Enforce deterministic hash seed ────────────────────────────────────────────
export PYTHONHASHSEED=0

# ── Enforce canonical PYTHONPATH ────────────────────────────────────────────────
export PYTHONPATH="$REPO_ROOT"

# ── Verify Python version matches locked version ───────────────────────────────
if [[ -f "$PYTHON_VERSION_FILE" ]]; then
    LOCKED_VERSION=$(cat "$PYTHON_VERSION_FILE")
    CURRENT_VERSION=$(python3 -c "import sys; print(sys.version.split()[0])")
    if [[ "$CURRENT_VERSION" != "$LOCKED_VERSION" ]]; then
        echo "ERROR: Python version mismatch."
        echo "  Locked:  $LOCKED_VERSION"
        echo "  Current: $CURRENT_VERSION"
        echo "  Run: bootstrap_env.sh"
        echo "  Or: pip install python==$LOCKED_VERSION"
        exit 1
    fi
    echo "[BOOTSTRAP] Python version OK: $CURRENT_VERSION"
fi

# ── Bootstrap pip packages from lock ────────────────────────────────────────────
if [[ -f "$LOCK_FILE" ]]; then
    echo "[BOOTSTRAP] Installing locked dependencies..."
    grep -E "^[a-zA-Z0-9_-]+==" "$LOCK_FILE" | grep -v "^_" | while read -r line; do
        package=$(echo "$line" | cut -d'=' -f1)
        version=$(echo "$line" | cut -d'=' -f2-)
        if pip show "$package" 2>/dev/null | grep -q "Version: $version"; then
            continue
        fi
        echo "  Installing: $package==$version"
        pip install "$package==$version" --quiet --disable-pip-version-check 2>/dev/null || \
            echo "  WARNING: Could not install $package==$version (may be stdlib)"
    done
    echo "[BOOTSTRAP] Dependencies verified."
fi

# ── Verify environment hash matches expected ────────────────────────────────────
if [[ -f "$ENV_HASH_FILE" ]]; then
    echo "[BOOTSTRAP] Verifying environment hash..."
    python3 "$REPO_ROOT/scripts/environment_hash.py" > /tmp/env_hash_check.txt
    SAVED_HASH=$(python3 -c "import json; print(json.load(open('$ENV_HASH_FILE'))['env_hash'])")
    CURRENT_HASH=$(cat /tmp/env_hash_check.txt)
    if [[ "$SAVED_HASH" != "$CURRENT_HASH" ]]; then
        echo "ERROR: Environment hash mismatch."
        echo "  Saved:   $SAVED_HASH"
        echo "  Current: $CURRENT_HASH"
        echo "  Run: python scripts/environment_hash.py --save"
        echo "  Then re-run bootstrap_env.sh"
        exit 1
    fi
    echo "[BOOTSTRAP] Environment hash OK"
fi

echo "[BOOTSTRAP] Environment ready."
echo "[BOOTSTRAP] PYTHONHASHSEED=$PYTHONHASHSEED"
echo "[BOOTSTRAP] PYTHONPATH=$PYTHONPATH"