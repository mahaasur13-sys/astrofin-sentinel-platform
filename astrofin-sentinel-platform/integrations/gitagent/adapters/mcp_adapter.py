"""Smithery MCP registry adapter for GitAgent."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import httpx


class MCPAdapter:
    """Discover, connect, inspect, and invoke Smithery MCP servers."""

    api_base = "https://api.smithery.ai"

    def __init__(self, storage_path: str | Path | None = None) -> None:
        self.storage_path = Path(storage_path or Path.home() / ".gitagent" / "mcp")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.installed_servers: dict[str, dict[str, Any]] = {}
        self._load_installed()

    def _config_path(self) -> Path:
        return self.storage_path / "installed_servers.json"

    def _load_installed(self) -> None:
        path = self._config_path()
        if not path.exists():
            return
        try:
            value = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(value, dict):
            self.installed_servers = value

    def _save_installed(self) -> None:
        self._config_path().write_text(
            json.dumps(self.installed_servers, indent=2, sort_keys=True) + "\n"
        )

    @staticmethod
    def _connection_id(server_name: str) -> str:
        value = server_name.strip().removeprefix("@")
        value = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-")
        return value[:80] or "mcp-server"

    @staticmethod
    def _qualified_name(item: dict[str, Any]) -> str:
        return str(item.get("qualifiedName") or item.get("qualified_name") or item.get("name") or "")

    @staticmethod
    def _json_from_output(output: str) -> Any:
        text = output.strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        for line in text.splitlines():
            candidate = line.strip()
            if not candidate or candidate[0] not in "[{":
                continue
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
        return None

    @staticmethod
    def _extract_servers(value: Any) -> list[dict[str, Any]]:
        if isinstance(value, dict):
            value = value.get("servers", value.get("results", value.get("data", [])))
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

    @staticmethod
    def _extract_tools(value: Any) -> list[dict[str, Any]]:
        if isinstance(value, dict):
            value = value.get("tools", value.get("data", []))
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

    @staticmethod
    def _category_match(item: dict[str, Any], category: str) -> bool:
        keywords = {
            "financial": ("finance", "financial", "stock", "equity", "market", "trading"),
            "crypto": ("crypto", "bitcoin", "ethereum", "coin", "exchange", "blockchain"),
            "news": ("news", "rss", "media", "article", "sentiment"),
            "calendar": ("calendar", "schedule", "event", "availability"),
        }.get(category.lower(), (category.lower(),))
        text = " ".join(
            str(item.get(key, ""))
            for key in ("name", "qualifiedName", "qualified_name", "displayName", "description")
        ).lower()
        return any(keyword in text for keyword in keywords)

    def _cli_prefix(self) -> list[str]:
        executable = shutil.which("smithery")
        if executable:
            return [executable]
        return ["npx", "--yes", "smithery@latest"]

    def _run_cli(self, arguments: list[str], timeout: int = 60) -> subprocess.CompletedProcess[str]:
        command = self._cli_prefix() + ["--json", *arguments]
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=self.storage_path,
            check=False,
        )

    def _api_headers(self) -> dict[str, str]:
        token = os.environ.get("SMITHERY_API_KEY")
        return {"Authorization": f"Bearer {token}"} if token else {}

    def _get_fallback_servers(self, query: str) -> list[dict[str, Any]]:
        entries = [
            {
                "name": "@smithery/github",
                "qualifiedName": "github",
                "displayName": "GitHub",
                "description": "Manage repositories, issues, pull requests, and workflows.",
                "category": "development",
                "source": "fallback",
            },
            {
                "name": "financial-data/financial-data",
                "qualifiedName": "financial-data/financial-data",
                "displayName": "FinancialData.Net",
                "description": "Stocks, crypto, forex, fundamentals, filings, macro indicators, and event calendars.",
                "category": "financial",
                "source": "fallback",
            },
            {
                "name": "cfocoder/financial-modeling-prep-mcp-server",
                "qualifiedName": "cfocoder/financial-modeling-prep-mcp-server",
                "displayName": "Financial Modeling Prep",
                "description": "Quotes, statements, ratios, technical indicators, news, SEC filings, earnings, and calendars.",
                "category": "financial",
                "source": "fallback",
            },
            {
                "name": "google/news",
                "qualifiedName": "google/news",
                "displayName": "Google News",
                "description": "Current and recent news search for sentiment and event monitoring.",
                "category": "news",
                "source": "fallback",
            },
            {
                "name": "kwp-lab/rss-reader-mcp",
                "qualifiedName": "kwp-lab/rss-reader-mcp",
                "displayName": "RSS Reader",
                "description": "Read RSS feeds and extract current article content.",
                "category": "news",
                "source": "fallback",
            },
            {
                "name": "crypto",
                "qualifiedName": "crypto",
                "displayName": "Crypto.com",
                "description": "Access real-time and historical cryptocurrency market data.",
                "category": "crypto",
                "source": "fallback",
            },
            {
                "name": "truss44/mcp-crypto-price",
                "qualifiedName": "truss44/mcp-crypto-price",
                "displayName": "Crypto Price & Market Analysis Server",
                "description": "Real-time cryptocurrency price data and market analysis.",
                "category": "crypto",
                "source": "fallback",
            },
            {
                "name": "node2flow/bitkub",
                "qualifiedName": "node2flow/bitkub",
                "displayName": "Bitkub",
                "description": "Crypto exchange market data, OHLCV, order books, and dry-run orders.",
                "category": "crypto",
                "source": "fallback",
            },
            {
                "name": "googlecalendar",
                "qualifiedName": "googlecalendar",
                "displayName": "Google Calendar",
                "description": "Schedule events, check availability, and manage calendars.",
                "category": "calendar",
                "source": "fallback",
            },
            {
                "name": "node2flow/google-calendar",
                "qualifiedName": "node2flow/google-calendar",
                "displayName": "Google Calendar",
                "description": "Create events, manage calendars, and check availability.",
                "category": "calendar",
                "source": "fallback",
            },
            {
                "name": "upstash/context7-mcp",
                "qualifiedName": "upstash/context7-mcp",
                "displayName": "Context7",
                "description": "Retrieve current documentation for libraries and APIs.",
                "category": "research",
                "source": "fallback",
            },
            {
                "name": "exa",
                "qualifiedName": "exa",
                "displayName": "Exa",
                "description": "Search the web and retrieve current research results.",
                "category": "news",
                "source": "fallback",
            },
        ]
        query_lower = query.lower()
        if query_lower == "github":
            return [entries[0], {
                "name": "@modelcontextprotocol/server-github",
                "qualifiedName": "modelcontextprotocol/server-github",
                "description": "GitHub MCP tools for repositories and issues.",
                "category": "development",
                "source": "fallback",
            }]
        if query_lower == "filesystem":
            return [
                {
                    "name": "@smithery/filesystem",
                    "qualifiedName": "@smithery/filesystem",
                    "description": "Filesystem operations for local agent workflows.",
                    "category": "system",
                    "source": "fallback",
                },
                {
                    "name": "@modelcontextprotocol/server-filesystem",
                    "qualifiedName": "@modelcontextprotocol/server-filesystem",
                    "description": "Filesystem MCP server.",
                    "category": "system",
                    "source": "fallback",
                },
            ]
        if not query_lower:
            return entries
        return [
            item
            for item in entries
            if query_lower in json.dumps(item, ensure_ascii=False).lower()
        ]

    def mcp_search(self, query: str, category: str | None = None) -> list[dict[str, Any]]:
        """Search Smithery using the CLI and public registry API."""
        results: list[dict[str, Any]] = []
        try:
            completed = self._run_cli(["mcp", "search", query], timeout=30)
            if completed.returncode == 0:
                results.extend(self._extract_servers(self._json_from_output(completed.stdout)))
        except (FileNotFoundError, subprocess.SubprocessError):
            pass

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(
                    f"{self.api_base}/servers",
                    params={"q": query, "pageSize": 20},
                    headers=self._api_headers(),
                )
            if response.is_success:
                results.extend(self._extract_servers(response.json()))
        except (httpx.HTTPError, ValueError):
            pass

        if not results:
            results = self._get_fallback_servers(query)

        unique: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in results:
            qualified_name = self._qualified_name(item)
            if not qualified_name or qualified_name in seen:
                continue
            seen.add(qualified_name)
            normalized = dict(item)
            normalized.setdefault("name", qualified_name)
            normalized["qualifiedName"] = qualified_name
            unique.append(normalized)

        if category:
            unique = [item for item in unique if self._category_match(item, category)]
        return unique[:20]

    def mcp_install(
        self, server_name: str, config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Connect an MCP server through Smithery and persist its connection."""
        qualified_name = server_name.strip()
        connection_id = self._connection_id(qualified_name)
        command = ["mcp", "add", qualified_name, "--id", connection_id]
        if config:
            command.extend(["--config", json.dumps(config, separators=(",", ":"))])

        result: dict[str, Any] = {
            "status": "pending",
            "name": qualified_name,
            "connection_id": connection_id,
            "storage_path": str(self.storage_path),
        }
        try:
            completed = self._run_cli(command, timeout=90)
        except subprocess.TimeoutExpired:
            result.update(status="timeout", error="Smithery CLI timed out")
            return result
        except (FileNotFoundError, subprocess.SubprocessError) as exc:
            result.update(status="failed", error=str(exc))
            return result

        payload = self._json_from_output(completed.stdout)
        if completed.returncode != 0:
            result.update(status="failed", error=completed.stderr.strip() or "Smithery connection failed")
            if payload is not None:
                result["response"] = payload
            return result

        server_info = {
            "name": qualified_name,
            "connection_id": connection_id,
            "config": config or {},
        }
        self.installed_servers[connection_id] = server_info
        self._save_installed()
        result.update(status="installed", response=payload)
        return result

    def _tools_from_api(self, connection_id: str) -> list[dict[str, Any]]:
        namespace = os.environ.get("SMITHERY_NAMESPACE")
        if not namespace or not os.environ.get("SMITHERY_API_KEY"):
            return []
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(
                    f"{self.api_base}/connect/{namespace}/{connection_id}/.tools",
                    headers=self._api_headers(),
                )
            if response.is_success:
                return self._extract_tools(response.json())
        except (httpx.HTTPError, ValueError):
            pass
        return []

    def mcp_list_tools(self) -> list[dict[str, Any]]:
        """List tools exposed by all persisted MCP connections."""
        tools: list[dict[str, Any]] = []
        for connection_id, server_info in self.installed_servers.items():
            local_tools = server_info.get("tools", [])
            server_tools = [item for item in local_tools if isinstance(item, dict)]
            if not server_tools:
                try:
                    completed = self._run_cli(
                        ["tool", "list", connection_id, "--flat", "--limit", "1000"],
                        timeout=45,
                    )
                    if completed.returncode == 0:
                        server_tools = self._extract_tools(self._json_from_output(completed.stdout))
                except (FileNotFoundError, subprocess.SubprocessError):
                    server_tools = []
            if not server_tools:
                server_tools = self._tools_from_api(connection_id)
            for tool in server_tools:
                enriched = dict(tool)
                enriched["_server"] = server_info.get("name", connection_id)
                enriched["_connection_id"] = connection_id
                tools.append(self.wrap_tool(enriched))
        return tools

    def call_tool(
        self, connection_id: str, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> Any:
        """Invoke a tool through the Smithery CLI and return its JSON response."""
        if connection_id not in self.installed_servers:
            raise KeyError(f"Unknown MCP connection: {connection_id}")
        completed = self._run_cli(
            [
                "tool",
                "call",
                connection_id,
                tool_name,
                json.dumps(arguments or {}, separators=(",", ":")),
            ],
            timeout=90,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "MCP tool invocation failed")
        return self._json_from_output(completed.stdout) or completed.stdout.strip()

    def mcp_uninstall(self, connection_id: str) -> dict[str, str]:
        """Remove a Smithery connection and its local record."""
        if connection_id not in self.installed_servers:
            return {"status": "error", "message": f"Server {connection_id} not found"}
        try:
            completed = self._run_cli(["mcp", "remove", connection_id], timeout=30)
        except (FileNotFoundError, subprocess.SubprocessError) as exc:
            completed = None
            error = str(exc)
        else:
            error = completed.stderr.strip() if completed.returncode else ""
        del self.installed_servers[connection_id]
        self._save_installed()
        if error:
            return {"status": "success", "message": f"Removed local record: {error}"}
        return {"status": "success", "message": f"Uninstalled {connection_id}"}

    def wrap_tool(self, tool_def: dict[str, Any]) -> dict[str, Any]:
        """Convert an MCP tool definition to the GitAgent tool shape."""
        connection_id = str(tool_def.get("_connection_id") or tool_def.get("connection_id") or "")
        return {
            "name": tool_def.get("name", "unnamed_tool"),
            "description": tool_def.get("description", ""),
            "input_schema": tool_def.get("inputSchema", tool_def.get("input_schema", {})),
            "output_schema": tool_def.get("outputSchema", tool_def.get("output_schema", {})),
            "server": tool_def.get("_server", tool_def.get("server", "unknown")),
            "connection_id": connection_id,
            "original_def": tool_def,
        }

    def get_recommended_servers(self) -> list[dict[str, Any]]:
        """Return verified starting points and discovery queries for AstroFin."""
        return [
            {
                "name": "financial-data/financial-data",
                "category": "financial",
                "description": "Stocks, crypto, forex, fundamentals, filings, macro indicators, and event calendars.",
                "discovery_query": "financial market data fundamentals SEC macro",
                "relevance": "high",
            },
            {
                "name": "cfocoder/financial-modeling-prep-mcp-server",
                "category": "financial",
                "description": "Quotes, statements, ratios, technical indicators, news, SEC filings, earnings, and calendars.",
                "discovery_query": "financial modeling prep market data",
                "relevance": "high",
            },
            {
                "name": "google/news",
                "category": "news",
                "description": "Current and recent news search for sentiment and event monitoring.",
                "discovery_query": "financial news search",
                "relevance": "high",
            },
            {
                "name": "kwp-lab/rss-reader-mcp",
                "category": "news",
                "description": "Read RSS feeds and extract current article content.",
                "discovery_query": "RSS news feeds",
                "relevance": "medium",
            },
            {
                "name": "crypto",
                "category": "crypto",
                "description": "Real-time and historical cryptocurrency market data.",
                "discovery_query": "crypto market data",
                "relevance": "high",
            },
            {
                "name": "truss44/mcp-crypto-price",
                "category": "crypto",
                "description": "Real-time crypto prices and market analysis.",
                "discovery_query": "crypto price market analysis",
                "relevance": "high",
            },
            {
                "name": "node2flow/bitkub",
                "category": "crypto",
                "description": "Crypto exchange ticker, OHLCV, order book, and dry-run order tools.",
                "discovery_query": "crypto exchange market data",
                "relevance": "medium",
            },
            {
                "name": "googlecalendar",
                "category": "calendar",
                "description": "Calendar availability and event-management tools.",
                "discovery_query": "calendar availability events",
                "relevance": "medium",
            },
            {
                "name": "node2flow/google-calendar",
                "category": "calendar",
                "description": "Google Calendar scheduling and availability.",
                "discovery_query": "Google Calendar MCP",
                "relevance": "medium",
            },
            {
                "name": "github",
                "category": "development",
                "description": "Repository, issue, pull-request, and workflow tools.",
                "discovery_query": "github",
                "relevance": "high",
            },
            {
                "name": "upstash/context7-mcp",
                "category": "research",
                "description": "Current documentation and API reference retrieval.",
                "discovery_query": "documentation search",
                "relevance": "medium",
            },
            {
                "name": "exa",
                "category": "news",
                "description": "Web research useful for news and sentiment inputs.",
                "discovery_query": "web search news",
                "relevance": "high",
            },
        ]
