# =============================================================================
# ROMA Consistency & Control Model Layer
# =======================================
#
# What it does:
# - GlobalStateModel: single source of truth hierarchy (K8s > Redis > Event Store)
# - BackpressureSystem: GPU saturation + queue throttling + admission control
#
# Truth hierarchy:
#   1. K8s (physical truth for running jobs)
#   2. Redis (logical cache for queued/scheduled)
#   3. Event Store (append-only historical log)
#   4. State Snapshots (derived, for fast recovery)
#
# Key invariant:
#   ∀ job: consistent(job) = (k8s_state == redis_state == event_store_replay)
#
# When invariant breaks → ReconciliationEngine.trigger_repair()
#
# Backpressure rules:
#   - GPU VRAM > 90% → stop admitting GPU jobs
#   - Queue depth > 100 → stop admitting
#   - Cooldown 30s after backpressure trigger
#
# =============================================================================

from consistency.global_state_model import (
    GlobalStateModel,
    TruthSource,
    ConflictResolution,
    GlobalStateRecord,
)

from consistency.backpressure import (
    BackpressureSystem,
    BackpressureConfig,
    BackpressureStatus,
)

__all__ = [
    "GlobalStateModel",
    "TruthSource",
    "ConflictResolution",
    "GlobalStateRecord",
    "BackpressureSystem",
    "BackpressureConfig",
    "BackpressureStatus",
]
