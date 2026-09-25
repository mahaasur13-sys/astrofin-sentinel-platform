"""
DashBeam Transfer Plugin — P2P файловый обмен через Iroh + QUIC.

Core entities: DashBeamTicket, DashBeamSession, PairedDevice, DashBeamRelayConfig.
Security: только view-only wallet данные, spend keys жёстко запрещены.
"""
from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime, timedelta, timezone


@dataclasses.dataclass
class DashBeamTicket:
    ticket_id: str = ""
    code: str = ""
    expires_at: str = ""
    file_metadata: dict | None = None
    relay_node_id: str | None = None

    @classmethod
    def create(cls, file_metadata: dict, ttl_minutes: int = 30) -> "DashBeamTicket":
        code = str(uuid.uuid4())[:8]
        expires = (datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)).isoformat()
        return cls(
            ticket_id=f"dbt-{code}",
            code=code,
            expires_at=expires,
            file_metadata=file_metadata,
        )


@dataclasses.dataclass
class DashBeamSession:
    session_id: str = ""
    ticket_code: str = ""
    peer_id: str = ""
    connected: bool = False
    transferred_bytes: int = 0
    encryption: str = "TLS 1.3 + QUIC"

    @classmethod
    def from_ticket(cls, ticket: DashBeamTicket) -> "DashBeamSession":
        return cls(
            session_id=f"dbs-{ticket.code}",
            ticket_code=ticket.code,
        )


@dataclasses.dataclass
class PairedDevice:
    device_id: str = ""
    name: str = ""
    last_seen: str = ""
    trusted: bool = False

    @classmethod
    def register(cls, name: str) -> "PairedDevice":
        return cls(
            device_id=str(uuid.uuid4())[:8],
            name=name,
            last_seen=datetime.now(timezone.utc).isoformat(),
            trusted=True,
        )


@dataclasses.dataclass
class DashBeamRelayConfig:
    relay_url: str = ""
    tls_cert_path: str = ""
    max_bandwidth_mbps: int = 100
    allowed_peers: list[str] = dataclasses.field(default_factory=list)

    @classmethod
    def for_enterprise(cls, relay_url: str, cert_path: str) -> "DashBeamRelayConfig":
        return cls(relay_url=relay_url, tls_cert_path=cert_path)


class Plugin:
    """DashBeam Transfer Plugin — P2P file transfer via Iroh/QUIC."""

    def __init__(self):
        self.tickets: dict[str, DashBeamTicket] = {}
        self.sessions: dict[str, DashBeamSession] = {}
        self.devices: dict[str, PairedDevice] = {}
        self.relay_config: DashBeamRelayConfig | None = None

    def on_enable(self) -> None:
        pass

    def create_ticket(self, file_metadata: dict, ttl_minutes: int = 30) -> DashBeamTicket:
        ticket = DashBeamTicket.create(file_metadata, ttl_minutes)
        self.tickets[ticket.ticket_id] = ticket
        return ticket

    def resolve_ticket(self, code: str) -> DashBeamSession | None:
        for ticket in self.tickets.values():
            if ticket.code == code:
                session = DashBeamSession.from_ticket(ticket)
                self.sessions[session.session_id] = session
                session.connected = True
                return session
        return None

    def register_device(self, name: str) -> PairedDevice:
        device = PairedDevice.register(name)
        self.devices[device.device_id] = device
        return device

    def share_wallet_view_only(self, wallet_id: str) -> dict:
        """Share ONLY view-only wallet data. Spend keys NEVER leak."""
        return {
            "wallet_id": wallet_id,
            "primary_address": "4...",
            "view_key": "0...",
            "subaddresses": [],
            "spend_key": "*** NEVER SHARED ***",
        }
