"""DecisionOS API — FastAPI integration."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from decision_os.core import PluginManager
from decision_os.core.plugin_manager import PluginManifest

logger = logging.getLogger("decisionos.api")

ROOT = Path(__file__).resolve().parent.parent

app = FastAPI(title="DecisionOS v2.0", version="2.0.0")
manager = PluginManager(tenant_tier="Start")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_app(tier: str = "Start") -> FastAPI:
    global manager
    manager = PluginManager(tenant_tier=tier)
    return app


@asyncio.coroutine
def bootstrap():
    """Install and enable built-in plugins."""
    manifests = manager.discover()
    for mid, mf in manifests.items():
        try:
            manager.install(mf)
            manager.load(mid)
            manager.enable(mid)
            logger.info("bootstrapped %s v%s", mid, mf.version)
        except Exception:
            logger.exception("failed to bootstrap %s", mid)


@app.get("/")
def root():
    return {"service": "DecisionOS v2.0", "status": "running"}


@app.get("/health")
def health():
    return {"status": "healthy", "tier": manager.tenant_tier}


@app.get("/plugins")
def list_plugins():
    return {"plugins": manager.list_all()}


@app.get("/plugins/{plugin_id}")
def get_plugin(plugin_id: str):
    entry = manager.registry.get(plugin_id)
    if entry is None:
        return {"error": "plugin not found"}, 404
    return {
        "id": plugin_id,
        "name": entry.manifest.name,
        "version": entry.manifest.version,
        "state": entry.state.value,
        "permissions": entry.manifest.permissions,
        "hooks": entry.manifest.hooks,
    }


@app.post("/plugins/install")
def install_plugin(body: dict):
    mf = PluginManifest(
        plugin_id=body["id"],
        name=body.get("name", body["id"]),
        version=body.get("version", "0.0.0"),
        description=body.get("description", ""),
        author=body.get("author", "unknown"),
        permissions=body.get("permissions", []),
        hooks=body.get("hooks", []),
        tier_required=body.get("tier_required", ["Start"]),
        entry_point=body.get("entry_point", "main.py"),
    )
    try:
        instance = manager.install(mf)
        manager.load(mf.plugin_id)
        manager.enable(mf.plugin_id)
        return {"status": "installed", "plugin_id": instance.manifest.plugin_id}
    except Exception:
        logger.exception("install failed")
        return {"error": "install failed"}, 500


@app.post("/plugins/{plugin_id}/disable")
def disable_plugin(plugin_id: str):
    try:
        manager.disable(plugin_id)
        return {"status": "disabled", "plugin_id": plugin_id}
    except KeyError:
        return {"error": "not found"}, 404


@app.post("/plugins/{plugin_id}/enable")
def enable_plugin(plugin_id: str):
    try:
        manager.enable(plugin_id)
        return {"status": "enabled", "plugin_id": plugin_id}
    except KeyError:
        return {"error": "not found"}, 404


@app.get("/hooks")
def list_hooks():
    events = manager.hook_system.list_events()
    return {"events": events}


@app.post("/hooks/{event}/fire")
def fire_hook(event: str, body: dict):
    results = manager.hook_system.fire(event, **body)
    return {"event": event, "results": results}


@app.get("/thought-trace")
def get_thought_trace(n: int = 50):
    entries = manager.thought_tracer.last_entries(n)
    return {
        "traces": [
            {"ts": e.timestamp, "level": e.level.value, "plugin": e.plugin_id,
             "agent": e.agent, "msg": e.message, "meta": e.metadata}
            for e in entries
        ]
    }
