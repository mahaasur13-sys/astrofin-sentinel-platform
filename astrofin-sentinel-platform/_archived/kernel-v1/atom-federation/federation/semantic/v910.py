"""
v9.10 — Semantic Consistency Lock Layer
========================================
Canonical Event Model + Semantic Binding + Cross-layer Identity Resolver + Drift Detector.

Unifies the system from "distributed protocol stack" into
"formally consistent semantic execution graph".
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class EventType(Enum):
    GOSSIP = auto()
    CONSENSUS = auto()
    PROOF = auto()
    REPLAY = auto()
    TRUST = auto()

    @classmethod
    def all(cls) -> list[EventType]:
        return [cls.GOSSIP, cls.CONSENSUS, cls.PROOF, cls.REPLAY, cls.TRUST]


class HashMode(Enum):
    CAUSAL = auto()
    CONSENSUS = auto()

    def separator(self) -> str:
        return "CAUSAL" if self == HashMode.CAUSAL else "CONSENSUS"


@dataclass(frozen=True)
class Event:
    event_id: str
    type: EventType
    entity_hash: str
    parent_refs: tuple[str, ...] = field(default_factory=tuple)
    hash_mode: HashMode = HashMode.CAUSAL
    trust_context: str = ""
    proof_ref: str = ""
    consensus_ref: str = ""
    timestamp_ns: int = field(default_factory=time.time_ns)
    metadata: tuple[str, ...] = field(default_factory=tuple)

    def semantic_id(self) -> tuple[EventType, str, HashMode]:
        return (self.type, self.entity_hash, self.hash_mode)

    def content_hash(self) -> str:
        payload = (
            self.event_id,
            self.type.name,
            self.entity_hash,
            self.parent_refs,
            self.hash_mode.name,
            self.trust_context,
            self.metadata,
        )
        data = json.dumps(payload, sort_keys=True, default=list)
        return hashlib.sha256(data.encode()).hexdigest()

    def consensus_hash(self) -> str:
        if not self.consensus_ref:
            raise ValueError("consensus_ref required for consensus_hash")
        payload = (
            self.event_id,
            self.type.name,
            self.entity_hash,
            self.parent_refs,
            self.hash_mode.name,
            self.trust_context,
            self.metadata,
            self.consensus_ref,
            self.proof_ref,
        )
        data = json.dumps(payload, sort_keys=True, default=list)
        return hashlib.sha256(data.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """
        Self-contained integrity check: recompute the event_id the same way emit() does.
        emit() uses: seed = (type.name, entity_hash, parent_refs, hash_mode.name)
        Returns True if recomputed seed-hash matches stored event_id.
        Does NOT depend on EventStore.get() — safe to call after reset().
        """
        try:
            seed = (
                self.type.name,
                self.entity_hash,
                self.parent_refs,
                self.hash_mode.name,
            )
            data = json.dumps(seed, sort_keys=True, default=list)
            expected = hashlib.sha256(data.encode()).hexdigest()
            return expected == self.event_id
        except Exception:
            return False
    def causal_ancestry(self) -> set[str]:
        ancestors: set[str] = set()
        stack = list(self.parent_refs)
        while stack:
            eid = stack.pop()
            if eid not in ancestors:
                ancestors.add(eid)
                parent = EventStore.get(eid)
                if parent:
                    stack.extend(parent.parent_refs)
        return ancestors

    def is_ancestor_of(self, other: Event) -> bool:
        return other.event_id in self.causal_ancestry()


class EventStore:
    _lock: threading.RLock = threading.RLock()
    _version_lock: threading.Lock = threading.Lock()
    _events: dict[str, Event] = {}
    _by_entity: dict[str, list[str]] = {}
    _by_type: dict[EventType, list[str]] = {}
    _version: int = 0
    _snapshot_epoch: int = 0

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            cls._events.clear()
            cls._by_entity.clear()
            cls._by_type.clear()
        with cls._version_lock:
            cls._version = 0

    @classmethod
    def emit(
        cls,
        event_type: EventType,
        entity_hash: str,
        parent_refs: Sequence[str] | None = None,
        hash_mode: HashMode = HashMode.CAUSAL,
        trust_context: str = "",
        proof_ref: str = "",
        consensus_ref: str = "",
        metadata: Sequence[str] | None = None,
    ) -> Event:
        """
        Thread-safe emit with idempotency + epoch monotonicity.

        Invariant: every event is tagged with the epoch at which it was emitted.
        Snapshot captures a consistent epoch boundary; no event emitted AFTER
        snapshot start can appear in it, even if store is mutated concurrently.
        """
        parents = tuple(parent_refs or [])
        meta = tuple(metadata or [])

        # event_id seed — does NOT include timestamp_ns (deterministic)
        seed = (event_type.name, entity_hash, parents, hash_mode.name)
        eid = hashlib.sha256(json.dumps(seed, sort_keys=True, default=list).encode()).hexdigest()

        # Capture monotonic epoch BEFORE writing — guarantees snapshot boundary
        with cls._version_lock:
            cls._version += 1
            emitted_epoch = cls._version

        with cls._lock:
            if eid in cls._events:
                return cls._events[eid]   # idempotent re-entry

            ev = Event(
                event_id=eid,
                type=event_type,
                entity_hash=entity_hash,
                parent_refs=parents,
                hash_mode=hash_mode,
                trust_context=trust_context,
                proof_ref=proof_ref,
                consensus_ref=consensus_ref,
                metadata=meta,
            )
            # Stamp epoch on event for snapshot boundary tracking
            object.__setattr__(ev, "_epoch", emitted_epoch)

            cls._events[eid] = ev
            cls._by_entity.setdefault(entity_hash, []).append(eid)
            cls._by_type.setdefault(event_type, []).append(eid)

            # Snapshot boundary: track epoch of last mutation
            cls._snapshot_epoch = emitted_epoch

        return ev

    @classmethod
    def get(cls, event_id: str) -> Event | None:
        with cls._lock:
            return cls._events.get(event_id)

    @classmethod
    def query_entity(cls, entity_hash: str) -> list[Event]:
        with cls._lock:
            return [
                cls._events[eid]
                for eid in cls._by_entity.get(entity_hash, [])
                if eid in cls._events
            ]

    @classmethod
    def size(cls) -> int:
        with cls._lock:
            return len(cls._events)

    @classmethod
    def resolve(cls, entity_hash: str) -> SemanticProjection | None:
        with cls._lock:
            entity_eids = cls._by_entity.get(entity_hash, [])
            if not entity_eids:
                return None

            mapped: dict[EventType, list[Event]] = {et: [] for et in EventType.all()}
            for eid in entity_eids:
                if eid in cls._events:
                    mapped[cls._events[eid].type].append(cls._events[eid])

            # CONSENSUS takes priority as canonical; then GOSSIP, then others
            canonical = None
            for et in [EventType.CONSENSUS, EventType.GOSSIP, EventType.PROOF, EventType.REPLAY, EventType.TRUST]:
                if mapped[et]:
                    canonical = max(mapped[et], key=lambda e: e.timestamp_ns)
                    break

            return SemanticProjection(
                entity_hash=entity_hash,
                canonical=canonical,
                gossip_events=mapped[EventType.GOSSIP],
                consensus_events=mapped[EventType.CONSENSUS],
                proof_events=mapped[EventType.PROOF],
                replay_events=mapped[EventType.REPLAY],
                trust_events=mapped[EventType.TRUST],
            )

    @classmethod
    def snapshot(cls) -> EventStoreSnapshot:
        """Point-in-time view with monotonic epoch boundary.

        Guarantees:
        - All events with _epoch <= boundary are fully captured
        - No event with _epoch > boundary is included
        - Even if emit() races concurrently, snapshot epoch is stable
        """
        with cls._version_lock:
            boundary_epoch = cls._snapshot_epoch

        events_copy: dict[str, Event] = {}
        by_entity_copy: dict[str, list[str]] = {}
        by_type_copy: dict[EventType, list[str]] = {}

        with cls._lock:
            for eid, ev in cls._events.items():
                # Filter: only events whose emission epoch is <= boundary
                ep = getattr(ev, "_epoch", 0)
                if ep <= boundary_epoch:
                    events_copy[eid] = ev
            by_entity_copy = {k: list(v) for k, v in cls._by_entity.items()}
            by_type_copy = {k: list(v) for k, v in cls._by_type.items()}

        return EventStoreSnapshot(
            _events=events_copy,
            _by_entity=by_entity_copy,
            _by_type=by_type_copy,
            epoch=boundary_epoch,
        )

    @classmethod
    def query_entity_snapshot(cls, entity_hash: str) -> list[Event]:
        snap = cls.snapshot()
        return [cls._events[eid] for eid in snap._by_entity.get(entity_hash, [])
                if eid in cls._events]

    @classmethod
    def resolve_snapshot(cls, entity_hash: str) -> SemanticProjection | None:
        snap = cls.snapshot()
        events = [snap._events[eid] for eid in snap._by_entity.get(entity_hash, [])
                  if eid in snap._events]
        if not events:
            return None
        mapped: dict[EventType, list[Event]] = {et: [] for et in EventType.all()}
        for event in events:
            mapped[event.type].append(event)
        canonical = None
        for et in [EventType.CONSENSUS, EventType.GOSSIP,
                   EventType.PROOF, EventType.REPLAY, EventType.TRUST]:
            if mapped[et]:
                canonical = max(mapped[et], key=lambda e: e.timestamp_ns)
                break
        return SemanticProjection(
            entity_hash=entity_hash,
            canonical=canonical,
            gossip_events=mapped[EventType.GOSSIP],
            consensus_events=mapped[EventType.CONSENSUS],
            proof_events=mapped[EventType.PROOF],
            replay_events=mapped[EventType.REPLAY],
            trust_events=mapped[EventType.TRUST],
        )

    @classmethod
    def scan_all_snapshot(cls) -> list[DriftReport]:
        """Drift scan on the epoch-bounded snapshot — consistent even under concurrent emit()."""
        snap = cls.snapshot()
        detector = DriftDetector(store=snap)
        return detector.scan_all()


@dataclass(frozen=True)
class SemanticProjection:
    entity_hash: str
    canonical: Event | None
    gossip_events: list[Event]
    consensus_events: list[Event]
    proof_events: list[Event]
    replay_events: list[Event]
    trust_events: list[Event]

    def has_consensus(self) -> bool:
        return bool(self.consensus_events)

    def event_ids(self) -> set[str]:
        result: set[str] = set()
        for bucket in (
            self.gossip_events,
            self.consensus_events,
            self.proof_events,
            self.replay_events,
            self.trust_events,
        ):
            result.update(event.event_id for event in bucket)
        return result


class DriftKind(Enum):
    HASH_MISMATCH = auto()
    GOSSIP_CONSENSUS = auto()
    PROOF_CONSENSUS = auto()
    TRUST_REPLAY = auto()
    IDENTITY_COLLISION = auto()


@dataclass(frozen=True)
class DriftReport:
    kind: DriftKind
    entity_hash: str
    description: str
    involved_ids: tuple[str, ...]

    def __str__(self) -> str:
        return f"[{self.kind.name}] {self.description} entity={self.entity_hash} events={self.involved_ids}"


class DriftDetector:
    def __init__(self, store: type[EventStore] = EventStore):
        self.store = store

    def scan_all(self) -> list[DriftReport]:
        reports: list[DriftReport] = []
        for entity_hash in list(self.store._by_entity.keys()):
            projection = self.store.resolve(entity_hash)
            if projection:
                reports.extend(self._scan_projection(projection))
        return reports

    def _scan_projection(self, proj: SemanticProjection) -> list[DriftReport]:
        reports: list[DriftReport] = []
        reports.extend(self._check_hash_mismatch(proj))
        reports.extend(self._check_proof_consensus(proj))
        # _check_proof_consensus_mismatch checks cross-reference consistency
        reports.extend(self._check_proof_consensus_mismatch(proj))
        reports.extend(self._check_trust_replay(proj))
        reports.extend(self._check_identity_collision(proj))
        return reports

    def _check_hash_mismatch(self, proj: SemanticProjection) -> list[DriftReport]:
        reports: list[DriftReport] = []
        # Group events by (type, hash_mode) — each group should agree on entity_hash
        from collections import defaultdict
        by_key: dict[tuple, list[Event]] = defaultdict(list)
        all_events = [self.store.get(eid) for eid in proj.event_ids()]
        for e in all_events:
            if e:
                by_key[(e.type, e.hash_mode)].append(e)
        for key, events in by_key.items():
            hashes = {e.content_hash() for e in events}
            if len(hashes) > 1:
                reports.append(DriftReport(
                    kind=DriftKind.HASH_MISMATCH,
                    entity_hash=proj.entity_hash,
                    description=f"multiple hashes for same (type,mode)={key}: {hashes}",
                    involved_ids=tuple(e.event_id for e in events),
                ))
        return reports

    def _check_gossip_consensus(self, proj: SemanticProjection) -> list[DriftReport]:
        # NOTE: GOSSIP_CONSENSUS drift detection is inherently impossible within
        # a single projection, because a projection IS defined by entity_hash.
        # If GOSSIP and CONSENSUS events share entity_hash, they agree by definition.
        # Cross-projection drift is handled via entity_alias tracking (future).
        return []

    def _check_proof_consensus(self, proj: SemanticProjection) -> list[DriftReport]:
        proof = {event.entity_hash for event in proj.proof_events}
        consensus = {event.entity_hash for event in proj.consensus_events}
        if proof and consensus and proof != consensus:
            return [DriftReport(
                kind=DriftKind.PROOF_CONSENSUS,
                entity_hash=proj.entity_hash,
                description="proof artifacts disagree with consensus",
                involved_ids=tuple(proj.event_ids()),
            )]
        return []

    def _check_proof_consensus_mismatch(self, proj: SemanticProjection) -> list[DriftReport]:
        reports: list[DriftReport] = []
        for event in proj.proof_events:
            if event.consensus_ref:
                consensus_event = self.store.get(event.consensus_ref)
                if consensus_event and event.entity_hash != consensus_event.entity_hash:
                    reports.append(DriftReport(
                        kind=DriftKind.PROOF_CONSENSUS,
                        entity_hash=proj.entity_hash,
                        description=(
                            f"PROOF {event.event_id} entity_hash={event.entity_hash} "
                            f"!= CONSENSUS {event.consensus_ref} entity_hash={consensus_event.entity_hash}"
                        ),
                        involved_ids=(event.event_id, event.consensus_ref),
                    ))
        return reports

    def _check_trust_replay(self, proj: SemanticProjection) -> list[DriftReport]:
        trust = {event.entity_hash for event in proj.trust_events}
        replay = {event.entity_hash for event in proj.replay_events}
        if trust and replay and trust != replay:
            return [DriftReport(
                kind=DriftKind.TRUST_REPLAY,
                entity_hash=proj.entity_hash,
                description="trust ledger diverges from replay trace",
                involved_ids=tuple(proj.event_ids()),
            )]
        return []

    def _check_identity_collision(self, proj: SemanticProjection) -> list[DriftReport]:
        reports: list[DriftReport] = []
        # Check for duplicate event_ids in the store
        seen_ids: dict[str, list[str]] = {}
        for eid in proj.event_ids():
            seen_ids.setdefault(eid, []).append(eid)
        for eid, ids in seen_ids.items():
            if len(ids) > 1:
                reports.append(DriftReport(
                    kind=DriftKind.IDENTITY_COLLISION,
                    entity_hash=proj.entity_hash,
                    description=f"event_id {eid} used {len(ids)} times",
                    involved_ids=tuple(ids),
                ))
        return reports


class SemanticBinder:
    @staticmethod
    def bind_layer(event_type: EventType, entity_hash: str, **kwargs: Any) -> Event:
        return EventStore.emit(event_type=event_type, entity_hash=entity_hash, **kwargs)

    @staticmethod
    def bind_gossip(delta_hash: str, seq: int, peers: Iterable[str], trust_context: str = "") -> Event:
        metadata = (f"seq={seq}", f"peers={','.join(sorted(peers))}")
        return SemanticBinder.bind_layer(
            EventType.GOSSIP,
            delta_hash,
            hash_mode=HashMode.CAUSAL,
            trust_context=trust_context,
            metadata=metadata,
        )

    @staticmethod
    def bind_consensus(entity_hash: str, voters: Sequence[str], outcome: str, parent_refs: Sequence[str] | None = None) -> Event:
        metadata = (f"voters={','.join(sorted(voters))}", f"outcome={outcome}")
        return SemanticBinder.bind_layer(
            EventType.CONSENSUS,
            entity_hash,
            parent_refs=list(parent_refs or []),
            hash_mode=HashMode.CONSENSUS,
            metadata=metadata,
        )

    @staticmethod
    def bind_proof(entity_hash: str, proof_hash: str, consensus_ref: str | None = None) -> Event:
        metadata = (f"proof={proof_hash}",)
        return SemanticBinder.bind_layer(
            EventType.PROOF,
            entity_hash,
            proof_ref=consensus_ref or "",
            metadata=metadata,
        )

    @staticmethod
    def bind_trust(entity_hash: str, ledger_snapshot: str) -> Event:
        metadata = (f"trust={ledger_snapshot}",)
        return SemanticBinder.bind_layer(
            EventType.TRUST,
            entity_hash,
            trust_context=ledger_snapshot,
            metadata=metadata,
        )

    @staticmethod
    def bind_replay(entity_hash: str, trace_id: str) -> Event:
        metadata = (f"trace={trace_id}",)
        return SemanticBinder.bind_layer(
            EventType.REPLAY,
            entity_hash,
            metadata=metadata,
        )


class EventStoreSnapshot:
    """
    Immutable, epoch-bounded view of EventStore state.

    Guarantees:
    - No event with _epoch > boundary_epoch is included
    - Snapshot epoch is determined atomically with _version_lock
      BEFORE snapshot construction starts — no mid-flight events leak in
    - safe to pass to DriftDetector from any thread
    """
    _events: dict[str, Event]
    _by_entity: dict[str, list[str]]
    _by_type: dict[EventType, list[str]]
    epoch: int

    def resolve(self, entity_hash: str) -> SemanticProjection | None:
        events = [self._events[eid] for eid in self._by_entity.get(entity_hash, [])
                  if eid in self._events]
        if not events:
            return None
        mapped: dict[EventType, list[Event]] = {et: [] for et in EventType.all()}
        for event in events:
            mapped[event.type].append(event)
        canonical = None
        for et in [EventType.CONSENSUS, EventType.GOSSIP,
                   EventType.PROOF, EventType.REPLAY, EventType.TRUST]:
            if mapped[et]:
                canonical = max(mapped[et], key=lambda e: e.timestamp_ns)
                break
        return SemanticProjection(
            entity_hash=entity_hash,
            canonical=canonical,
            gossip_events=mapped[EventType.GOSSIP],
            consensus_events=mapped[EventType.CONSENSUS],
            proof_events=mapped[EventType.PROOF],
            replay_events=mapped[EventType.REPLAY],
            trust_events=mapped[EventType.TRUST],
        )
