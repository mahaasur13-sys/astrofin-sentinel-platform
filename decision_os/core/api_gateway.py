"""API Gateway — FastAPI-based unified entry point for DecisionOS."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .plugin_manager import PluginManager
from .security import AuthService, Tenant
from .thought_tracer import ThoughtTracer


def create_app(
    plugin_manager: PluginManager,
    auth_service: AuthService,
    thought_tracer: ThoughtTracer | None = None,
) -> FastAPI:
    """Create the DecisionOS FastAPI application."""

    app = FastAPI(
        title="DecisionOS v2.0",
        description="Enterprise decision-making platform — everything is a plugin.",
        version="2.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.plugin_manager = plugin_manager
    app.state.auth_service = auth_service
    app.state.thought_tracer = thought_tracer

    # ── Dependencies ──

    async def get_tenant(request: Request) -> Tenant:
        api_key = request.headers.get("X-API-Key", "")
        if not api_key:
            raise HTTPException(status_code=401, detail="X-API-Key header required")

        tenant = auth_service.validate_api_key(api_key)
        if not tenant:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return tenant

    # ── Plugin endpoints ──

    @app.get("/api/v2/plugins")
    async def list_plugins(tenant: Tenant = Depends(get_tenant)):
        """List all installed plugins with status."""
        plugins = plugin_manager.list_plugins()
        return {"plugins": plugins, "tenant_tier": tenant.tier}

    @app.post("/api/v2/plugins/{plugin_id}/enable")
    async def enable_plugin(plugin_id: str, tenant: Tenant = Depends(get_tenant)):
        """Enable a plugin."""
        manifest = plugin_manager.get_manifest(plugin_id)
        if not manifest:
            raise HTTPException(status_code=404, detail="Plugin not found")

        if not tenant.can_use_plugin(manifest.get("tier_required", ["Start"])):
            raise HTTPException(status_code=403, detail="Your tier does not support this plugin")

        plugin_manager.enable(plugin_id)
        return {"status": "enabled", "plugin_id": plugin_id}

    @app.post("/api/v2/plugins/{plugin_id}/disable")
    async def disable_plugin(plugin_id: str, tenant: Tenant = Depends(get_tenant)):
        """Disable a plugin."""
        plugin_manager.disable(plugin_id)
        return {"status": "disabled", "plugin_id": plugin_id}

    @app.post("/api/v2/plugins/{plugin_id}/reload")
    async def reload_plugin(plugin_id: str, tenant: Tenant = Depends(get_tenant)):
        """Hot-reload a plugin (Enterprise only)."""
        if tenant.tier != "Enterprise":
            raise HTTPException(status_code=403, detail="Hot-reload requires Enterprise tier")

        try:
            plugin_manager.reload(plugin_id)
            return {"status": "reloaded", "plugin_id": plugin_id}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    # ── DashBeam endpoints ──

    @app.post("/api/v2/dashbeam/ticket")
    async def create_dashbeam_ticket(ticket_data: DashBeamTicketRequest, tenant: Tenant = Depends(get_tenant)):
        """Create a DashBeam transfer ticket."""
        if not tenant.can_use_plugin(["Pro", "Enterprise"]):
            raise HTTPException(status_code=403, detail="DashBeam requires Pro or Enterprise tier")

        dashbeam = plugin_manager.get("dashbeam-transfer")
        if not dashbeam:
            raise HTTPException(status_code=404, detail="DashBeam plugin not active")

        if thought_tracer:
            thought_tracer.start_trace(ticket_data.trace_id, tenant.tenant_id)
            thought_tracer.add_step(
                ticket_data.trace_id, "dashbeam-transfer", "create_ticket",
                "Creating P2P transfer ticket",
                inputs={"file_name": ticket_data.file_name},
            )

        ticket = dashbeam.create_ticket(
            tenant_id=tenant.tenant_id,
            file_name=ticket_data.file_name,
            file_size=ticket_data.file_size,
        )

        if thought_tracer:
            thought_tracer.complete_trace(ticket_data.trace_id, {"ticket_created": True})

        return {"ticket": ticket}

    @app.post("/api/v2/dashbeam/transfer")
    async def initiate_transfer(transfer_data: DashBeamTransferRequest, tenant: Tenant = Depends(get_tenant)):
        """Initiate a P2P file transfer."""
        if not tenant.can_use_plugin(["Pro", "Enterprise"]):
            raise HTTPException(status_code=403, detail="DashBeam requires Pro or Enterprise tier")

        dashbeam = plugin_manager.get("dashbeam-transfer")
        if not dashbeam:
            raise HTTPException(status_code=404, detail="DashBeam plugin not active")

        session = dashbeam.initiate_transfer(
            ticket_code=transfer_data.ticket_code,
            file_path=transfer_data.file_path,
            tenant_id=tenant.tenant_id,
        )

        return {"session": session}

    @app.get("/api/v2/dashbeam/session/{session_id}")
    async def get_session_status(session_id: str, tenant: Tenant = Depends(get_tenant)):
        """Get DashBeam session status."""
        dashbeam = plugin_manager.get("dashbeam-transfer")
        if not dashbeam:
            raise HTTPException(status_code=404, detail="DashBeam plugin not active")

        session = dashbeam.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"session": session}

    # ── Wallet endpoint ──

    @app.get("/api/v2/wallets/{wallet_id}/view-only")
    async def get_view_only_wallet(wallet_id: str, tenant: Tenant = Depends(get_tenant)):
        """Share view-only wallet data via DashBeam."""
        wallets_plugin = plugin_manager.get("crypto-wallets")
        if not wallets_plugin:
            raise HTTPException(status_code=404, detail="Crypto Wallets plugin not active")

        view_data = wallets_plugin.get_view_only_data(wallet_id, tenant.tenant_id)
        return {"wallet": view_data}

    # ── Stats ──

    @app.get("/api/v2/stats")
    async def get_stats():
        """Get global system stats."""
        return {
            "plugins": plugin_manager.get_stats(),
        }

    # ── Health ──

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": "2.0.0"}

    return app


class DashBeamTicketRequest(BaseModel):
    file_name: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., gt=0, le=100 * 1024 * 1024)
    trace_id: str = Field(default="trace_default")


class DashBeamTransferRequest(BaseModel):
    ticket_code: str = Field(..., min_length=6, max_length=64)
    file_path: str = Field(default="")
