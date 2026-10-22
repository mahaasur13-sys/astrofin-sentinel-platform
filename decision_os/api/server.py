"""
DecisionOS API — FastAPI application.

Minimal core: only plugin management endpoints.
Every other endpoint comes from plugins.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from decision_os.core import PluginManager


def create_app(
    plugin_manager: PluginManager,
    tenant_id: str = "default",
    tier: str = "Start",
) -> FastAPI:
    app = FastAPI(
        title="DecisionOS API",
        version="1.0.0",
        description="Enterprise decision platform — plugin architecture",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "version": "1.0.0",
            "tenant_id": tenant_id,
            "tier": tier,
        }

    @app.get("/api/plugins")
    async def list_plugins():
        return {"plugins": plugin_manager.list_all()}

    @app.get("/api/plugins/{plugin_id}")
    async def get_plugin(plugin_id: str):
        instance = plugin_manager.get(plugin_id)
        if not instance:
            return {"error": "PLUGIN_NOT_FOUND", "plugin_id": plugin_id}
        return {
            "plugin_id": plugin_id,
            "name": instance.manifest.name,
            "status": instance.status,
            "version": instance.manifest.version,
        }

    @app.post("/api/plugins/{plugin_id}/enable")
    async def enable_plugin(plugin_id: str):
        try:
            instance = plugin_manager.enable(plugin_id)
            return {"plugin_id": plugin_id, "status": instance.status}
        except Exception as e:
            return {"error": str(e), "plugin_id": plugin_id}

    @app.post("/api/plugins/{plugin_id}/disable")
    async def disable_plugin(plugin_id: str):
        try:
            instance = plugin_manager.disable(plugin_id)
            return {"plugin_id": plugin_id, "status": instance.status}
        except Exception as e:
            return {"error": str(e), "plugin_id": plugin_id}

    @app.get("/api/hooks")
    async def list_hooks():
        return {"hooks": plugin_manager.hook_system.list_hooks()}

    @app.get("/api/trace")
    async def get_trace():
        entries = plugin_manager.thought_tracer.entries()
        return {"entries": [e.to_dict() for e in entries], "count": len(entries)}

    return app
