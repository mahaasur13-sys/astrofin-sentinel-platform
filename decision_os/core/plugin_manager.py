"""DecisionOS V2.0 — Plugin Architecture Core."""
from __future__ import annotations

import functools
import importlib
import json
import logging
import os
import sys
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger("decisionos.core")

ROOT = Path(__file__).resolve().parent.parent


# ────────────────────── Enums / Types ──────────────────────

class PluginState(Enum):
    REGISTERED = "registered"
    INSTALLED = "installed"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
    UNLOADED = "unloaded"


class TraceLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    DECISION = "decision"
    WARN = "warn"
    ERROR = "error"


# ────────────────────── Plugin Manifest ──────────────────────

@dataclass
class PluginManifest:
    plugin_id: str
    name: str
    version: str
    description: str
    author: str
    permissions: list[str]
    hooks: list[str]
    tier_required: list[str]
    entry_point: str
    sandbox: str = ""
    signatures: list[str] = field(default_factory=list)

    @classmethod
    def from_json(cls, path: Path | str) -> "PluginManifest":
        with open(path) as f:
            raw = json.load(f)
        return cls(
            plugin_id=raw["id"],
            name=raw.get("name", raw["id"]),
            version=raw.get("version", "0.0.0"),
            description=raw.get("description", ""),
            author=raw.get("author", "unknown"),
            permissions=raw.get("permissions", []),
            hooks=raw.get("hooks", []),
            tier_required=raw.get("tier_required", ["Start"]),
            entry_point=raw.get("entry_point", "main.py"),
        )


# ────────────────────── Plugin Instance ──────────────────────

@dataclass
class PluginInstance:
    manifest: PluginManifest
    state: PluginState = PluginState.REGISTERED
    mod: Any = None
    obj: Any = None
    sandbox_id: str = ""
    installed_at: str = ""
    enabled_at: str = ""

    @property
    def status(self) -> str:
        return self.state.value


# ────────────────────── Thought Tracer ──────────────────────

@dataclass
class ThoughtEntry:
    timestamp: str
    level: TraceLevel
    plugin_id: str
    agent: str
    message: str
    metadata: dict = field(default_factory=dict)


class ThoughtTracer:
    def __init__(self, max_entries: int = 10_000):
        self._lock = threading.Lock()
        self._entries: list[ThoughtEntry] = []
        self._max = max_entries
        self._jsonl_path: Path | None = None

    def set_jsonl_path(self, path: Path):
        self._jsonl_path = path

    def trace(self, level: TraceLevel, plugin_id: str, agent: str, message: str, **meta):
        entry = ThoughtEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level,
            plugin_id=plugin_id,
            agent=agent,
            message=message,
            metadata=meta,
        )
        with self._lock:
            self._entries.append(entry)
            if len(self._entries) > self._max:
                self._entries = self._entries[-self._max:]
            if self._jsonl_path:
                with open(self._jsonl_path, "a") as f:
                    f.write(json.dumps({
                        "ts": entry.timestamp, "level": entry.level.value,
                        "plugin": entry.plugin_id, "agent": entry.agent,
                        "msg": entry.message, "meta": entry.metadata,
                    }) + "\n")

    def last_entries(self, n: int = 50) -> list[ThoughtEntry]:
        with self._lock:
            return list(self._entries[-n:])

    def entries_since(self, iso_ts: str) -> list[ThoughtEntry]:
        with self._lock:
            return [e for e in self._entries if e.timestamp > iso_ts]


# ────────────────────── Hook System ──────────────────────

class HookSystem:
    def __init__(self):
        self._hooks: dict[str, list[tuple[str, Callable]]] = {}

    def register(self, event: str, plugin_id: str, handler: Callable):
        self._hooks.setdefault(event, []).append((plugin_id, handler))

    def unregister_plugin(self, plugin_id: str):
        for event in self._hooks:
            self._hooks[event] = [
                (pid, h) for pid, h in self._hooks[event] if pid != plugin_id
            ]

    def fire(self, event: str, **ctx) -> list[dict]:
        results = []
        for _pid, handler in self._hooks.get(event, []):
            try:
                result = handler(**ctx)
                if result is not None:
                    results.append(result)
            except Exception:
                logger.exception("hook %s in %s failed", event, _pid)
        return results

    def list_events(self) -> list[str]:
        return list(self._hooks.keys())

    def handlers_for(self, event: str) -> list[str]:
        return [pid for pid, _ in self._hooks.get(event, [])]


# ────────────────────── Sandbox ──────────────────────

