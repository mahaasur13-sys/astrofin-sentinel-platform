"""Hypothesis pre-registration: the spec's SHA-256 is recorded BEFORE any test runs.

Layout under ``root``: hypotheses/<sha256>.json  (write-once, 0o444)
``require_registered`` refuses (ProtocolError) a spec whose hash was never registered or whose
content no longer matches the registered hash; nothing should be computed in that case.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .errors import ProtocolError
from .protocol import canonical


def spec_sha256(spec: bytes | str | os.PathLike) -> str:
    """SHA-256 of the spec's exact bytes (a path is read as bytes; str is UTF-8 encoded)."""
    if isinstance(spec, (os.PathLike, Path)):
        data = Path(spec).read_bytes()
    elif isinstance(spec, str):
        data = spec.encode()
    else:
        data = bytes(spec)
    return hashlib.sha256(data).hexdigest()


class HypothesisRegistry:
    def __init__(self, root: str | os.PathLike, clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)):
        self.dir = Path(root) / "hypotheses"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.clock = clock

    def _path(self, h: str) -> Path:
        if not (len(h) == 64 and all(c in "0123456789abcdef" for c in h)):
            raise ProtocolError(f"invalid spec hash {h!r}")
        return self.dir / f"{h}.json"

    def register(self, spec: bytes | str | os.PathLike, hypothesis_id: str) -> str:
        h = spec_sha256(spec)
        try:
            fd = os.open(self._path(h), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
        except FileExistsError:
            return h  # idempotent: same bytes, same record
        with os.fdopen(fd, "w") as f:
            f.write(
                canonical({"spec_sha256": h, "hypothesis_id": hypothesis_id, "registered_at": self.clock().isoformat()})
            )
        return h

    def require_registered(self, spec: bytes | str | os.PathLike, expected_sha256: str) -> dict:
        """Gate before a test: spec bytes must hash to ``expected_sha256`` and that hash be registered."""
        actual = spec_sha256(spec)
        if actual != expected_sha256:
            raise ProtocolError(f"hypothesis spec changed after registration: {actual} != {expected_sha256}")
        p = self._path(actual)
        if not p.exists():
            raise ProtocolError(f"hypothesis {actual} not pre-registered; register before testing")
        rec = json.loads(p.read_text())
        if rec.get("spec_sha256") != actual:
            raise ProtocolError(f"registry record {actual} tampered")
        return rec
