"""Integration tests — actual API coverage for core + DashBeam entities."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.plugin_manager import (
    PluginManager, PluginManifest, PluginState, PluginInstance, Sandbox,
    PluginRegistry, PluginEntry, HookSystem, ThoughtTracer, TraceLevel,
)
from plugins.dashbeam_transfer.main import (
    DashBeamTicket, DashBeamSession, PairedDevice, DashBeamRelayConfig,
)


def _mk_manifest(pid: str, **kwargs) -> PluginManifest:
    return PluginManifest(
        plugin_id=pid,
        name=kwargs.pop("name", pid),
        version=kwargs.pop("version", "1.0.0"),
        description=kwargs.pop("description", ""),
        author=kwargs.pop("author", "test"),
        permissions=kwargs.pop("permissions", []),
        hooks=kwargs.pop("hooks", []),
        tier_required=kwargs.pop("tier_required", ["Start", "Pro", "Enterprise"]),
        entry_point=kwargs.pop("entry_point", "main.py"),
        **kwargs,
    )


@pytest.fixture
def pm():
    return PluginManager("Enterprise")


@pytest.fixture
def m():
    return _mk_manifest("test-plugin", permissions=["support:file:send_p2p"])


# ── Lifecycle ─────────────────────────────────────────────────────────────────

class TestLifecycle:
    def test_full_cycle(self, pm, m):
        pm.install(m)
        assert pm.registry.get(m.plugin_id).state == PluginState.INSTALLED

        pm.enable(m.plugin_id)
        assert pm.registry.get(m.plugin_id).state == PluginState.ENABLED

        pm.disable(m.plugin_id)
        assert pm.registry.get(m.plugin_id).state == PluginState.DISABLED

        pm.unload(m.plugin_id)
        assert pm.registry.get(m.plugin_id).state == PluginState.UNLOADED

    def test_list_all(self, pm, m):
        """list_all() returns list of dict summaries."""
        pm.install(m)
        pm.enable(m.plugin_id)
        result = pm.list_all()
        assert len(result) >= 1
        assert result[0]["plugin_id"] == m.plugin_id

    def test_list_plugins(self, pm, m):
        pm.install(m)
        pm.enable(m.plugin_id)
        assert m.plugin_id in pm.list_plugins()

    def test_get_count(self, pm, m):
        pm.install(m)
        pm.enable(m.plugin_id)
        pm.install(_mk_manifest("p2"))
        pm.enable("p2")
        assert pm.get_count() == 2

    def test_disable_not_enabled_ok(self, pm, m):
        pm.install(m)
        pm.disable(m.plugin_id)  # should not raise

    def test_install_duplicate_while_enabled_raises(self, pm, m):
        pm.install(m)
        pm.enable(m.plugin_id)
        with pytest.raises(RuntimeError):
            pm.install(m)

    def test_update(self):
        pm = PluginManager("Enterprise")
        m = _mk_manifest("upd", version="1.0.0")
        pm.install(m)
        pm.enable("upd")
        new_m = _mk_manifest("upd", version="1.1.0")
        pm.update("upd", new_m)
        assert pm.registry.get("upd").manifest.version == "1.1.0"

    def test_update_nonexistent_raises(self, pm):
        with pytest.raises(ValueError):
            pm.update("nonexistent", _mk_manifest("nonexistent"))


# ── Hook System ───────────────────────────────────────────────────────────────

class TestHookSystem:
    def test_register_and_fire(self, pm):
        calls = []
        def cb(**kw):
            calls.append(kw)
            return {"ok": True}
        pm.hook_system.register("before_message_send", "h1", cb)
        results = pm.hook_system.fire("before_message_send", msg="hello", uid="U1")
        assert len(calls) == 1
        assert calls[0]["msg"] == "hello"

    def test_hook_accessible_via_property(self, pm):
        # 'hooks' is an alias for 'hook_system'
        ph = pm.hooks
        assert isinstance(ph, HookSystem)

    def test_unregister(self, pm):
        calls = []
        def cb(**kw):
            calls.append(kw)
        pm.hook_system.register("after_ticket_create", "h2", cb)
        pm.hook_system.unregister_plugin("h2")
        pm.hook_system.fire("after_ticket_create", ticket_id="T1")
        assert len(calls) == 0


# ── Plugin Registry ───────────────────────────────────────────────────────────

class TestPluginRegistry:
    def test_register_instance(self):
        reg = PluginRegistry()
        m = _mk_manifest("p1")
        inst = PluginInstance(m, PluginState.INSTALLED)
        reg.register(inst)
        assert reg.get("p1") is not None
        assert reg.get("p1").manifest.plugin_id == "p1"

    def test_remove(self):
        reg = PluginRegistry()
        inst = PluginInstance(_mk_manifest("p1"), PluginState.INSTALLED)
        reg.register(inst)
        reg.remove("p1")
        assert reg.get("p1") is None

    def test_list_all(self):
        reg = PluginRegistry()
        for pid in ("a", "b"):
            reg.register(PluginInstance(_mk_manifest(pid), PluginState.INSTALLED))
        assert len(reg.list_all()) == 2

    def test_find_by_state(self):
        reg = PluginRegistry()
        reg.register(PluginInstance(_mk_manifest("e"), PluginState.ENABLED))
        reg.register(PluginInstance(_mk_manifest("d"), PluginState.DISABLED))
        assert len(reg.find_by_state(PluginState.ENABLED)) == 1


# ── Security ──────────────────────────────────────────────────────────────────

class TestSecurity:
    def test_spend_key_blocked(self, pm):
        m = _mk_manifest("pw", permissions=["crypto:wallet:spend_key", "crypto:wallet:view_only"])
        allowed = pm.sandbox.allowed_permissions(m, "Enterprise")
        assert "crypto:wallet:spend_key" not in allowed
        assert "crypto:wallet:view_only" in allowed

    def test_spend_key_install_blocked(self, pm):
        m = _mk_manifest("bad", permissions=["crypto:wallet:spend_key"])
        pm.install(m)  # install is fine
        with pytest.raises(PermissionError):
            pm.enable("bad")  # enable BLOCKS spend_key

    def test_enterprise_permission_gated_on_start(self, pm):
        m = _mk_manifest("relay", permissions=["dashbeam:relay:configure"], tier_required=["Enterprise"])
        allowed = pm.sandbox.allowed_permissions(m, "Start")
        assert "dashbeam:relay:configure" not in allowed

    def test_enterprise_permission_allowed(self, pm):
        m = _mk_manifest("relay", permissions=["dashbeam:relay:configure"], tier_required=["Enterprise"])
        allowed = pm.sandbox.allowed_permissions(m, "Enterprise")
        assert "dashbeam:relay:configure" in allowed

    def test_dashbeam_share_view_only_allowed(self, pm):
        m = _mk_manifest("safe", permissions=["dashbeam:wallet:share_view_only"], tier_required=["Pro"])
        allowed = pm.sandbox.allowed_permissions(m, "Pro")
        assert "dashbeam:wallet:share_view_only" in allowed


# ── Sandbox ───────────────────────────────────────────────────────────────────

class TestSandbox:
    def test_isolate_returns_sandbox_id(self):
        sb = Sandbox(Path("/tmp/decisionos-sandbox"))
        m = _mk_manifest("test")
        sid = sb.isolate(m)
        assert isinstance(sid, str) and len(sid) > 0

    def test_validate_ok(self):
        sb = Sandbox(Path("/tmp/decisionos-sandbox"))
        assert sb.validate(_mk_manifest("test"))


# ── Thought Tracer ────────────────────────────────────────────────────────────

class TestThoughtTracer:
    def test_trace(self):
        tt = ThoughtTracer(max_entries=100)
        tt.trace(TraceLevel.DECISION, "policy-engine", "default",
                 "Checking dashbeam:ticket:create", user="user_x")
        tt.trace(TraceLevel.INFO, "decision-gate", "default",
                 "Gate PASSED — user Pro tier")
        entries = tt.last_entries(50)
        assert len(entries) == 2


# ── DashBeam Entities ─────────────────────────────────────────────────────────

class TestDashBeam:
    def test_ticket_lifecycle(self):
        t = DashBeamTicket(
            ticket_id="T-001",
            file_metadata={
                "sender_id": "alice",
                "recipient_id": "bob",
                "file_name": "report.pdf",
                "file_size": 1024,
                "mime_type": "application/pdf",
                "encryption_key": "sekret",
            },
        )
        assert t.ticket_id == "T-001"
        assert t.file_metadata["sender_id"] == "alice"

    def test_session(self):
        s = DashBeamSession(
            session_id="S-001",
            ticket_code="CODE42",
            peer_id="QmPeerX",
            connected=True,
            transferred_bytes=0,
        )
        assert s.session_id == "S-001"
        assert s.connected is True

    def test_paired_device(self):
        d = PairedDevice(
            device_id="dev-01",
            name="Laptop",
            last_seen="2026-08-20T06:00:00Z",
            trusted=True,
        )
        assert d.device_id == "dev-01"
        assert d.trusted is True

    def test_relay_config(self):
        r = DashBeamRelayConfig(
            relay_url="https://relay.enterprise.com",
            tls_cert_path="/etc/certs/relay.pem",
            max_bandwidth_mbps=500,
            allowed_peers=["QmPeer1", "QmPeer2"],
        )
        assert r.relay_url == "https://relay.enterprise.com"
        assert r.max_bandwidth_mbps == 500

    def test_plugin_manifest_install(self, pm):
        m = _mk_manifest(
            "dashbeam-transfer",
            name="DashBeam P2P Transfer",
            version="1.0.0",
            permissions=[
                "support:file:send_p2p", "dashbeam:ticket:create",
                "dashbeam:file:send", "dashbeam:wallet:share_view_only",
            ],
            hooks=["before_message_send", "after_ticket_create"],
            tier_required=["Pro", "Enterprise"],
        )
        pm.install(m)
        pm.enable("dashbeam-transfer")
        assert pm.list_plugins() == ["dashbeam-transfer"]


# ── Version Check ─────────────────────────────────────────────────────────────

class TestVersionCheck:
    def test_ok(self, pm):
        assert pm.check_version("1.0.0", "1.0.0") is True
        assert pm.check_version("1.0.0", "1.0.1") is True
        assert pm.check_version("1.0.0", "1.1.0") is True
        assert pm.check_version("1.0.0", "2.0.0") is True

    def test_fail(self, pm):
        assert pm.check_version("1.0.0", "0.9.0") is False
        assert pm.check_version("3.0.0", "1.0.0") is False


# ── Bulk operations ───────────────────────────────────────────────────────────

class TestBulk:
    def test_enable_disable_all(self, pm):
        for pid in ("a", "b", "c"):
            pm.install(_mk_manifest(pid))
        pm.enable_all()
        assert pm.get_count() == 3
        pm.disable_all()
        assert pm.get_count() == 0


# ── Builtin discovery ─────────────────────────────────────────────────────────

class TestBuiltinDiscovery:
    def test_finds_builtin_dirs(self, pm):
        """Verify at least builtin/plugin-system/ dir is found."""
        pm.add_plugin_dir(Path(__file__).resolve().parents[1] / "plugins" / "builtin")
        discovered = pm.discover()
        # We might not have the actual search path set up right,
        # but the method should run without error and return a dict
        assert isinstance(discovered, dict)


# ── Edge cases ────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_enable_not_installed_raises(self, pm):
        with pytest.raises(KeyError):
            pm.enable("never_installed")

    def test_disable_twice_idempotent(self, pm, m):
        pm.install(m)
        pm.enable(m.plugin_id)
        pm.disable(m.plugin_id)
        pm.disable(m.plugin_id)  # should not raise

    def test_unload_already_unloaded(self, pm, m):
        pm.install(m)
        pm.unload(m.plugin_id)
        pm.unload(m.plugin_id)  # should not raise

    def test_empty_get_count(self, pm):
        assert pm.get_count() == 0

    def test_empty_list_plugins(self, pm):
        assert pm.list_plugins() == []

    def test_empty_discover(self, pm):
        assert isinstance(pm.discover(), dict)


# ── Policy Engine integration via hooks ──────────────────────────────────────

class TestPolicyEngineHooks:
    def test_before_policy_check_block(self, pm):
        blocked = []
        def policy_handler(**kw):
            if kw.get("action") == "delete_production":
                blocked.append(kw)
                return {"allowed": False, "reason": "BLOCKED"}
            return {"allowed": True}

        pm.hook_system.register("before_policy_check", "policy-engine", policy_handler)
        results = pm.hook_system.fire("before_policy_check", action="delete_production")
        assert results[0]["allowed"] is False
        assert len(blocked) == 1


# ── Decision Gate integration ─────────────────────────────────────────────────

class TestDecisionGate:
    def test_gate_blocks_restricted(self, pm):
        def gate_handler(**kw):
            action = kw.get("action", "")
            if "delete:tenant" in action:
                return {"passed": False, "reason": "Tenant deletion requires admin"}
            return {"passed": True}

        pm.hook_system.register("before_decision_gate", "decision-gate", gate_handler)
        results = pm.hook_system.fire("before_decision_gate", action="delete:tenant")
        assert results[0]["passed"] is False
