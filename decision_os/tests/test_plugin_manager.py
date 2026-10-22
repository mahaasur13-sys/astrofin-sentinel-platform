"""Tests for DecisionOS Plugin Architecture."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from decision_os.core.plugin_manager import PluginManager, PluginManifest, PluginState, ThoughtTracer, TraceLevel


@pytest.fixture
def fresh_manager() -> PluginManager:
    """Clean PluginManager per test."""
    return PluginManager(tenant_tier="Pro")


@pytest.fixture
def sample_manifest() -> PluginManifest:
    return PluginManifest(
        plugin_id="test-plugin",
        name="Test Plugin",
        version="1.0.0",
        description="A test plugin",
        author="Test Team",
        permissions=["support:chat:send"],
        hooks=["before_test"],
        tier_required=["Pro"],
        entry_point="main.py",
    )


# ────────────────────── Manifest Tests ──────────────────────

def test_manifest_from_json():
    manifest = PluginManifest.from_json(Path(__file__).parent / "fixtures/sample_manifest.json")
    assert manifest.plugin_id == "sample-plugin"
    assert manifest.version == "2.0.0"


# ────────────────────── Install Tests ──────────────────────

def test_install_plugin(fresh_manager: PluginManager, sample_manifest: PluginManifest):
    instance = fresh_manager.install(sample_manifest)
    assert instance.state == PluginState.INSTALLED
    assert fresh_manager.registry.get("test-plugin") is not None


def test_install_duplicate_enabled(fresh_manager: PluginManager, sample_manifest: PluginManifest):
    fresh_manager.install(sample_manifest)
    with pytest.raises(RuntimeError):
        fresh_manager.install(sample_manifest)


# ────────────────────── Discover Tests ──────────────────────

def test_discover_builtin(fresh_manager: PluginManager):
    manifests = fresh_manager.discover()
    assert "policy-engine" in manifests
    assert "dashboard" in manifests


# ────────────────────── Lifecycle Tests ──────────────────────

def test_disable_plugin(fresh_manager: PluginManager, sample_manifest: PluginManifest):
    fresh_manager.install(sample_manifest)
    fresh_manager.disable("test-plugin")
    entry = fresh_manager.registry.get("test-plugin")
    assert entry.state == PluginState.DISABLED


def test_unload_plugin(fresh_manager: PluginManager, sample_manifest: PluginManifest):
    fresh_manager.install(sample_manifest)
    fresh_manager.unload("test-plugin")
    entry = fresh_manager.registry.get("test-plugin")
    assert entry.state == PluginState.UNLOADED


def test_plugin_not_found(fresh_manager: PluginManager):
    with pytest.raises(KeyError):
        fresh_manager.disable("nonexistent")


# ────────────────────── Hook System Tests ──────────────────────

def test_hook_registration(fresh_manager: PluginManager):
    calls = []

    def handler(**ctx):
        calls.append(ctx)
        return {"ok": True}

    fresh_manager.hook_system.register("before_test", "test-hook", handler)
    results = fresh_manager.hook_system.fire("before_test", user_id="u1")
    assert len(results) == 1
    assert results[0]["ok"] is True


def test_hook_unregister(fresh_manager: PluginManager):
    calls = []

    def handler(**ctx):
        calls.append(1)

    fresh_manager.hook_system.register("event", "p1", handler)
    fresh_manager.hook_system.unregister_plugin("p1")
    results = fresh_manager.hook_system.fire("event")
    assert results == []


# ────────────────────── Thought Tracer Tests ──────────────────────

def test_tracer(fresh_manager: PluginManager):
    tracer = fresh_manager.thought_tracer
    tracer.trace(TraceLevel.DECISION, "p1", "agent-a", "decision made", x=1)
    entries = tracer.last_entries(10)
    assert len(entries) == 1
    assert entries[0].plugin_id == "p1"
    assert entries[0].level == TraceLevel.DECISION


def test_tracer_max_entries(fresh_manager: PluginManager):
    tracer = ThoughtTracer(max_entries=5)
    for i in range(10):
        tracer.trace(TraceLevel.INFO, "p1", "agent", f"msg {i}")
    assert len(tracer.last_entries(100)) == 5


# ────────────────────── Sandbox Tests ──────────────────────

def test_sandbox_validate(fresh_manager: PluginManager, sample_manifest: PluginManifest):
    assert fresh_manager.sandbox.validate(sample_manifest)


def test_sandbox_reject_empty(fresh_manager: PluginManager):
    m = PluginManifest(
        plugin_id="", name="", version="", description="", author="",
        permissions=[], hooks=[], tier_required=[], entry_point="",
    )
    assert not fresh_manager.sandbox.validate(m)


# ────────────────────── Tier Tests ──────────────────────

def test_pro_tier_allows_dashbeam(fresh_manager: PluginManager):
    m = PluginManifest(
        plugin_id="pro-p", name="Pro", version="1.0", description="", author="",
        permissions=["dashbeam:ticket:create"], hooks=[], tier_required=["Pro"],
        entry_point="main.py",
    )
    allowed = fresh_manager.sandbox.allowed_permissions(m, "Pro")
    assert "dashbeam:ticket:create" in allowed


def test_start_tier_blocks_dashbeam(fresh_manager: PluginManager):
    m = PluginManifest(
        plugin_id="start-p", name="Start", version="1.0", description="", author="",
        permissions=["dashbeam:ticket:create"], hooks=[], tier_required=["Pro"],
        entry_point="main.py",
    )
    allowed = fresh_manager.sandbox.allowed_permissions(m, "Start")
    assert "dashbeam:ticket:create" not in allowed


# ────────────────────── Spend Key Tests ──────────────────────

def test_spend_keys_never_allowed(fresh_manager: PluginManager):
    """Spend key permissions must never be granted to ANY plugin."""
    evil_manifest = PluginManifest(
        plugin_id="evil",
        name="Evil Plugin",
        version="1.0.0",
        description="Mallory's plugin",
        author="Mallory",
        permissions=["spend_key"],
        hooks=[],
        tier_required=["Start"],
        entry_point="main.py",
    )
    allowed = fresh_manager.sandbox.allowed_permissions(evil_manifest, fresh_manager.tenant_tier)
    assert not any("spend" in p for p in allowed), "Spend keys leaked!"


# ────────────────────── Registry Tests ──────────────────────

def test_registry_list_all(fresh_manager: PluginManager, sample_manifest: PluginManifest):
    fresh_manager.install(sample_manifest)
    assert "test-plugin" in fresh_manager.registry.list_all()


def test_registry_remove(fresh_manager: PluginManager, sample_manifest: PluginManifest):
    fresh_manager.install(sample_manifest)
    fresh_manager.registry.remove("test-plugin")
    assert fresh_manager.registry.get("test-plugin") is None