class Sandbox:
    def __init__(self, base_path: Path):
        self._base = base_path

    def isolate(self, manifest: PluginManifest) -> str:
        sandbox_id = f"sandbox_{manifest.plugin_id}_{manifest.version.replace('.', '_')}"
        return sandbox_id

    def validate(self, manifest: PluginManifest) -> bool:
        if not manifest.plugin_id:
            return False
        if not manifest.entry_point:
            return False
        return True

    def allowed_permissions(self, manifest: PluginManifest, tenant_tier: str) -> list[str]:
        tier_weights = {"Start": 0, "Pro": 1, "Enterprise": 2}
        permitted = set()
        for perm in manifest.permissions:
            if "spend" in perm.lower():
                logger.critical("SPEND_KEY permission denied for %s", manifest.plugin_id)
                continue
            if "dashbeam" in perm.lower():
                if tenant_tier in ("Pro", "Enterprise"):
                    permitted.add(perm)
            elif tier_weights.get(tenant_tier, 0) >= 0:
                permitted.add(perm)
        return list(permitted)


# ────────────────────── Plugin Registry ──────────────────────

@dataclass
class PluginEntry:
    manifest: PluginManifest
    state: PluginState
    sandbox_id: str

    @property
    def status(self) -> str:
        return self.state.value


class PluginRegistry:
    def __init__(self):
        self._plugins: dict[str, PluginEntry] = {}

    def register(self, instance: PluginInstance):
        self._plugins[instance.manifest.plugin_id] = PluginEntry(
            manifest=instance.manifest,
            state=instance.state,
            sandbox_id=instance.sandbox_id,
        )

    def update_state(self, plugin_id: str, state: PluginState):
        if plugin_id in self._plugins:
            self._plugins[plugin_id].state = state
            self._plugins[plugin_id].manifest = self._plugins[plugin_id].manifest

    def get(self, plugin_id: str) -> PluginEntry | None:
        return self._plugins.get(plugin_id)

    def list_all(self) -> dict[str, PluginEntry]:
        return dict(self._plugins)

    def remove(self, plugin_id: str):
        self._plugins.pop(plugin_id, None)

    def find_by_state(self, state: PluginState) -> list[PluginEntry]:
        return [p for p in self._plugins.values() if p.state == state]


# ────────────────────── Plugin Manager ──────────────────────

