"""
Observability layer — structured logging + cluster metrics.
"""
import threading
import time
from dataclasses import dataclass, field
from enum import Enum

import logging
log = logging.getLogger(__name__)



class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    ts: float
    level: str
    node_id: str
    event: str
    details: dict = field(default_factory=dict)


class ClusterLogger:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self._entries: list[LogEntry] = []
        self._lock = threading.Lock()
        self._max_entries = 10_000

    def log(self, level: str, event: str, **details):
        entry = LogEntry(
            ts=time.time(),
            level=level,
            node_id=self.node_id,
            event=event,
            details=details,
        )
        with self._lock:
            self._entries.append(entry)
            if len(self._entries) > self._max_entries:
                self._entries = self._entries[-self._max_entries_:]

        prefix = {
            "DEBUG":   "[DBG]",
            "INFO":    "[INF]",
            "WARN":    "[WRN]",
            "ERROR":   "[ERR]",
            "CRITICAL":"[CRT]",
        }.get(level, "[???]")
        log.info(f"{prefix} {self.node_id} {event}  {details}")

    def debug(self, event: str, **details):
        self.log("DEBUG", event, **details)

    def info(self, event: str, **details):
        self.log("INFO", event, **details)

    def warn(self, event: str, **details):
        self.log("WARN", event, **details)

    def error(self, event: str, **details):
        self.log("ERROR", event, **details)

    def get_entries(self, since: float | None = None) -> list[LogEntry]:
        with self._lock:
            if since is None:
                return list(self._entries)
            return [e for e in self._entries if e.ts >= since]


@dataclass
class NodeMetrics:
    node_id: str
    sent: int = 0
    recv: int = 0
    drops: int = 0
    duplicates: int = 0
    sbs_violations: int = 0
    last_pong_ms: float = 0.0
    lag_ms: float = 0.0
    last_seen: float = 0.0

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "sent": self.sent,
            "recv": self.recv,
            "drops": self.drops,
            "duplicates": self.duplicates,
            "sbs_violations": self.sbs_violations,
            "last_pong_ms": self.last_pong_ms,
            "lag_ms": self.lag_ms,
            "last_seen": self.last_seen,
        }


class MetricsCollector:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self._lock = threading.Lock()
        self._peers: dict[str, NodeMetrics] = {}

    def init_peer(self, peer_id: str):
        with self._lock:
            if peer_id not in self._peers:
                self._peers[peer_id] = NodeMetrics(node_id=peer_id)

    def record_send(self, peer_id: str):
        with self._lock:
            if peer_id in self._peers:
                self._peers[peer_id].sent += 1

    def record_recv(self, peer_id: str):
        with self._lock:
            if peer_id in self._peers:
                m = self._peers[peer_id]
                m.recv += 1
                m.last_seen = time.time()

    def record_drop(self, peer_id: str):
        with self._lock:
            if peer_id in self._peers:
                self._peers[peer_id].drops += 1

    def record_dup(self, peer_id: str):
        with self._lock:
            if peer_id in self._peers:
                self._peers[peer_id].duplicates += 1

    def record_pong(self, peer_id: str, latency_ms: float):
        with self._lock:
            if peer_id in self._peers:
                m = self._peers[peer_id]
                m.last_pong_ms = latency_ms
                m.lag_ms = latency_ms
                m.last_seen = time.time()

    def record_violation(self, peer_id: str):
        with self._lock:
            if peer_id in self._peers:
                self._peers[peer_id].sbs_violations += 1

    def get_peer(self, peer_id: str) -> NodeMetrics | None:
        with self._lock:
            return self._peers.get(peer_id)

    def get_all(self) -> dict[str, dict]:
        with self._lock:
            return {pid: m.to_dict() for pid, m in self._peers.items()}
