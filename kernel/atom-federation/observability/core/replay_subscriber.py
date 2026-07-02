"""
Replay Observability Subscriber v7.0.

Bridges ReplayEngine → Prometheus + OTEL.
Every applied replay event emits:
  - counter: atom_replay_events_applied_total{replayed_event_type=...}
  - histogram: atom_replay_lag_ms{replayed_event_type=...}
  - OTEL span: replay.apply_event with event.id, event.type, replay.lag_ms, replay.speed

Usage:
    from failure_replay.replay_engine import ReplayEngine
    from observability.core.replay_subscriber import ReplayObservabilitySubscriber

    subscriber = ReplayObservabilitySubscriber(
        enable_tracing=True,
        enable_metrics=True,
    )
    engine.add_subscriber(subscriber)
"""

from __future__ import annotations

from observability.core.atom_metrics import prom_metrics  # global singleton
from observability.core.event_schema import Event
from observability.core.otel_instrumentation import get_tracer


class ReplayObservabilitySubscriber:
    """
    Subscriber that emits Prometheus metrics + OTEL traces for each replayed event.

    Supports three calling signatures (backward compatible):
      - subscriber(event)                        — old style, no lag/speed
      - subscriber(event, lag_ms=...)             — lag only
      - subscriber(event, lag_ms=..., speed=...) — full signature

    Metrics emitted:
      atom_replay_events_applied_total{replayed_event_type=...}
      atom_replay_lag_ms_bucket{replayed_event_type=...,le=...}
      atom_replay_lag_ms_sum{replayed_event_type=...}
      atom_replay_lag_ms_count{replayed_event_type=...}

    Spans emitted:
      replay.apply_event
        event.id       = event.event_id
        event.type     = event.event_type
        replay.lag_ms  = lag_ms
        replay.speed   = speed
        node.id        = event.node_id
        correlation.id = event.correlation_id (if present)
        causation.id   = event.causation_id (if present)
    """

    def __init__(
        self,
        enable_tracing: bool = True,
        enable_metrics: bool = True,
    ) -> None:
        self.enable_tracing = enable_tracing
        self.enable_metrics = enable_metrics

    def __call__(
        self,
        event: Event,
        lag_ms: float = 0.0,
        speed: float = 1.0,
        **kwargs,
    ) -> None:
        if self.enable_metrics:
            self._emit_metrics(event, lag_ms)

        if self.enable_tracing:
            self._emit_trace(event, lag_ms, speed)

    def _emit_metrics(self, event: Event, lag_ms: float) -> None:
        label = {"replayed_event_type": event.event_type}

        prom_metrics.inc_counter(
            "atom_replay_events_applied_total",
            labels=label,
        )

        prom_metrics.observe_histogram(
            "atom_replay_lag_ms",
            value=lag_ms,
            labels=label,
        )

    def _emit_trace(
        self,
        event: Event,
        lag_ms: float,
        speed: float,
    ) -> None:
        tracer = get_tracer()
        if tracer is None:
            return

        span_name = f"replay.apply_event[{event.event_type}]"

        try:
            span = tracer.start_span(span_name)
        except Exception:
            return

        with span:
            span.set_attribute("event.id", event.event_id)
            span.set_attribute("event.type", event.event_type)
            span.set_attribute("replay.lag_ms", lag_ms)
            span.set_attribute("replay.speed", speed)
            span.set_attribute("node.id", event.node_id)

            if hasattr(event, "correlation_id") and event.correlation_id:
                span.set_attribute("correlation.id", event.correlation_id)

            if hasattr(event, "causation_id") and event.causation_id:
                span.set_attribute("causation.id", event.causation_id)

            for key, value in event.payload.items():
                try:
                    span.set_attribute(f"payload.{key}", str(value) if value is not None else "")
                except Exception:
                    pass