class PluginManager:
    def __init__(self, tenant_tier: str = "Start"):
        self.tenant_tier = tenant_tier
        self.hook_system = HookSystem()
        self.registry = PluginRegistry()
        self.sandbox = Sandbox(ROOT / "sandbox")
        self.thought_tracer = ThoughtTracer()

        self._builtin_dir = ROOT / "plugins/builtin"
        self._community_dir = ROOT / "plugins/community"
        self._external_dirs: list[Path] = []

    def add_plugin_dir(self, path: Path):
        self._external_dirs.append(path)

    def discover(self) -> dict[str, PluginManifest]:
        manifests: dict[str, PluginManifest] = {}
        for d in self._scan_dirs():
            mf_path = d / "manifest.json"
            if mf_path.exists():
                mf = PluginManifest.from_json(mf_path)
                manifests[mf.plugin_id] = mf
        return manifests

    def _scan_dirs(self) -> list[Path]:
        dirs = []
        for base in [self._builtin_dir, self._community_dir] + self._external_dirs:
            if base.exists():
                for item in base.iterdir():
                    if item.is_dir() and (item / "manifest.json").exists():
                        dirs.append(item)
        return dirs

    def install(self, manifest: PluginManifest) -> PluginInstance:
        if manifest.plugin_id in self.registry._plugins:
            raise RuntimeError(f"Plugin '{manifest.plugin_id}' already installed — uninstall first")

        instance = PluginInstance(
            manifest=manifest,
            state=PluginState.INSTALLED,
            installed_at=datetime.now(timezone.utc).isoformat(),
        )
        self.registry.register(instance)

        self.thought_tracer.trace(
            TraceLevel.INFO, manifest.plugin_id, "plugin_manager",
            f"Plugin {manifest.plugin_id} v{manifest.version} installed",
        )
        return instance

    def load(self, plugin_id: str) -> PluginInstance:
        instance = self._get_instance(plugin_id)
        manifest = instance.manifest

        plugin_dir = self._find_plugin_dir(plugin_id)
        if plugin_dir is None:
            raise FileNotFoundError(f"Plugin dir not found: {plugin_id}")

        entry_stem = Path(manifest.entry_point).stem
        sys.path.insert(0, str(plugin_dir))
        try:
            mod = importlib.import_module(entry_stem)
            plugin_cls = getattr(mod, "Plugin", None)
            if plugin_cls is None:
                raise ImportError(f"No 'Plugin' class in {entry_stem}")
        finally:
            sys.path.pop(0)

        instance.obj = plugin_cls()
        instance.mod = mod
        instance.state = PluginState.LOADED
        self.registry.update_state(plugin_id, PluginState.LOADED)

        self.thought_tracer.trace(
            TraceLevel.INFO, plugin_id, "plugin_manager",
            f"Plugin {plugin_id} loaded (class={plugin_cls.__name__})",
        )
        return instance

    def enable(self, plugin_id: str) -> PluginInstance:
        instance = self._get_instance(plugin_id)

        allowed = self.sandbox.allowed_permissions(instance.manifest, self.tenant_tier)
        if len(allowed) == 0 and instance.manifest.permissions:
            raise PermissionError(f"Plugin '{plugin_id}' has no allowed permissions for tier '{self.tenant_tier}'")

        for hook_event in instance.manifest.hooks:
            handler = getattr(instance.obj, f"_hook_{hook_event}", None)
            if handler:
                self.hook_system.register(hook_event, plugin_id, handler)

        if hasattr(instance.obj, "on_enable"):
            instance.obj.on_enable()

        instance.state = PluginState.ENABLED
        instance.enabled_at = datetime.now(timezone.utc).isoformat()
        self.registry.update_state(plugin_id, PluginState.ENABLED)

        self.thought_tracer.trace(
            TraceLevel.DECISION, plugin_id, "plugin_manager",
            f"Plugin {plugin_id} ENABLED (tier={self.tenant_tier})",
        )
        return instance

    def disable(self, plugin_id: str) -> PluginInstance:
        instance = self._get_instance(plugin_id)
        self.thought_tracer.trace(TraceLevel.INFO, plugin_id, "plugin_manager", f"Plugin {plugin_id} disabled")
        instance.state = PluginState.DISABLED
        self.registry.update_state(plugin_id, PluginState.DISABLED)
        self.hook_system.unregister_plugin(plugin_id)
        return instance

    def unload(self, plugin_id: str) -> PluginInstance:
        instance = self._get_instance(plugin_id)
        instance.obj = None
        instance.mod = None
        instance.state = PluginState.UNLOADED
        self.registry.update_state(plugin_id, PluginState.UNLOADED)
        return instance

    def update(self, plugin_id: str, new_manifest: PluginManifest) -> PluginInstance:
        entry = self.registry.get(plugin_id)
        if entry is None:
            raise ValueError(f"Plugin '{plugin_id}' not found")
        entry.manifest = new_manifest
        entry.manifest.version = new_manifest.version
        self.disable(plugin_id)
        return self.enable(plugin_id)

    def hot_reload(self, plugin_id: str) -> PluginInstance:
        self.disable(plugin_id)
        self.unload(plugin_id)
        return self.load(plugin_id)
    
    def _get_instance(self, plugin_id: str) -> PluginInstance:
        entry = self.registry.get(plugin_id)
        if entry is None:
            raise KeyError(f"Plugin '{plugin_id}' not found in registry")
        return PluginInstance(
            manifest=entry.manifest,
            state=entry.state,
            sandbox_id=entry.sandbox_id,
        )

    def _find_plugin_dir(self, plugin_id: str) -> Path | None:
        for base in [self._builtin_dir, self._community_dir] + self._external_dirs:
            candidate = base / plugin_id
            if candidate.exists() and (candidate / "manifest.json").exists():
                return candidate
        return None

    def list_all(self) -> list[dict]:
        return [
            {
                "plugin_id": pid,
                "name": e.manifest.name,
                "version": e.manifest.version,
                "status": e.state.value,
                "tier_required": e.manifest.tier_required,
            }
            for pid, e in self.registry.list_all().items()
        ]

    @property
    def hooks(self):
        """Alias for hook_system (test compatibility)."""
        return self.hook_system

    def list_plugins(self) -> list:
        """Return list of enabled plugin ids."""
        return [eid for eid, entry in self.registry._plugins.items() if entry.state == PluginState.ENABLED]

    def get_count(self) -> int:
        """Return count of enabled plugins."""
        return len(self.list_plugins())

    def check_version(self, required: str, installed: str) -> bool:
        """Check if installed version satisfies required semver."""
        from packaging.version import Version
        return Version(installed) >= Version(required)

    def enable_all(self):
        """Enable all installed plugins."""
        for plugin_id in list(self.registry._plugins.keys()):
            self.enable(plugin_id)

    def disable_all(self):
        """Disable all enabled plugins."""
        for plugin_id in list(self.registry._plugins.keys()):
            if self.registry._plugins[plugin_id].state == PluginState.ENABLED:
                self.disable(plugin_id)

