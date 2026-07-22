"""Tests for atom_operator — covers the Phase-2.A bug fixes."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `import atom_operator...` when running from this directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from atom_operator.client import K8sClient
from atom_operator.controller import ATOMController
from atom_operator.health import _HealthState
from atom_operator.reconciler import Reconciler
from atom_operator.state import NodeState, _parse_heal_time


class FakeK8s(K8sClient):
    """In-memory K8sClient — no network, no /version probe."""


def test_reconciler_accepts_k8s():
    """Bug 1: Reconciler.__init__ must take a K8sClient (was: TypeError at startup)."""
    r = Reconciler(k8s=FakeK8s())
    assert r.k8s is not None
    assert r.reconcile({"metadata": {"name": "demo"}}) == {
        "status": "ok",
        "object": {"metadata": {"name": "demo"}},
    }


def test_controller_construction():
    """Bug 1 follow-up: ATOMController(K8sClient()) must not raise at __init__."""
    ctrl = ATOMController(FakeK8s(), poll_interval=10.0)
    assert ctrl.poll_interval == 10.0
    assert isinstance(ctrl.reconciler, Reconciler)
    assert ctrl.reconciler.k8s is not None


def test_refresh_custom_api_no_dynamic():
    """Bug 2: refresh_custom_api must not eagerly call /version via DynamicClient."""
    k = FakeK8s()
    k.refresh_custom_api()
    from kubernetes.client import ApiClient
    assert isinstance(k.custom.api_client, ApiClient)
    assert not hasattr(k, "dynamic_client") or k.dynamic_client is None


def test_node_state_iso_roundtrip():
    """Bug 3: last_heal_time round-trips ISO-string <-> float."""
    iso = "2026-06-19T12:00:00Z"
    parsed = _parse_heal_time(iso)
    assert isinstance(parsed, float)
    ns = NodeState.from_k8s({"nodeId": "n1", "lastHealTime": iso})
    assert ns.last_heal_time == parsed
    out = ns.to_k8s()
    assert out["lastHealTime"] == iso


def test_node_state_numeric_passthrough():
    """Bug 3: numeric epoch values pass through unchanged."""
    n = NodeState.from_k8s({"nodeId": "n1", "lastHealTime": 1718800000.5})
    assert n.last_heal_time == 1718800000.5
    assert n.to_k8s()["lastHealTime"].startswith("2024-")


def test_node_state_empty_value():
    """Bug 3: empty / missing lastHealTime must produce None, not crash."""
    assert NodeState.from_k8s({}).last_heal_time is None
    assert NodeState.from_k8s({"lastHealTime": ""}).last_heal_time is None


def test_health_state_lifecycle():
    """Sanity: _HealthState transitions match the /healthz /readyz contract."""
    s = _HealthState()
    assert s.is_alive() and not s.is_ready()
    s.mark_ready()
    assert s.is_ready()
    s.mark_not_ready()
    assert not s.is_ready()
    assert s.is_alive()  # alive flag independent from ready
