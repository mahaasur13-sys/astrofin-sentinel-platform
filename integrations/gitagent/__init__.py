"""GitAgent integration package.

Provides agent export/import, MCP (Model Context Protocol) adapter,
and LangGraph/n8n orchestration primitives for AstroFinSentinelV5.
"""

from __future__ import annotations

from .adapters.mcp_adapter import MCPAdapter

__all__ = ["MCPAdapter", "adapters"]
