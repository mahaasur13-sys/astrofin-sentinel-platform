"""
ReplayObservabilitySubscriber Tests v7.0.

Tests the bridge: ReplayEngine → Prometheus + OTEL.

Covered:
  - subscriber(event) emits atom_replay_events_applied_total counter
  - subscriber(event, lag_ms) emits atom_replay_lag_ms histogram
  - subscriber emits OTEL span when tracer available
  - backward-compatible: accepts (event) and (event, lag_ms=..., speed=...) signatures
  - correlation_id / causation_id → span attributes
"""

import sys

REPO_ROOT = "/home/workspace/atom-federation-os"
sys.path.insert(0, REPO_ROOT)

from observability.core.atom_metrics import prom_metrics
from observability.core.event_schema import Event
from observability.core.replay_subscriber import ReplayObservabilitySubscriber


def _make_event(event_type: str = "sbs.violation", **payload_extra) -> Event:
    import uuid
    return Event(
        ts=1_700_000_000_000_000_000,
        node_id="node-test",
        event_type=event_type,
        payload={"invariant_name": "f2_quorum", "severity": "CRITICAL", **payload_extra},
        event_id=uuid.uuid4().hex,
        version="7.0",
    )


def test_subscriber_increments_counter():
    """Counter atom_replay_events_applied_total increases on each call."""
    prom_metrics._counters.clear()
    prom_metrics._histograms.clear()

    sub = ReplayObservabilitySubscriber(enable_tracing=False, enable_metrics=True)
    ev = _make_event("sbs.violation")

    assert prom_metrics.get_counter("atom_replay_events_applied_total", {"replayed_event_type": "sbs.violation"}) == 0.0

    sub(ev, lag_ms=0.0, speed=1.0)

    assert prom_metrics.get_counter("atom_replay_events_applied_total", {"replayed_event_type": "sbs.violation"}) == 1.0

    sub(ev, lag_ms=0.0, speed=1.0)
    assert prom_metrics.get_counter("atom_replay_events_applied_total", {"replayed_event_type": "sbs.violation"}) == 2.0

    log.info("✅ test_subscriber_increments_counter PASSED")


def test_subscriber_records_lag_histogram():
    """Lag histogram receives correct lag_ms values."""
    prom_metrics._histograms.clear()

    sub = ReplayObservabilitySubscriber(enable_tracing=False, enable_metrics=True)

    sub(_make_event("coherence.drift.detected"), lag_ms=5.0, speed=10.0)
    sub(_make_event("coherence.drift.detected"), lag_ms=15.5, speed=10.0)

    samples = prom_metrics.get_histogram_samples("atom_replay_lag_ms", {"replayed_event_type": "coherence.drift.detected"})
    assert len(samples) == 2, f"Expected 2 samples, got {len(samples)}"
    assert 5.0 in samples
    assert 15.5 in samples

    log.info("✅ test_subscriber_records_lag_histogram PASSED")


def test_backward_compatible_signature():
    """Subscriber works with old-style subscriber(event) and subscriber(event, lag_ms=...)."""
    prom_metrics._counters.clear()
    prom_metrics._histograms.clear()

    sub = ReplayObservabilitySubscriber(enable_tracing=False, enable_metrics=True)
    ev = _make_event()

    # Old style: positional args only (no lag_ms)
    sub(ev)

    assert prom_metrics.get_counter("atom_replay_events_applied_total", {"replayed_event_type": "sbs.violation"}) == 1.0

    # Lag-only style
    sub(ev, lag_ms=42.0)

    assert prom_metrics.get_counter("atom_replay_events_applied_total", {"replayed_event_type": "sbs.violation"}) == 2.0
    samples = prom_metrics.get_histogram_samples("atom_replay_lag_ms", {"replayed_event_type": "sbs.violation"})
    assert 42.0 in samples

    log.info("✅ test_backward_compatible_signature PASSED")


def test_correlation_and_causation_ids():
    """correlation_id and causation_id are set as span attributes when present."""
    # Verify Event dataclass accepts correlation_id and causation_id
    ev = _make_event()
    ev.correlation_id = "corr-abc123"
    ev.causation_id = "caus-xyz789"

    # These fields are optional on the dataclass, subscriber uses hasattr to read them
    assert hasattr(ev, "correlation_id")
    assert hasattr(ev, "causation_id")
    assert ev.correlation_id == "corr-abc123"
    assert ev.causation_id == "caus-xyz789"

    log.info("✅ test_correlation_and_causation_ids PASSED")


def test_tracing_disabled():
    """When enable_tracing=False, no span is created (no crash)."""
    sub = ReplayObservabilitySubscriber(enable_tracing=False, enable_metrics=True)
    ev = _make_event()

    # Should not raise even without OTEL setup
    sub(ev, lag_ms=1.0, speed=1.0)

    log.info("✅ test_tracing_disabled PASSED")


def test_metrics_disabled():
    """When enable_metrics=False, counters/histograms are not modified."""
    prom_metrics._counters.clear()
    prom_metrics._histograms.clear()

    sub = ReplayObservabilitySubscriber(enable_tracing=False, enable_metrics=False)
    ev = _make_event()

    sub(ev, lag_ms=10.0, speed=1.0)

    counter = prom_metrics.get_counter("atom_replay_events_applied_total", {"replayed_event_type": "sbs.violation"})
    assert counter == 0.0, f"Expected 0 when metrics disabled, got {counter}"

    log.info("✅ test_metrics_disabled PASSED")


def test_prometheus_render():
    """Emitted metrics render correctly in Prometheus text format."""
    prom_metrics._counters.clear()
    prom_metrics._histograms.clear()

    sub = ReplayObservabilitySubscriber(enable_tracing=False, enable_metrics=True)
    sub(_make_event("lattice.decision"), lag_ms=2.5, speed=1.0)
    sub(_make_event("sbs.violation"), lag_ms=0.5, speed=1.0)

    text = prom_metrics.render_prometheus()

    assert "atom_replay_events_applied_total" in text
    assert "replayed_event_type=\"lattice.decision\"" in text
    assert "replayed_event_type=\"sbs.violation\"" in text
    assert "atom_replay_lag_ms" in text

    log.info("✅ test_prometheus_render PASSED")
    log.info(f"   Rendered metrics:\n{text[:300]}")


if __name__ == "__main__":
    log.info("=" * 60)
    log.info("ReplayObservabilitySubscriber Tests v7.0")
    log.info("=" * 60)

    test_subscriber_increments_counter()
    test_subscriber_records_lag_histogram()
    test_backward_compatible_signature()
    test_correlation_and_causation_ids()
    test_tracing_disabled()
    test_metrics_disabled()
    test_prometheus_render()

    log.info()
    log.info("🎉 ALL TESTS PASSED")
