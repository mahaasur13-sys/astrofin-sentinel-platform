"""meta_rl/checkpoint.py — ATOM-META-RL-020: Checkpoint save/load."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CHECKPOINT_DIR = Path("data/meta_rl/checkpoints")
DEFAULT_TTL = timedelta(hours=24)


def _ensure_dir() -> Path:
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    return CHECKPOINT_DIR


def save_checkpoint(weights: dict[str, float], session_id: str, metadata: dict[str, Any] | None = None) -> Path:
    """Save agent weights as JSON checkpoint."""
    _ensure_dir()
    ts = datetime.now(timezone.utc).isoformat()
    payload = {
        "session_id": session_id,
        "timestamp": ts,
        "weights": weights,
        "metadata": metadata or {},
    }
    path = CHECKPOINT_DIR / f"checkpoint-{session_id}.json"
    path.write_text(json.dumps(payload, indent=2, default=str))
    logger.info("checkpoint saved: %s (%d agents)", path, len(weights))
    return path


def load_checkpoint(session_id: str = "latest") -> dict[str, Any] | None:
    """Load most recent checkpoint. Returns None if not found or stale."""
    _ensure_dir()
    if session_id == "latest":
        files = sorted(CHECKPOINT_DIR.glob("checkpoint-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            logger.warning("no checkpoints found")
            return None
        path = files[0]
    else:
        path = CHECKPOINT_DIR / f"checkpoint-{session_id}.json"
        if not path.exists():
            return None

    try:
        data = json.loads(path.read_text())
        ts = datetime.fromisoformat(data["timestamp"])
        if datetime.now(timezone.utc) - ts > DEFAULT_TTL:
            logger.warning("checkpoint %s is stale (>24h)", path.name)
        return data
    except Exception as e:
        logger.error("failed to load checkpoint %s: %s", path, e)
        return None


def is_checkpoint_fresh(max_age: timedelta = DEFAULT_TTL) -> bool:
    """Check if a recent checkpoint exists."""
    _ensure_dir()
    files = sorted(CHECKPOINT_DIR.glob("checkpoint-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return False
    mtime = datetime.fromtimestamp(files[0].stat().st_mtime, tz=timezone.utc)
    return datetime.now(timezone.utc) - mtime <= max_age
