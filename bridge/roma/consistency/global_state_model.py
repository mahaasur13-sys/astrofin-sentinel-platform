"""
ROMA Global State Model — Single Source of Truth contract.
Defines: truth hierarchy, conflict resolution rules, consistency guarantees.
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone


class TruthSource(str, Enum):
    """
    Hierarchy of truth sources (highest to lowest).
    K8s is the physical truth. Redis is the logical cache.
    Event Store is the historical truth.
    """
    KUBERNETES = "k8s"          # Physical execution truth (always authoritative for running jobs)
    REDIS = "redis"              # Logical state cache (queues, scheduling)
    EVENT_STORE = "event_store"  # Historical truth (append-only log)
    STATE_SNAPSHOT = "snapshot"  # Derived truth (from replay)


class ConflictResolution(str, Enum):
    """Rules for resolving state conflicts between sources."""
    K8S_WINS = "k8s_wins"           # K8s job state overrides all
    LAST_WRITE_WINS = "last_write"  # Most recent timestamp wins
    SOURCE_PRIORITY = "source"       # Follow TruthSource hierarchy
    MERGE = "merge"                  # Merge states (union of truth)
    BLOCK = "block"                  # Reject conflicting update


@dataclass
class GlobalStateRecord:
    """Single record in the global state model."""
    job_id: str
    field: str
    value: Any
    source: TruthSource
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sequence: int = 0
    version: int = 0  # Optimistic locking

    def is_stale(self, other: "GlobalStateRecord") -> bool:
        """Check if this record is older than another."""
        if self.sequence and other.sequence:
            return self.sequence < other.sequence
        return self.timestamp < other.timestamp


class GlobalStateModel:
    """
    Single source of truth contract.
    
    Truth hierarchy:
    1. K8s (running job state) — highest priority
    2. Redis (queued/scheduled state) — medium priority  
    3. Event Store (historical log) — replay source
    4. State Snapshots (derived) — for fast recovery
    
    Key invariant:
    ∀ job: consistent(job) = (k8s_state == redis_state == event_store_replay)
    
    When invariant breaks → ReconciliationEngine.trigger_repair()
    """

    def __init__(self, event_store=None, state_store=None, redis_client=None):
        self.event_store = event_store
        self.state_store = state_store
        self.redis_client = redis_client
        self._cache: Dict[str, GlobalStateRecord] = {}

    # -------------------------------------------------------------------------
    # Truth reconciliation
    # -------------------------------------------------------------------------

    def get_truth(self, job_id: str, field: str) -> GlobalStateRecord:
        """
        Get authoritative value for a job field.
        Follows truth hierarchy: K8s → Redis → Event Store → Snapshot
        """
        # 1. Check K8s (physical truth)
        k8s_val = self._get_k8s_field(job_id, field)
        if k8s_val is not None:
            return GlobalStateRecord(
                job_id=job_id, field=field, value=k8s_val,
                source=TruthSource.KUBERNETES
            )

        # 2. Check Redis (logical cache)
        redis_val = self._get_redis_field(job_id, field)
        if redis_val is not None:
            return GlobalStateRecord(
                job_id=job_id, field=field, value=redis_val,
                source=TruthSource.REDIS
            )

        # 3. Reconstruct from Event Store
        event_val = self._reconstruct_from_event_store(job_id, field)
        if event_val is not None:
            return GlobalStateRecord(
                job_id=job_id, field=field, value=event_val,
                source=TruthSource.EVENT_STORE
            )

        return None

    def resolve_conflict(self, record_a: GlobalStateRecord, record_b: GlobalStateRecord) -> GlobalStateRecord:
        """
        Resolve conflict between two records using resolution strategy.
        Returns authoritative record.
        """
        # Source priority wins by default
        source_order = {
            TruthSource.KUBERNETES: 0,
            TruthSource.REDIS: 1,
            TruthSource.EVENT_STORE: 2,
            TruthSource.STATE_SNAPSHOT: 3,
        }

        if source_order[record_a.source] < source_order[record_b.source]:
            return record_a
        return record_b

    def check_consistency(self, job_id: str) -> Dict[str, bool]:
        """
        Verify consistency invariant for a job.
        Returns dict of field -> is_consistent
        """
        fields = ["status", "gpu_allocated", "node", "priority"]
        result = {}
        records = []

        for field in fields:
            record = self.get_truth(job_id, field)
            if record:
                records.append(record)

        # Check if all sources agree (simplified)
        if len(records) < 2:
            result["overall"] = True  # Not enough data
        else:
            # All records should have same value for shared fields
            values_by_field: Dict[str, set] = {}
            for rec in records:
                if rec.field not in values_by_field:
                    values_by_field[rec.field] = set()
                values_by_field[rec.field].add(rec.value)

            result["overall"] = all(len(v) == 1 for v in values_by_field.values())

        return result

    # -------------------------------------------------------------------------
    # Backpressure & load control
    # -------------------------------------------------------------------------

    def get_gpu_saturation(self) -> float:
        """
        Returns GPU saturation 0.0-1.0 (VRAM used / VRAM available).
        Used for backpressure decisions.
        """
        # Placeholder — integrate with nvidia-smi or K8s metrics
        return 0.0

    def should_admit_job(self, job_priority: int, estimated_vram_mb: int) -> tuple[bool, str]:
        """
        Queue admission control.
        Returns (admit: bool, reason: str)
        
        Reject if:
        - GPU saturation > 90%
        - Queue depth > threshold (100 jobs default)
        - VRAM would exceed available by > 20%
        """
        saturation = self.get_gpu_saturation()

        if saturation > 0.90:
            return False, f"GPU saturation {saturation:.0%} > 90%"

        if self._get_queue_depth() > 100:
            return False, "Queue depth > 100"

        # Estimate post-allocation saturation
        estimated_saturation = saturation + (estimated_vram_mb / 10240)  # 10.5GB max
        if estimated_saturation > 1.10:
            return False, f"Estimated VRAM {estimated_saturation:.0%} would exceed 110%"

        return True, "Admitted"

    def _get_queue_depth(self) -> int:
        """Get current queue depth from Redis."""
        if self.redis_client:
            try:
                return self.redis_client.zcard("roma:queue")
            except Exception:
                return 0
        return 0

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _get_k8s_field(self, job_id: str, field: str) -> Optional[Any]:
        """Query K8s for job field (via kubectl or K8s API)."""
        # Placeholder — integrate with kubernetes client
        return None

    def _get_redis_field(self, job_id: str, field: str) -> Optional[Any]:
        """Query Redis for job field."""
        if self.redis_client:
            try:
                key = f"roma:job:{job_id}:{field}"
                return self.redis_client.get(key)
            except Exception:
                return None
        return None

    def _reconstruct_from_event_store(self, job_id: str, field: str) -> Optional[Any]:
        """Reconstruct field value by replaying event log."""
        if self.event_store:
            events = self.event_store.get_events_for_job(job_id)
            state = {}
            for event in events:
                if event.payload and field in event.payload:
                    state[field] = event.payload[field]
            return state.get(field)
        return None