"""Smithery MCP registry and connection adapter for GitAgent."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import httpx


class MCPAdapter:
    """Discover Smithery servers and expose their MCP tools to GitAgent.

    The adapter intentionally manages Smithery connections rather than copying
    arbitrary server packages into the application. This keeps credentials and
    server runtimes outside the AstroFin process.
    """

    api_base = "https://api.smithery.ai"
    registry_path = "/servers"

    def __init__(
        self,
        storage_path: str | Path | None = None,
        *,
        api_key: str | None = None,
        cli: str = "smithery",
    ) -> None:
        self.storage_path = Path(storage_path or Path.home() / ".gitagent" / "mcp")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.api_key = api_key or os.getenv("SMITHERY_API_KEY")
        self.cli = cli
        self.installed_servers: dict[str, dict[str, Any]] = {}
        self._load_installed()

    @property
    def _state_file(self) -> Path:
        return self.storage_path / "installed_servers.json"

    def _load_installed(self) -> None:
        if not self._state_file.exists():
            return
        try:
            payload = json.loads(self._state_file.read_text())
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(payload, dict):
            self.installed_servers = payload

    def _save_installed(self) -> None:
        self._state_file.write_text(json.dumps(self.installed_servers, indent=2, sort_keys=True))

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    def _api_search(self, query: str, page_size: int) -> list[dict[str, Any]]:
        params = {
            "q": query,
            "page": 1,
            "pageSize": min(max(page_size, 1), 100),
            "topK": max(10, min(page_size * 2, 500)),
        }
        with httpx.Client(timeout=15.0) as client:
            response = client.get(
                f"{self.api_base}{self.registry_path}", params=params, headers=self._headers()
            )
            response.raise_for_status()
            return self._extract_servers(response.json())

    @staticmethod
    def _extract_servers(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if not isinstance(payload, dict):
            return []
        for key in ("servers", "results", "data", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [payload] if payload.get("name") or payload.get("qualifiedName") else []

    @staticmethod
    def _server_name(server: dict[str, Any]) -> str:
        return str(
            server.get("name") or server.get("qualifiedName") or server.get("qualified_name") or ""
        )

    @staticmethod
    def _normalize_servers(servers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        seen: set[str] = set()
        for server in servers:
            name = MCPAdapter._server_name(server)
            if not name or name in seen:
                continue
            seen.add(name)
            item = dict(server)
            item["name"] = name
            normalized.append(item)
        return normalized

    def _run_cli(self, args: list[str], timeout: int | None = None) -> dict[str, Any]:
        command_args = [arg for arg in args if arg != "--json"]
        command = [self.cli, "--json", *command_args]
        try:
            completed = subprocess.run(
                command, capture_output=True, text=True, timeout=timeout or 60, check=False
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"ok": False, "error": str(exc)}
        if completed.returncode != 0:
            return {"ok": False, "error": completed.stderr.strip() or completed.stdout.strip()}
        output = completed.stdout.strip()
        try:
            payload: Any = json.loads(output) if output else {}
        except json.JSONDecodeError:
            payload = {"output": output}
        return {"ok": True, "payload": payload}

    def _fallback_servers(self, query: str) -> list[dict[str, Any]]:
        catalog = [
            {
                "name": "parichay-pothepalli/financial-research-mcp",
                "capability": "market-data",
                "description": "Financial statements, prices, crypto data, news, and SEC filings.",
            },
            {
                "name": "financialdata-net/financialdata-mcp",
                "capability": "market-data",
                "description": "Stocks, ETFs, indices, forex, crypto, commodities, derivatives, and event calendars.",
            },
            {
                "name": "coinmarketcap/coinmarketcap-mcp",
                "capability": "crypto-market-data",
                "description": "Cryptocurrency prices, market statistics, and asset metadata.",
            },
            {
                "name": "openclaw/finnhub",
                "capability": "financial-news",
                "description": "Quotes, company news, financial statements, earnings, and market calendars.",
            },
            {
                "name": "google-calendar/google-calendar-mcp",
                "capability": "economic-calendar",
                "description": "Calendar integration for scheduled research and event reminders.",
            },
            {
                "name": "github/github-mcp-server",
                "capability": "github-operations",
                "description": "Repositories, issues, pull requests, and code operations.",
            },
        ]
        terms = set(re.findall(r"[a-z0-9]+", query.lower()))
        if not terms:
            return catalog
        return [
            item
            for item in catalog
            if terms
            & set(
                re.findall(
                    r"[a-z0-9]+",
                    f"{item['name']} {item['capability']} {item['description']}".lower(),
                )
            )
        ]

    def mcp_search(
        self, query: str, category: str | None = None, *, page_size: int = 20
    ) -> list[dict[str, Any]]:
        """Search Smithery's registry, falling back to CLI and known capability hints."""
        results: list[dict[str, Any]] = []
        try:
            results = self._api_search(query, page_size)
        except (httpx.HTTPError, OSError, ValueError):
            cli = self._run_cli(["--json", "mcp", "search", query], timeout=45)
            if cli["ok"]:
                results = self._extract_servers(cli["payload"])
        results = self._normalize_servers(results)
        if not results:
            results = self._fallback_servers(query)
        results = self._normalize_servers(results)
        if category:
            category_lower = category.lower()
            results = [item for item in results if category_lower in json.dumps(item).lower()]
        return results[:page_size]

    @staticmethod
    def _connection_id(server_name: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_-]+", "-", server_name).strip("-").lower()

    def mcp_install(self, server_name: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
        """Create a Smithery MCP connection and persist its non-secret metadata."""
        if not server_name:
            return {"status": "failed", "error": "server_name is required"}
        connection_id = self._connection_id(server_name)
        args = ["mcp", "add", server_name, "--id", connection_id, "--json"]
        if config:
            args.extend(["--config", json.dumps(config, separators=(",", ":"))])
        result = self._run_cli(args, timeout=120)
        if not result["ok"]:
            return {
                "status": "failed",
                "name": server_name,
                "connection_id": connection_id,
                "error": result.get("error", "Smithery CLI failed"),
            }
        metadata = result.get("payload") if isinstance(result.get("payload"), dict) else {}
        self.installed_servers[connection_id] = {
            "name": server_name,
            "connection_id": connection_id,
            "metadata": metadata,
        }
        self._save_installed()
        return {
            "status": "installed",
            "name": server_name,
            "connection_id": connection_id,
            "metadata": metadata,
        }

    def mcp_list_tools(self) -> list[dict[str, Any]]:
        """List and wrap tools from every persisted Smithery connection."""
        tools: list[dict[str, Any]] = []
        for connection_id, server in self.installed_servers.items():
            result = self._run_cli(["--json", "tool", "list", connection_id], timeout=60)
            if not result["ok"]:
                continue
            payload = result.get("payload")
            raw_tools = payload.get("tools", []) if isinstance(payload, dict) else payload
            if not isinstance(raw_tools, list):
                continue
            for tool in raw_tools:
                if isinstance(tool, dict):
                    tools.append(self.wrap_tool(tool, server["name"], connection_id))
        return tools

    def wrap_tool(
        self, tool_def: dict[str, Any], server: str | None = None, connection_id: str | None = None
    ) -> dict[str, Any]:
        """Convert an MCP tool schema into the stable GitAgent tool shape."""
        return {
            "name": str(tool_def.get("name", "unnamed_tool")),
            "description": str(tool_def.get("description", "")),
            "input_schema": tool_def.get("inputSchema", tool_def.get("input_schema", {})),
            "server": server or tool_def.get("_server", "unknown"),
            "connection_id": connection_id or tool_def.get("_connection_id"),
            "protocol": "mcp",
            "original_def": tool_def,
        }

    def call_tool(
        self, connection_id: str, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Call a connected MCP tool through Smithery CLI."""
        result = self._run_cli(
            ["tool", "call", connection_id, tool_name, json.dumps(arguments or {}), "--json"],
            timeout=120,
        )
        if result["ok"]:
            return {
                "status": "ok",
                "connection_id": connection_id,
                "tool": tool_name,
                "result": result.get("payload"),
            }
        return {
            "status": "failed",
            "connection_id": connection_id,
            "tool": tool_name,
            "error": result.get("error", "Smithery CLI failed"),
        }

    def mcp_uninstall(self, connection_id: str) -> dict[str, str]:
        """Remove a Smithery connection and its local metadata."""
        if connection_id not in self.installed_servers:
            return {"status": "error", "message": f"Connection {connection_id} not found"}
        result = self._run_cli(["mcp", "remove", connection_id, "--json"], timeout=60)
        if not result["ok"]:
            return {"status": "failed", "message": result.get("error", "Smithery CLI failed")}
        self.installed_servers.pop(connection_id)
        self._save_installed()
        return {"status": "success", "message": f"Uninstalled {connection_id}"}

    @classmethod
    def get_recommended_servers(cls) -> list[dict[str, str]]:
        return [
            {
                "name": "parichay-pothepalli/financial-research-mcp",
                "capability": "market-data",
                "description": "Prices, financial statements, crypto data, news, and SEC filings.",
            },
            {
                "name": "financialdata-net/financialdata-mcp",
                "capability": "market-data",
                "description": "Cross-asset prices and economic/earnings calendars.",
            },
            {
                "name": "coinmarketcap/coinmarketcap-mcp",
                "capability": "crypto-market-data",
                "description": "Crypto prices and market statistics.",
            },
            {
                "name": "openclaw/finnhub",
                "capability": "financial-news",
                "description": "Company news, quotes, filings, earnings, and calendars.",
            },
            {
                "name": "google-calendar/google-calendar-mcp",
                "capability": "economic-calendar",
                "description": "Calendar events and scheduled research.",
            },
            {
                "name": "github/github-mcp-server",
                "capability": "github-operations",
                "description": "GitHub issues, pull requests, repositories, and code.",
            },
        ]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Smithery MCP adapter")
    parser.add_argument(
        "command", choices=["search", "install", "list", "tools", "call", "recommended"]
    )
    parser.add_argument("value", nargs="?", help="Search query, server name, or connection id")
    parser.add_argument("--tool", help="Tool name for call")
    parser.add_argument("--arguments", default="{}", help="JSON arguments for call")
    parser.add_argument("--category")
    args = parser.parse_args()
    adapter = MCPAdapter()
    if args.command == "search":
        output = adapter.mcp_search(args.value or "", category=args.category)
    elif args.command == "install":
        output = adapter.mcp_install(args.value or "")
    elif args.command == "list":
        output = adapter.installed_servers
    elif args.command == "tools":
        output = adapter.mcp_list_tools()
    elif args.command == "call":
        output = adapter.call_tool(args.value or "", args.tool or "", json.loads(args.arguments))
    else:
        output = adapter.get_recommended_servers()
    print(json.dumps(output, indent=2))
