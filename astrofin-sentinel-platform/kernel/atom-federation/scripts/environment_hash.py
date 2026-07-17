#!/usr/bin/env python3
"""
environment_hash.py — atom-federation-os v9.0+P0.3
Deterministic environment pinning and hash computation.

Generates a cryptographically binding hash of:
  - Python version
  - Platform
  - pip freeze output
  - PYTHONHASHSEED
  - PYTHONPATH
  - locked file hashes

Usage:
  python scripts/environment_hash.py --save    # generate + save to env_hash.json
  python scripts/environment_hash.py           # print current hash
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import platform
import subprocess
import sys

# ── Constants ───────────────────────────────────────────────────────────────────

REPO_ROOT = pathlib.Path(__file__).parent.parent.resolve()
LOCK_FILE = REPO_ROOT / "requirements.lock"
PYTHON_VERSION_FILE = REPO_ROOT / ".python-version"
ENV_HASH_FILE = REPO_ROOT / "formal_model" / "env_hash.json"
SYSTEM_SNAPSHOT_FILE = REPO_ROOT / "formal_model" / "system_snapshot.json"

REQUIRED_SEED = "0"
REQUIRED_PYTHON = "3.12.1"

# ── Core hash functions ─────────────────────────────────────────────────────────

def get_pip_freeze() -> str:
    """Get deterministic pip freeze output."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "freeze", "--all"],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "PIP_VERBOSITY": "quiet"},
    )
    # Filter to only meaningful packages (not pip/setuptools wheel)
    lines = [
        l.strip()
        for l in result.stdout.strip().split("\n")
        if l and not l.startswith(("pip==", "setuptools==", "wheel==", "_="))
    ]
    return "\n".join(sorted(lines))


def get_lock_file_hash() -> str:
    """Hash of requirements.lock (captures dependency versions)."""
    if not LOCK_FILE.exists():
        return "NO_LOCK_FILE"
    content = LOCK_FILE.read_text()
    # Normalize whitespace for determinism
    lines = [l.strip() for l in content.split("\n")]
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def compute_env_hash() -> str:
    """
    Compute the full environment hash.

    Binds together:
      - Python version + platform
      - pip freeze (deterministic, sorted)
      - locked file hash
      - PYTHONHASHSEED
      - PYTHONPATH
    """
    components: dict[str, str] = {
        "python_version": sys.version.split()[0],
        "python_platform": platform.platform(),
        "python_implementation": platform.python_implementation(),
        "python_hash_seed": os.environ.get("PYTHONHASHSEED", ""),
        "pythonpath": os.environ.get("PYTHONPATH", ""),
        "pip_freeze": get_pip_freeze(),
        "lock_file_hash": get_lock_file_hash(),
        "repo_root": str(REPO_ROOT),
    }

    # Canonical serialization for determinism
    canonical = json.dumps(components, sort_keys=True, separators=(",", ":"))
    full_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    return full_hash


def get_locked_python_version() -> str:
    """Read locked Python version from .python-version."""
    if PYTHON_VERSION_FILE.exists():
        return PYTHON_VERSION_FILE.read_text().strip()
    return REQUIRED_PYTHON  # fallback to required


def validate_environment() -> tuple[bool, str]:
    """
    Validate current environment against locked requirements.

    Returns (is_valid, error_message).
    """
    # Check Python version
    locked_py = get_locked_python_version()
    current_py = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if current_py != locked_py:
        return False, (
            f"Python version mismatch: locked={locked_py} current={current_py}. "
            f"Run: bash scripts/bootstrap_env.sh"
        )

    # Check PYTHONHASHSEED
    seed = os.environ.get("PYTHONHASHSEED", "")
    if seed != REQUIRED_SEED:
        return False, (
            f"PYTHONHASHSEED={seed} (expected {REQUIRED_SEED}). "
            f"Run: bash scripts/bootstrap_env.sh"
        )

    # Check PYTHONPATH
    pypath = os.environ.get("PYTHONPATH", "")
    if str(REPO_ROOT) not in pypath:
        return False, (
            "PYTHONPATH does not contain repo root. "
            "Run: bash scripts/bootstrap_env.sh"
        )

    return True, "OK"


def save_env_hash() -> str:
    """Compute and save env hash to formal_model/env_hash.json."""
    env_hash = compute_env_hash()
    locked_py = get_locked_python_version()

    data = {
        "version": "9.0+P0.3",
        "generated_at": f"{__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}",
        "python_version_locked": locked_py,
        "python_version_current": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": platform.platform(),
        "env_hash": env_hash,
        "pip_hash": hashlib.sha256(get_pip_freeze().encode()).hexdigest(),
        "lock_hash": get_lock_file_hash(),
        "pythonhashseed": os.environ.get("PYTHONHASHSEED", ""),
        "pythonpath": str(REPO_ROOT),
    }

    ENV_HASH_FILE.parent.mkdir(parents=True, exist_ok=True)
    ENV_HASH_FILE.write_text(json.dumps(data, indent=2, sort_keys=True))

    return env_hash


def update_system_snapshot() -> None:
    """Bind env_hash to the existing system_snapshot.json."""
    env_hash = compute_env_hash()

    if SYSTEM_SNAPSHOT_FILE.exists():
        snap = json.loads(SYSTEM_SNAPSHOT_FILE.read_text())
    else:
        snap = {}

    # Bind env to all existing hashes
    snap["env_hash"] = env_hash
    snap["env_version"] = "9.0+P0.3"

    SYSTEM_SNAPSHOT_FILE.write_text(json.dumps(snap, indent=2, sort_keys=True))


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Atom Federation OS environment hash")
    parser.add_argument(
        "--save", action="store_true",
        help="Save env hash to formal_model/env_hash.json and bind to system_snapshot.json"
    )
    parser.add_argument(
        "--output", choices=["hash", "json", "save"],
        default="hash",
        help="Output format: 'hash' (just the hash), 'json' (full report), 'save' (= --save)"
    )

    args = parser.parse_args()

    if args.output == "save" or args.save:
        env_hash = save_env_hash()
        update_system_snapshot()
        print(f"env_hash={env_hash}")
        print(f"Saved to: {ENV_HASH_FILE}")
        return 0

    if args.output == "json":
        valid, err = validate_environment()
        data = {
            "env_hash": compute_env_hash(),
            "python_version_locked": get_locked_python_version(),
            "python_version_current": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": platform.platform(),
            "valid": valid,
            "error": err if not valid else None,
        }
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0 if valid else 1

    # Default: just the hash
    print(compute_env_hash())
    return 0


if __name__ == "__main__":
    sys.exit(main())
