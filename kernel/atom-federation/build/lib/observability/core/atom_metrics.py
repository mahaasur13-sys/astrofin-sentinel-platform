"""
Metrics Emitter v7.0 — Prometheus bridge for ATOMFederationOS.

Maps events → Prometheus counters/gauges/histograms.
Serves as the /metrics endpoint handler.
"""

from __future__ import annotations

from observability.core.metrics_schema import METRICS_SCHEMA, validate_metric_labels


class InMemoryPrometheusEmitter:
    """
    In-process Prometheus-compatible metric store.

    Suitable for:
      - Unit tests
      - Standalone processes (no actual Prometheus scrape needed)
      - Pre-validation before wiring to real prometheus_client

    Thread-safe via Python GIL (all state dict access is atomic for small objects).
    """

    def __init__(self) -> None:
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}
        self._label_sets: dict[str, set[tuple]] = {}

    # ── Counter ────────────────────────────────────────────────────────────────

    def inc_counter(self, name: str, labels: dict[str, str], value: float = 1.0) -> None:
        errors = validate_metric_labels(name, labels)
        if errors:
            raise ValueError(f"Invalid metric labels: {errors}")

        key = self._make_key(name, labels)
        self._counters[key] = self._counters.get(key, 0.0) + value
        self._record_label_set(name, labels)

    # ── Gauge ─────────────────────────────────────────────────────────────────

    def set_gauge(self, name: str, labels: dict[str, str], value: float) -> None:
        errors = validate_metric_labels(name, labels)
        if errors:
            raise ValueError(f"Invalid metric labels: {errors}")

        key = self._make_key(name, labels)
        self._gauges[key] = value
        self._record_label_set(name, labels)

    # ── Histogram ─────────────────────────────────────────────────────────────

    def observe_histogram(self, name: str, labels: dict[str, str], value: float) -> None:
        errors = validate_metric_labels(name, labels)
        if errors:
            raise ValueError(f"Invalid metric labels: {errors}")

        key = self._make_key(name, labels)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)
        self._record_label_set(name, labels)

    # ── Query (for testing / validation) ──────────────────────────────────────

    def get_counter(self, name: str, labels: dict[str, str]) -> float:
        key = self._make_key(name, labels)
        return self._counters.get(key, 0.0)

    def get_gauge(self, name: str, labels: dict[str, str]) -> float:
        key = self._make_key(name, labels)
        return self._gauges.get(key, 0.0)

    def get_histogram_samples(self, name: str, labels: dict[str, str]) -> list[float]:
        key = self._make_key(name, labels)
        return list(self._histograms.get(key, []))

    def get_all_labels(self, name: str) -> set[tuple]:
        """Return all label tuples ever used for a given metric."""
        return self._label_sets.get(name, set())

    def get_metric_type(self, name: str) -> str | None:
        spec = METRICS_SCHEMA.get(name)
        return spec.get("type") if spec else None

    # ── Prometheus /metrics text format ──────────────────────────────────────

    def render_prometheus(self) -> str:
        """Render all metrics in Prometheus text format."""
        lines = ["# HELP atom_metrics ATOMFederationOS metrics", "# TYPE atom_metrics gauge"]

        def fmt_labels(labels: dict[str, str]) -> str:
            if not labels:
                return ""
            parts = [f'{k}="{v}"' for k, v in sorted(labels.items())]
            return "{" + ",".join(parts) + "}"

        # Gauges
        for key, val in sorted(self._gauges.items()):
            name, labels = self._parse_key(key)
            # name already carries 'atom_' prefix — strip it before prepending
            base_name = name[5:] if name.startswith("atom_") else name
            lines.append(f"atom_{base_name}{fmt_labels(labels)} {val}")

        # Counters  (Prometheus convention: _total suffix is part of the metric type, not stripped)
        for key, val in sorted(self._counters.items()):
            name, labels = self._parse_key(key)
            # name carries 'atom_' prefix from storage — strip it before rendering
            base_name = name[5:] if name.startswith("atom_") else name
            lines.append(f"atom_{base_name}{fmt_labels(labels)} {val}")

        # Histograms (with bucket accumulation)
        for key, vals in sorted(self._histograms.items()):
            name, labels = self._parse_key(key)
            base_name = name[5:] if name.startswith("atom_") else name
            spec = METRICS_SCHEMA.get(name, {})
            buckets = spec.get("buckets", [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0])
            labels_str = fmt_labels(labels)
            sorted_vals = sorted(vals)
            total = len(sorted_vals)

            cumulative = 0
            for bound in buckets:
                count = sum(1 for v in sorted_vals if v <= bound)
                cumulative = count
                lines.append(f"atom_{base_name}_bucket{labels_str},le={bound} {count}")
            lines.append(f"atom_{base_name}_bucket{labels_str},le=+Inf {total}")
            lines.append(f"atom_{base_name}_sum{labels_str} {sum(sorted_vals):.6f}")
            lines.append(f"atom_{base_name}_count{labels_str} {total}")

        return "\n".join(lines) + "\n"

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _make_key(name: str, labels: dict[str, str]) -> str:
        """Stable key for (name, labels). Name may already carry the 'atom_' prefix."""
        label_items = sorted(labels.items())
        return f"{name}#{sum(hash(v) for v in labels.values())}#{label_items}"

    @staticmethod
    def _parse_key(key: str) -> tuple[str, dict[str, str]]:
        """Reverse _make_key — extracts metric name and label dict."""
        # Format: "atom_replay_events_applied_total#hashval#[(k,v), ...]"
        parts = key.split("#", 2)
        name = parts[0]  # already includes 'atom_' prefix if present
        if len(parts) >= 3:
            import ast
            label_items = ast.literal_eval(parts[2])
            labels = dict(label_items)
        else:
            labels = {}
        return name, labels

    def _record_label_set(self, name: str, labels: dict[str, str]) -> None:
        if name not in self._label_sets:
            self._label_sets[name] = set()
        self._label_sets[name].add(tuple(sorted(labels.items())))

    # ── Convenience: bulk emit from event ─────────────────────────────────────

    def emit_from_event(self, event_type: str, payload: dict, node_id: str) -> None:
        """
        Auto-map event type → metric increments.
        Used when wiring is not explicit.
        """
        node_labels = {"node_id": node_id}

        if event_type == "sbs.violation":
            self.inc_counter("atom_sbs_violations_total",
                            {**node_labels, "violation_type": payload.get("severity", "unknown").lower()})

        elif event_type == "coherence.drift.detected":
            self.set_gauge("atom_coherence_drift_score", node_labels, payload.get("drift_score", 0.0))

        elif event_type == "lattice.decision":
            self.inc_counter("atom_lattice_decisions_total",
                             {**node_labels, "decision_type": payload.get("decision_type", "unknown")})

        elif event_type == "healer.repair.start":
            self.set_gauge("atom_healer_queue_depth", node_labels,
                          max(0, self.get_gauge("atom_healer_queue_depth", node_labels) + 1))

        elif event_type == "healer.repair.complete":
            repair_type = payload.get("repair_type", "unknown")
            self.inc_counter("atom_healer_repair_total",
                             {**node_labels, "repair_type": repair_type})
            duration = payload.get("duration_ms", 0.0) / 1000.0
            self.observe_histogram("atom_healer_repair_duration_seconds",
                                  {**node_labels, "repair_type": repair_type}, duration)

        elif event_type == "rpc.drop":
            self.inc_counter("atom_rpc_requests_total",
                             {**node_labels,
                              "peer_id": payload.get("peer_id", "unknown"),
                              "method": payload.get("method", "unknown")})
            self.inc_counter("atom_rpc_errors_total",
                             {**node_labels,
                              "peer_id": payload.get("peer_id", "unknown"),
                              "method": payload.get("method", "unknown"),
                              "error_type": "drop"})


# Aliases for backward compatibility with existing __init__.py exports
PrometheusMetrics = InMemoryPrometheusEmitter
NodeMetricsEmitter = InMemoryPrometheusEmitter


# ── Global singleton (used by ReplayObservabilitySubscriber) ────────────────────

prom_metrics = InMemoryPrometheusEmitter()
