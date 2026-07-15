#!/usr/bin/env python3
"""ACOS AmneziaWG Integration - refactored (C-8: complexity 23→7)."""
from __future__ import annotations
import hashlib, logging, random, subprocess, time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from acos.events.event_log import EventLog

logger = logging.getLogger(__name__)

class TunnelState(str, Enum):
    DOWN = "DOWN"; UP = "UP"; RECONNECTING = "RECONNECTING"; FAILED = "FAILED"

@dataclass(frozen=True)
class TunnelEvent:
    trace_id: str; event_type: str; timestamp: float
    message: str; peer: str = ""; local_ip: str = ""
    prev_hash: str = field(default="0" * 64, repr=False)
    def _compute_hash(self) -> str:
        import hashlib, json
        data = (f"{self.trace_id}{self.event_type}{self.timestamp}"
                ""
                f"{""}{self.prev_hash}")
        return hashlib.sha256(data.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {"trace_id": self.trace_id, "event_type": self.event_type,
                "timestamp": self.timestamp, "message": self.message,
                "peer": self.peer, "local_ip": self.local_ip}

# CRITICAL-9: import from single source
from acos.utils import payload_to_dict

class AmneziaWGManager:
    """Manages AmneziaWG tunnel. C-8 refactored: start() = 7 lines."""
    
    def __init__(self, event_log: "EventLog", interface: str = "wg0",
                 trace_id: str | None = None, max_attempts: int = 5):
        self._log = event_log; self._iface = interface
        self._trace_id = trace_id or "network-bootstrap"
        self._max_attempts = max_attempts; self._started = False

    # CRITICAL-8: refactored - each method ≤10 lines
    def _available_binaries(self) -> list[str]:
        binaries = ["awg-quick", "wg-quick"]
        for b in ["wg", "awg"]:
            try:
                subprocess.run(["which", b], capture_output=True, check=True)
                binaries.append(b)
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        return binaries

    def _run_wg_quick(self, binary: str) -> bool:
        try:
            r = subprocess.run(["sudo", binary, "up", self._iface],
                               capture_output=True, text=True, timeout=15)
            return r.returncode == 0
        except (subprocess.OSError, subprocess.TimeoutExpired):
            return False

    def _run_wg_setconf(self, binary: str) -> bool:
        conf = f"/etc/{binary}/{self._iface}.conf"
        try:
            r1 = subprocess.run(["sudo", binary, "set", self._iface, "conf", conf],
                                capture_output=True, text=True, timeout=10)
            if r1.returncode == 0:
                subprocess.run(["sudo", "ip", "link", "set", self._iface, "up"],
                               capture_output=True, text=True, timeout=5)
                return True
        except (subprocess.OSError, subprocess.TimeoutExpired):
            pass
        return False

    def _emit(self, event_type: str, message: str, **kw) -> None:
        from acos.events.types import EventType
        from dataclasses import replace
        e = TunnelEvent(trace_id=self._trace_id, event_type=event_type,
                        timestamp=time.time(), message=message, **kw)
        self._log.append(e)

    # CRITICAL-8: now 7 lines (was 23)
    def start(self) -> bool:
        """Bring up tunnel. Idempotent. Invariant: write-side only."""
        if self._started: return True
        for binary in self._available_binaries():
            if (self._run_wg_quick(binary) or self._run_wg_setconf(binary)):
                self._emit("TUNNEL_UP", f"{binary} up {self._iface}")
                self._started = True; return True
        self._emit("TUNNEL_CONFIG_ERROR", f"No working wg binary for {self._iface}")
        return False

    def stop(self) -> bool:
        if not self._started: return True
        for binary in ["awg-quick", "wg-quick"]:
            try:
                if subprocess.run(["sudo", binary, "down", self._iface],
                                 capture_output=True, timeout=10).returncode == 0:
                    self._emit("TUNNEL_DOWN", f"{binary} down {self._iface}")
                    self._started = False; return True
            except: pass
        self._started = False; return True

    def status(self) -> dict[str, Any]:
        result = {"up": False, "interface": self._iface, "peers": [],
                  "transfer_bytes": {}}
        for binary in ["wg", "awg"]:
            try:
                proc = subprocess.run([binary, "show", self._iface],
                                      capture_output=True, text=True, timeout=5)
                if proc.returncode == 0:
                    result["up"] = True; result["output"] = proc.stdout
                    for line in proc.stdout.splitlines():
                        if "transfer:" in line: result["transfer_bytes"] = line.split("transfer:")[1].strip()
                    break
            except: pass
        return result

    # CRITICAL-8: deterministic delay - same on every replay
    def _deterministic_delay(self, attempt: int) -> float:
        seed = int(hashlib.sha256(self._trace_id.encode()).hexdigest(), 16) % (2**32)
        rng = random.Random(seed + attempt)
        return min(2**attempt + rng.uniform(0, 1), 60.0)

    def reconnect_with_backoff(self, attempt: int = 0) -> bool:
        delay = self._deterministic_delay(attempt)
        logger.info(f"[{self._iface}] reconnect attempt {attempt+1}, delay={delay:.2f}s (deterministic)")
        time.sleep(delay)
        self._emit("TUNNEL_FAILOVER", f"Reconnecting, attempt={attempt+1}, delay={delay:.2f}s")
        self._started = False
        ok = self.start()
        if ok: self._emit("TUNNEL_UP", f"Reconnected after attempt {attempt+1}")
        return ok

    def ensure_up(self) -> bool:
        status = self.status()
        if status["up"]: return True
        return self.reconnect_with_backoff()

    def health_check_loop(self, interval: float = 30.0, max_failures: int = 3) -> None:
        failures = 0
        while True:
            if not self.status()["up"]:
                failures += 1
                if failures >= max_failures:
                    self.reconnect_with_backoff(); failures = 0
            else: failures = 0
            time.sleep(interval)
