"""Frozen protocol records and the final-OOS access log (contamination guard).

Layout under ``root``:
  protocols/<protocol_hash>.json      frozen protocol (write-once)
  final_oos/<protocol_hash>.accessed  marker created atomically (O_EXCL) BEFORE final OOS is computed
  final_oos_access.log                append-only JSONL of every final-OOS access and refusal
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .errors import ContaminationError, ProtocolError
from .leakage import Bar


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def params_hash(params: Mapping[str, Any]) -> str:
    return _sha(canonical(dict(params)))


def data_fingerprint(bars: Sequence[Bar]) -> str:
    h = hashlib.sha256()
    for b in bars:
        h.update(f"{b.ts.isoformat()}|{b.symbol}|{b.close!r}\n".encode())
    return h.hexdigest()


@dataclass(frozen=True)
class FrozenProtocol:
    strategy_version: str
    params: Mapping[str, Any]
    params_hash: str
    split: Mapping[str, Any]  # split boundaries (indices + timestamps + embargo)
    config_hash: str
    data_fingerprint: str
    variants_tried: int

    def body(self) -> dict:
        d = asdict(self)
        d["params"] = dict(self.params)
        d["split"] = json.loads(canonical(self.split))
        return d

    @property
    def protocol_hash(self) -> str:
        return _sha(canonical(self.body()))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProtocolStore:
    def __init__(self, root: str | os.PathLike, clock: Callable[[], datetime] = _utcnow):
        self.root = Path(root)
        self.clock = clock
        (self.root / "protocols").mkdir(parents=True, exist_ok=True)
        (self.root / "final_oos").mkdir(parents=True, exist_ok=True)
        self.log_path = self.root / "final_oos_access.log"

    # ── protocol records ─────────────────────────────────────────────────────

    def _ppath(self, h: str) -> Path:
        if not (len(h) == 64 and all(c in "0123456789abcdef" for c in h)):
            raise ProtocolError(f"invalid protocol hash {h!r}")
        return self.root / "protocols" / f"{h}.json"

    def freeze(self, protocol: FrozenProtocol) -> str:
        viewed = self.viewed_protocols(protocol.strategy_version)
        h = protocol.protocol_hash
        if viewed and h not in viewed:
            self._log({"event": "REFUSED_FREEZE", "protocol_hash": h, "strategy_version": protocol.strategy_version,
                       "reason": "final OOS already viewed for this strategy_version"})
            raise ContaminationError(
                f"strategy {protocol.strategy_version!r} already viewed final OOS under {sorted(viewed)}; "
                "a changed protocol after viewing is contaminated"
            )
        path = self._ppath(h)
        data = canonical({"protocol_hash": h, "frozen_at": self.clock().isoformat(), "body": protocol.body()})
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
        except FileExistsError:
            self.load(h)  # verifies integrity of the existing record
            return h
        with os.fdopen(fd, "w") as f:
            f.write(data)
        return h

    def load(self, h: str) -> FrozenProtocol:
        path = self._ppath(h)
        if not path.exists():
            raise ProtocolError(f"no frozen protocol {h}: freeze the protocol before final OOS")
        try:
            rec = json.loads(path.read_text())
            p = FrozenProtocol(**rec["body"])
        except (ValueError, KeyError, TypeError) as e:
            raise ProtocolError(f"protocol {h} unreadable: {e}") from None
        if p.protocol_hash != h or rec.get("protocol_hash") != h:
            raise ProtocolError(f"protocol {h} content does not match its hash (tampered)")
        return p

    # ── final-OOS access ─────────────────────────────────────────────────────

    def _log(self, entry: dict) -> None:
        entry = {"at": self.clock().isoformat(), **entry}
        with open(self.log_path, "a") as f:
            f.write(canonical(entry) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def access_log(self) -> list[dict]:
        if not self.log_path.exists():
            return []
        return [json.loads(line) for line in self.log_path.read_text().splitlines() if line.strip()]

    def viewed_protocols(self, strategy_version: str) -> set[str]:
        return {e["protocol_hash"] for e in self.access_log()
                if e.get("event") == "FINAL_OOS_ACCESS" and e.get("strategy_version") == strategy_version}

    def marker(self, h: str) -> Path:
        self._ppath(h)
        return self.root / "final_oos" / f"{h}.accessed"

    def refuse(self, h: str, strategy_version: str, reason: str) -> None:
        self._log({"event": "REFUSED", "protocol_hash": h, "strategy_version": strategy_version, "reason": reason})

    def claim_final_oos(self, protocol: FrozenProtocol) -> None:
        """Atomically mark the protocol's final OOS as viewed. Raises ContaminationError if already viewed."""
        h = protocol.protocol_hash
        others = self.viewed_protocols(protocol.strategy_version) - {h}
        if others:
            self.refuse(h, protocol.strategy_version, f"strategy already viewed final OOS under {sorted(others)}")
            raise ContaminationError(
                f"strategy {protocol.strategy_version!r} already viewed final OOS under another protocol; refused"
            )
        try:
            fd = os.open(self.marker(h), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
        except FileExistsError:
            self.refuse(h, protocol.strategy_version, "final OOS already run for this protocol")
            raise ContaminationError(
                f"final OOS for protocol {h} was already viewed; re-run refused (contaminated)"
            ) from None
        with os.fdopen(fd, "w") as f:
            f.write(canonical({"protocol_hash": h, "strategy_version": protocol.strategy_version,
                               "at": self.clock().isoformat()}))
        self._log({"event": "FINAL_OOS_ACCESS", "protocol_hash": h, "strategy_version": protocol.strategy_version})

    def record_result(self, h: str, strategy_version: str, metrics: Mapping[str, Any]) -> None:
        self._log({"event": "FINAL_OOS_RESULT", "protocol_hash": h, "strategy_version": strategy_version,
                   "metrics": dict(metrics)})
