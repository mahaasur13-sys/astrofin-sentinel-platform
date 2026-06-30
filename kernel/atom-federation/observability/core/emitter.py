"""
ObservabilityEmitter v7.0 — Unified single-point observability for ATOMFederationOS.

Wiring principle (Step 2.5):
  Event = single source of truth
  ↓
  event_store.append()    ← failure_replay (deterministic log)
  ↓
  _to_metrics()           ← Prometheus counters/gauges/histograms
  ↓
  _to_traces()            ← OpenTelemetry spans (optional)

Usage:
  from observability.core import ObservabilityEmitter

  emitter = ObservabilityEmitter(node_id="node-a", event_store_path="/tmp/events.db")
  emitter.emit(
      event_type="coherence.drift.detected",
      payload={"drift_score": 0.23, "epsilon": 0.05, "corrected": True},
  )

  # Prometheus /metrics endpoint:
  print(emitter.metrics.render_prometheus())

  # Replay:
  for event in emitter.replay_engine.replay():
      process(event)
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from typing import Any

from observability.core.atom_metrics import InMemoryPrometheusEmitter
from observability.core.event_schema import (
    CoherenceStateSnapshot,
    Event,
    EventType,
    LatticeSnapshot,
    QuorumSnapshot,
    SBSStateSnapshot,
    validate_payload,
)


class ObservabilityEmitter:
    """
    Single unified entry point for all observability emission.

    Guarantees:
      - Every emit() goes to event_store (replay)
      - Every emit() updates Prometheus metrics
      - Optionally emits OTel spans (if tracer is set)
      - payload is validated against PAYLOAD_SCHEMAS before emission
      - event_id is globally unique (uuid4 hex)
      - ts is nanosecond Unix timestamp
    """

    def __init__(
        self,
        node_id: str,
        event_store_path: str,
        otel_tracer: Any | None = None,
    ) -> None:
        self.node_id = node_id

        # ── Replay layer ────────────────────────────────────────────────
        from failure_replay.event_store import EventStore
        from failure_replay.replay_engine import ReplayEngine
        self._event_store = EventStore(db_path=event_store_path, node_id=node_id)
        self.replay_engine = ReplayEngine(event_store=self._event_store)

        # ── Metrics layer ──────────────────────────────────────────────
        self.metrics = InMemoryPrometheusEmitter()

        # ── Tracing layer ───────────────────────────────────────────────
        self._otel_tracer = otel_tracer  # opentelemetry.trace.get_tracer(...)
        self._active_span: Any | None = None

        # ── Callbacks ───────────────────────────────────────────────────
        self._on_emit: list[Callable[[Event], None]] = []

        # Stats
        self._emit_count = 0
        self._last_error: str | None = None

    # ── Public API ─────────────────────────────────────────────────────────────

    def emit(
        self,
        event_type: str,
        payload: dict[str, Any],
        coherence_state: CoherenceStateSnapshot | None = None,
        lattice_snapshot: LatticeSnapshot | None = None,
        quorum_snapshot: QuorumSnapshot | None = None,
        sbs_state: SBSStateSnapshot | None = None,
        _skip_metrics: bool = False,
    ) -> Event:
        """
        Emit a structured event.

        Args:
            event_type:    EventType.value string, e.g. "coherence.drift.detected"
            payload:       event-specific fields
            coherence_state: optional coherence subsystem snapshot
            lattice_snapshot: optional lattice subsystem snapshot
            quorum_snapshot:  optional quorum subsystem snapshot
            sbs_state:       optional SBS subsystem snapshot
            _skip_metrics:   internal flag (True only in replay context)

        Returns:
            the emitted Event

        Raises:
            ValueError: if payload is missing required fields per PAYLOAD_SCHEMAS
        """
        # Validate payload
        errors = validate_payload(event_type, payload)
        if errors:
            self._last_error = "; ".join(errors)
            raise ValueError(f"Invalid event payload: {errors}")

        # Build event
        event = Event(
            ts=time.time_ns(),
            node_id=self.node_id,
            event_type=event_type,
            payload=payload,
            coherence_state=coherence_state,
            lattice_snapshot=lattice_snapshot,
            quorum_snapshot=quorum_snapshot,
            sbs_state=sbs_state,
            event_id=uuid.uuid4().hex,
            version="7.0",
        )

        # ── 1. Append to event store (replay source of truth) ────────────
        self._event_store.append(event)

        # ── 2. Update Prometheus metrics ─────────────────────────────────
        if not _skip_metrics:
            self._to_metrics(event)

        # ── 3. Emit OTel span ──────────────────────────────────────────
        if self._otel_tracer is not None and not _skip_metrics:
            self._to_trace(event)

        # ── 4. Fire callbacks ───────────────────────────────────────────
        for cb in self._on_emit:
            try:
                cb(event)
            except Exception:
                pass

        self._emit_count += 1
        return event

    def on_emit(self, cb: Callable[[Event], None]) -> None:
        """Register a callback fired after each emit."""
        self._on_emit.append(cb)

    def replay(self, from_ts: int | None = None):
        """Yield all events from store (for testing/validation)."""
        store = self._event_store
        if from_ts is not None:
            for event in store.query():
                if event.ts >= from_ts:
                    yield event
        else:
            yield from store.query()

    # ── Metric update ──────────────────────────────────────────────────────────

    def _to_metrics(self, event: Event) -> None:
        """Fan out event → Prometheus counters/gauges/histograms."""
        et = event.event_type
        payload = event.payload
        # node_id from payload takes precedence (affected node);
        # event.node_id is the detecting node (used when payload has no node_id)
        node_id = payload.get("node_id", event.node_id)
        node_labels = {"node_id": node_id}

        try:
            if et == EventType.SBS_VIOLATION.value:
                self.metrics.inc_counter(
                    "atom_sbs_violations_total",
                    {**node_labels, "violation_type": payload.get("severity", "unknown").lower()}
                )

            elif et == EventType.COHERENCE_DRIFT_DETECTED.value:
                self.metrics.set_gauge(
                    "atom_coherence_drift_score", node_labels,
                    float(payload.get("drift_score", 0.0))
                )

            elif et == EventType.COHERENCE_DRIFT_RESOLVED.value:
                self.metrics.set_gauge(
                    "atom_coherence_drift_score", node_labels,
                    float(payload.get("drift_score", 0.0))
                )

            elif et == EventType.LATTICE_DECISION.value:
                self.metrics.inc_counter(
                    "atom_lattice_decisions_total",
                    {**node_labels, "decision_type": payload.get("decision_type", "unknown")}
                )

            elif et == EventType.LATTICE_FAILOVER.value:
                self.metrics.inc_counter(
                    "atom_lattice_decisions_total",
                    {**node_labels, "decision_type": "failover"}
                )

            elif et == EventType.HEALER_REPAIR_START.value:
                queue_depth = self.metrics.get_gauge(
                    "atom_healer_queue_depth", node_labels
                )
                self.metrics.set_gauge(
                    "atom_healer_queue_depth", node_labels, queue_depth + 1
                )

            elif et == EventType.HEALER_REPAIR_COMPLETE.value:
                repair_type = payload.get("repair_type", "unknown")
                self.metrics.inc_counter(
                    "atom_healer_repair_total",
                    {**node_labels, "repair_type": repair_type}
                )
                duration_s = float(payload.get("duration_ms", 0)) / 1000.0
                self.metrics.observe_histogram(
                    "atom_healer_repair_duration_seconds",
                    {**node_labels, "repair_type": repair_type}, duration_s
                )
                queue_depth = self.metrics.get_gauge(
                    "atom_healer_queue_depth", node_labels
                )
                self.metrics.set_gauge(
                    "atom_healer_queue_depth", node_labels, max(0, queue_depth - 1)
                )

            elif et == EventType.HEALER_REPAIR_FAILED.value:
                self.metrics.inc_counter(
                    "atom_healer_repair_total",
                    {**node_labels, "repair_type": payload.get("repair_type", "unknown")}
                )
                queue_depth = self.metrics.get_gauge(
                    "atom_healer_queue_depth", node_labels
                )
                self.metrics.set_gauge(
                    "atom_healer_queue_depth", node_labels, max(0, queue_depth - 1)
                )

            elif et == EventType.RPC_ERROR.value:
                self.metrics.inc_counter(
                    "atom_rpc_errors_total",
                    {
                        **node_labels,
                        "peer_id": payload.get("peer_id", "unknown"),
                        "method": payload.get("method", "unknown"),
                        "error_type": payload.get("error_type", "unknown"),
                    }
                )

            elif et == EventType.RPC_DROP.value:
                self.metrics.inc_counter(
                    "atom_rpc_errors_total",
                    {
                        **node_labels,
                        "peer_id": payload.get("peer_id", "unknown"),
                        "method": payload.get("method", "unknown"),
                        "error_type": "drop",
                    }
                )

            elif et == EventType.NODE_HEARTBEAT.value:
                self.metrics.set_gauge(
                    "atom_cluster_healthy_nodes", {}, 1.0  # cluster-level gauge
                )

            elif et == EventType.QUORUM_LOST.value:
                self.metrics.set_gauge(
                    "atom_quorum_health", node_labels, 0.0
                )

            elif et == EventType.QUORUM_RECOVERED.value:
                self.metrics.set_gauge(
                    "atom_quorum_health", node_labels, 1.0
                )

        except Exception as exc:
            self._last_error = f"_to_metrics failed: {exc}"

    # ── OTel trace ─────────────────────────────────────────────────────────────

    def _to_trace(self, event: Event) -> None:
        """Emit an OTel span linked to the event."""
        if self._otel_tracer is None:
            return
        try:
            with self._otel_tracer.start_as_current_span(
                event.event_type.replace(".", "_")
            ) as span:
                span.set_attribute("event.node_id", event.node_id)
                span.set_attribute("event.event_id", event.event_id)
                for k, v in event.payload.items():
                    span.set_attribute(f"event.payload.{k}", str(v))
                if event.coherence_state:
                    span.set_attribute(
                        "coherence.drift_score", event.coherence_state.drift_score
                    )
        except Exception as exc:
            self._last_error = f"_to_trace failed: {exc}"

    # ── Stats ───────────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        return {
            "emit_count": self._emit_count,
            "last_error": self._last_error,
            "store_count": len(self._event_store.query()),
        }
