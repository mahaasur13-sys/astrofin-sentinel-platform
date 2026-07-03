"""Append-only JSONL audit log (P1-13).

Writes one JSON object per line to ``logs/audit.jsonl`` (path overridable
via ``AUDIT_LOG_FILE`` env var). Each record carries:

  - ts:      UTC ISO8601 timestamp
  - event:   short event name (e.g. "auth.login.success")
  - actor:   subject claim from JWT, or "-" for anonymous events
  - ip:      client IP (when available)
  - method:  HTTP method (for HTTP-scoped events)
  - path:    HTTP path
  - status:  HTTP status (or "ok"/"denied" for non-HTTP)
  - detail:  event-specific dict (redact secrets before passing!)

The writer is thread-safe and process-safe at the append level (Python
opens with O_APPEND, the kernel guarantees atomicity for writes
<= PIPE_BUF; in practice every audit record is well under that).
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

_DEFAULT_PATH = Path(
    os.environ.get(
        "AUDIT_LOG_FILE",
        str(Path(__file__).resolve().parent.parent / "logs" / "audit.jsonl"),
    )
)

_lock = threading.Lock()


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat(timespec="seconds")


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_audit(
    event: str,
    *,
    actor: str = "-",
    ip: str = "-",
    method: str = "-",
    path: str = "-",
    status: str = "ok",
    detail: Optional[Dict[str, Any]] = None,
) -> None:
    """Append one record to the audit log. Best-effort: never raises."""
    record = {
        "ts": _now(),
        "event": event,
        "actor": actor,
        "ip": ip,
        "method": method,
        "path": path,
        "status": status,
        "detail": detail or {},
    }
    target = Path(
        os.environ.get("AUDIT_LOG_FILE", str(_DEFAULT_PATH))
    )
    try:
        _ensure_parent(target)
        line = json.dumps(record, separators=(",", ":"), ensure_ascii=False)
        with _lock:
            with open(target, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
    except Exception:  # pragma: no cover - never block the request
        # Audit must never break the main flow. Swallow errors silently.
        pass


__all__ = ["write_audit"]
