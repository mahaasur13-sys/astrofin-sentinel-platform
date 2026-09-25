"""Core type system for DecisionOS — Pydantic v2, fully typed."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Plugin States ──────────────────────────────────────────────

class PluginState(str, enum.Enum):
    INSTALLED = "installed"
    VALIDATED = "validated"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNLOADED = "unloaded"
    ERROR = "error"
    UPDATING = "updating"


class PluginSource(str, enum.Enum):
    FILESYSTEM = "filesystem"
    NPM_PACKAGE = "npm_package"
    MARKETPLACE = "marketplace"
    CUSTOM = "custom"


# ── Tier ───────────────────────────────────────────────────────

class TenantTier(str, enum.Enum):
    START = "Start"
    PRO = "Pro"
    ENTERPRISE = "Enterprise"


# ── Plugin Manifest ────────────────────────────────────────────

class PluginManifest(BaseModel):
    id: str = Field(..., pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
    name: str = Field(..., min_length=1, max_length=128)
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    description: str = Field(default="", max_length=1024)
    author: str = Field(default="DecisionOS Team")
    permissions: list[str] = Field(default_factory=list)
    hooks: list[str] = Field(default_factory=list)
    tier_required: list[TenantTier] = Field(default_factory=lambda: [TenantTier.START])
    dependencies: list[str] = Field(default_factory=list)
    entry_point: str = Field(default="main.py")
    source: PluginSource = Field(default=PluginSource.FILESYSTEM)
    signature: str | None = Field(default=None)
    min_core_version: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Plugin Instance ────────────────────────────────────────────

class PluginInstance(BaseModel):
    manifest: PluginManifest
    state: PluginState = Field(default=PluginState.INSTALLED)
    loaded_at: datetime | None = Field(default=None)
    error_message: str | None = Field(default=None)
    tenant_id: str | None = Field(default=None)
    sandbox_id: str | None = Field(default=None)
    metrics: dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


# ── Hook ───────────────────────────────────────────────────────

class HookContext(BaseModel):
    hook_name: str
    tenant_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: dict[str, Any] = Field(default_factory=dict)
    trace_id: str | None = None

    class Config:
        arbitrary_types_allowed = True


class HookResult(BaseModel):
    allowed: bool = True
    modified_payload: dict[str, Any] | None = None
    message: str | None = None


# ── Thought Trace ──────────────────────────────────────────────

class ThoughtStep(BaseModel):
    step_id: str
    agent_id: str
    action: str
    reasoning: str
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: float | None = None
    policy_decision: str | None = None

    class Config:
        arbitrary_types_allowed = True


class ThoughtTrace(BaseModel):
    trace_id: str
    session_id: str
    tenant_id: str
    steps: list[ThoughtStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    final_decision: str | None = None

    class Config:
        arbitrary_types_allowed = True


# ── Permission ─────────────────────────────────────────────────

class Permission(BaseModel):
    domain: str  # e.g. "dashbeam", "crypto", "support"
    action: str  # e.g. "ticket:create", "file:send"
    description: str = ""


# ── Audit Event ────────────────────────────────────────────────

class AuditEvent(BaseModel):
    event_id: str
    tenant_id: str
    plugin_id: str
    action: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: dict[str, Any] = Field(default_factory=dict)
    gate_decision: str | None = None

    class Config:
        arbitrary_types_allowed = True


# ── Policy Action ──────────────────────────────────────────────

class PolicyAction(str, enum.Enum):
    # DashBeam
    DASHBEAM_TICKET_CREATE = "dashbeam:ticket:create"
    DASHBEAM_FILE_SEND = "dashbeam:file:send"
    DASHBEAM_RELAY_CONFIGURE = "dashbeam:relay:configure"
    DASHBEAM_WALLET_SHARE_VIEW = "dashbeam:wallet:share_view_only"
    # Crypto
    CRYPTO_PAYMENT_CREATE = "crypto:payment:create"
    CRYPTO_WALLET_GENERATE = "crypto:wallet:generate"
    CRYPTO_WALLET_VIEW_ONLY = "crypto:wallet:view_only"
    # Support
    SUPPORT_TICKET_CREATE = "support:ticket:create"
    SUPPORT_MESSAGE_SEND = "support:message:send"
    # Decision
    DECISION_GATE_PASS = "decision:gate:pass"
    # System
    PLUGIN_INSTALL = "system:plugin:install"
    PLUGIN_ENABLE = "system:plugin:enable"
    PLUGIN_UNLOAD = "system:plugin:unload"


# ── Error Codes ────────────────────────────────────────────────

class ErrorCode(str, enum.Enum):
    PLUGIN_NOT_FOUND = "ERR_PLUGIN_NOT_FOUND"
    PLUGIN_ALREADY_LOADED = "ERR_PLUGIN_ALREADY_LOADED"
    PLUGIN_VALIDATION_FAILED = "ERR_PLUGIN_VALIDATION_FAILED"
    PLUGIN_SIGNATURE_INVALID = "ERR_PLUGIN_SIGNATURE_INVALID"
    PLUGIN_TIER_DENIED = "ERR_PLUGIN_TIER_DENIED"
    PLUGIN_PERMISSION_DENIED = "ERR_PLUGIN_PERMISSION_DENIED"
    PLUGIN_SANDBOX_VIOLATION = "ERR_PLUGIN_SANDBOX_VIOLATION"
    PLUGIN_HOOK_FAILED = "ERR_PLUGIN_HOOK_FAILED"
    PLUGIN_DEPENDENCY_MISSING = "ERR_PLUGIN_DEPENDENCY_MISSING"
    GATE_DENIED = "ERR_GATE_DENIED"
    SPEND_KEY_EXPOSURE = "ERR_SPEND_KEY_EXPOSURE"
    TENANT_ISOLATION_VIOLATION = "ERR_TENANT_ISOLATION_VIOLATION"
