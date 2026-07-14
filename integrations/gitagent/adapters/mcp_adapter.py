"""
MCP Adapter for Smithery/GitHub Tools
Integrates with Smithery MCP registry to search, install, and wrap MCP tools
as GitAgent-compatible tools.
"""

from __future__ import annotations


import json
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Any, Optional
import httpx


class MCPAdapter:
    """
    MCP Adapter that integrates with Smithery registry to search, install,
    and wrap MCP tools as GitAgent-compatible tools.

    Supports:
    - Smithery CLI (`npx @smithery/cli`) for server management
    - Direct REST API for registry queries
    - Dynamic MCP server installation and tool wrapping
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = (
            Path(storage_path) if storage_path else Path.home() / ".gitagent" / "mcp"
        )
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.installed_servers: dict[str, dict[str, Any]] = {}
        self._load_installed()

        # Smithery API base
        self.api_base = "https://api.smithery.dev/v1"
        # Fallback registry API
        self.registry_api = "https://registry.smithery.ai"

    def _load_installed(self):
        """Load previously installed servers from disk."""
        config_file = self.storage_path / "installed_servers.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    self.installed_servers = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.installed_servers = {}

    def _save_installed(self):
        """Persist installed servers to disk."""
        config_file = self.storage_path / "installed_servers.json"
        with open(config_file, "w") as f:
            json.dump(self.installed_servers, f, indent=2)

    def _get_fallback_servers(self, query: str) -> list[dict[str, Any]]:
        """Get fallback server list for common queries when network is unavailable."""
        query_lower = query.lower()
        fallback_db = {
            "github": [
                {
                    "name": "@smithery/github",
                    "description": "GitHub API integration for code, issues, PRs",
                    "category": "development",
                },
                {
                    "name": "@modelcontextprotocol/server-github",
                    "description": "GitHub MCP server",
                    "category": "development",
                },
            ],
            "filesystem": [
                {
                    "name": "@smithery/filesystem",
                    "description": "Local filesystem operations",
                    "category": "system",
                },
                {
                    "name": "@modelcontextprotocol/server-filesystem",
                    "description": "Filesystem MCP server",
                    "category": "system",
                },
            ],
            "search": [
                {
                    "name": "@modelcontextprotocol/server-brave-search",
                    "description": "Web search capabilities",
                    "category": "search",
                },
                {
                    "name": "@smithery/brave-search",
                    "description": "Brave Search API integration",
                    "category": "search",
                },
            ],
            "slack": [
                {
                    "name": "@modelcontextprotocol/server-slack",
                    "description": "Slack messaging integration",
                    "category": "communication",
                },
                {
                    "name": "@smithery/slack",
                    "description": "Slack API MCP server",
                    "category": "communication",
                },
            ],
            "postgres": [
                {
                    "name": "@modelcontextprotocol/server-postgres",
                    "description": "PostgreSQL database access",
                    "category": "database",
                },
                {
                    "name": "@smithery/postgres",
                    "description": "PostgreSQL MCP server",
                    "category": "database",
                },
            ],
            "finance": [
                {
                    "name": "yahoo-finance-mcp",
                    "description": "Yahoo Finance data (stocks, crypto, options)",
                    "category": "financial",
                },
                {
                    "name": "bloomberg-mcp",
                    "description": "Bloomberg API integration",
                    "category": "financial",
                },
            ],
            "crypto": [
                {
                    "name": "coinmarketcap-mcp",
                    "description": "Cryptocurrency price data",
                    "category": "crypto",
                },
                {
                    "name": "binance-mcp",
                    "description": "Binance crypto exchange API",
                    "category": "crypto",
                },
            ],
            "news": [
                {
                    "name": "newsapi-mcp",
                    "description": "News API for financial news aggregation",
                    "category": "news",
                },
                {
                    "name": "rss-mcp",
                    "description": "RSS feed reader for news aggregation",
                    "category": "news",
                },
            ],
            "calendar": [
                {
                    "name": "google-calendar-mcp",
                    "description": "Google Calendar integration",
                    "category": "calendar",
                },
                {
                    "name": "@modelcontextprotocol/server-google-calendar",
                    "description": "Google Calendar MCP",
                    "category": "calendar",
                },
            ],
            "postgres": [
                {
                    "name": "@modelcontextprotocol/server-postgres",
                    "description": "PostgreSQL database access",
                    "category": "database",
                },
            ],
            "memory": [
                {
                    "name": "@modelcontextprotocol/server-memory",
                    "description": "Persistent memory storage",
                    "category": "system",
                },
            ],
        }

        for key, servers in fallback_db.items():
            if key in query_lower:
                return servers
        return []

    def mcp_search(
        self, query: str, category: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Search Smithery registry for MCP servers matching query.

        Args:
            query: Search query (e.g., "github", "crypto", "calendar")
            category: Optional category filter (financial, crypto, news, calendar)

        Returns:
            List of matching MCP server definitions
        """
        results = []

        # Try Smithery CLI first
        try:
            result = subprocess.run(
                ["npx", "@smithery/cli", "search", query, "--json"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.storage_path,
            )
            if result.returncode == 0 and result.stdout.strip():
                try:
                    cli_results = json.loads(result.stdout)
                    # CLI might return a dict with keys like "servers" - extract properly
                    if isinstance(cli_results, dict):
                        if "servers" in cli_results:
                            results.extend(cli_results["servers"])
                        elif "results" in cli_results:
                            results.extend(cli_results["results"])
                        elif "data" in cli_results:
                            results.extend(cli_results["data"])
                        elif isinstance(cli_results.get("name"), str):
                            # Single server dict
                            results.append(cli_results)
                    elif isinstance(cli_results, list):
                        results.extend(cli_results)
                except json.JSONDecodeError:
                    # If stdout isn't JSON, treat each line as a potential server name
                    for line in result.stdout.strip().split("\n"):
                        line = line.strip()
                        if line and not line.startswith("{"):
                            results.append({"name": line, "description": ""})
        except (subprocess.SubprocessError, FileNotFoundError, Exception):
            pass

        # Try REST API as fallback
        try:
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            with httpx.Client(timeout=15.0, verify=False, http2=True) as client:
                resp = client.get(
                    f"{self.api_base}/servers", params={"q": query, "limit": 20}
                )
                if resp.status_code == 200:
                    api_results = resp.json()
                    if isinstance(api_results, dict):
                        # Extract servers from response (handle {"servers": [...]} format)
                        if "servers" in api_results:
                            results.extend(api_results["servers"])
                        # Also check for "results" key
                        elif "results" in api_results:
                            results.extend(api_results["results"])
                        # If it's a direct list in "data" key
                        elif "data" in api_results:
                            results.extend(api_results["data"])
                    elif isinstance(api_results, list):
                        results.extend(api_results)
        except Exception:
            pass

        # If no results from API or CLI, use fallback mock data for common queries
        if not results:
            results = self._get_fallback_servers(query)

        # Deduplicate by name
        seen = set()
        unique_results = []
        for r in results:
            # Handle both string and dict results
            if isinstance(r, str):
                name = r
            elif isinstance(r, dict):
                name = r.get("name", r.get("qualified_name", ""))
            else:
                continue
            if name and name not in seen:
                seen.add(name)
                unique_results.append(r)

        # Filter by category if specified
        if category:
            category_keywords = {
                "financial": ["finance", "stock", "trading", "bloomberg", "yahoo"],
                "crypto": ["crypto", "bitcoin", "ethereum", "defi", "binance"],
                "news": ["news", "rss", "feed", "media"],
                "calendar": ["calendar", "schedule", "google-calendar"],
            }
            keywords = category_keywords.get(category.lower(), [])
            filtered = []
            for r in unique_results:
                desc = r.get("description", "").lower()
                name = r.get("name", "").lower()
                if any(kw in desc or kw in name for kw in keywords):
                    filtered.append(r)
            return filtered

        return unique_results[:20]

    def mcp_install(
        self, server_name: str, config: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Install an MCP server from Smithery registry.

        Args:
            server_name: Server name (e.g., "@smithery/github", "yahoo-finance")
            config: Optional configuration dict for the server

        Returns:
            Installation result with status and server details
        """
        install_id = f"mcp_{server_name.replace('/', '_').replace('@', '')}"
        install_path = self.storage_path / "servers" / install_id
        install_path.mkdir(parents=True, exist_ok=True)

        result = {
            "status": "pending",
            "name": server_name,
            "install_path": str(install_path),
        }

        try:
            # Use Smithery CLI to install
            cmd = ["npx", "@smithery/cli", "mcp", "add", server_name]
            if config:
                # Write config to temp file
                config_file = install_path / "config.json"
                with open(config_file, "w") as f:
                    json.dump(config, f)
                cmd.extend(["--config", str(config_file)])

            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120, cwd=install_path
            )

            if proc.returncode == 0:
                result["status"] = "installed"
                result["stdout"] = proc.stdout

                # Save server info
                self.installed_servers[install_id] = {
                    "name": server_name,
                    "install_path": str(install_path),
                    "config": config or {},
                }
                self._save_installed()
            else:
                result["status"] = "failed"
                result["stderr"] = proc.stderr

        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
        except FileNotFoundError:
            # npx not available, try direct npm install
            try:
                npm_name = (
                    server_name if server_name.startswith("@") else f"@{server_name}"
                )
                subprocess.run(
                    ["npm", "install", "-g", npm_name], capture_output=True, timeout=60
                )
                result["status"] = "installed"
                self.installed_servers[install_id] = {
                    "name": server_name,
                    "install_path": str(install_path),
                    "config": config or {},
                }
                self._save_installed()
            except Exception as e:
                result["status"] = "failed"
                result["error"] = str(e)
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

        return result

    def mcp_list_tools(self) -> list[dict[str, Any]]:
        """
        List all available tools from installed MCP servers.

        Returns:
            List of tool definitions from all installed servers
        """
        tools = []

        for install_id, server_info in self.installed_servers.items():
            server_name = server_info["name"]
            install_path = server_info.get("install_path", "")

            # Try to get tools via Smithery CLI
            try:
                result = subprocess.run(
                    ["npx", "@smithery/cli", "tools", server_name, "--json"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=install_path or self.storage_path,
                )
                if result.returncode == 0 and result.stdout.strip():
                    try:
                        server_tools = json.loads(result.stdout)
                        for tool in server_tools:
                            tool["_server"] = server_name
                            tool["_install_id"] = install_id
                        tools.extend(server_tools)
                    except json.JSONDecodeError:
                        pass
            except Exception:
                pass

            # Also check for server manifest
            if install_path:
                manifest_path = Path(install_path) / "manifest.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path) as f:
                            manifest = json.load(f)
                            if "tools" in manifest:
                                for tool in manifest["tools"]:
                                    tool["_server"] = server_name
                                    tool["_install_id"] = install_id
                                tools.extend(manifest["tools"])
                    except (json.JSONDecodeError, IOError):
                        pass

        return tools

    def mcp_uninstall(self, install_id: str) -> dict[str, str]:
        """Uninstall an MCP server."""
        if install_id not in self.installed_servers:
            return {"status": "error", "message": f"Server {install_id} not found"}

        try:
            server_name = self.installed_servers[install_id]["name"]
            subprocess.run(
                ["npx", "@smithery/cli", "remove", server_name],
                capture_output=True,
                timeout=30,
            )
        except Exception:
            pass

        del self.installed_servers[install_id]
        self._save_installed()

        return {"status": "success", "message": f"Uninstalled {install_id}"}

    def wrap_tool(self, tool_def: dict[str, Any]) -> dict[str, Any]:
        """
        Wrap an MCP tool definition as a GitAgent-compatible tool.

        Args:
            tool_def: Raw tool definition from MCP server

        Returns:
            GitAgent-compatible tool definition
        """
        return {
            "name": tool_def.get("name", "unnamed_tool"),
            "description": tool_def.get("description", ""),
            "input_schema": tool_def.get(
                "inputSchema", tool_def.get("input_schema", {})
            ),
            "server": tool_def.get("_server", "unknown"),
            "original_def": tool_def,
        }

    def get_recommended_servers(self) -> list[dict[str, Any]]:
        """
        Get recommended MCP servers for financial/trading agents.

        Returns:
            List of recommended servers with descriptions
        """
        return [
            {
                "name": "@smithery/github",
                "description": "GitHub API integration for code, issues, PRs",
                "category": "development",
                "relevance": "high",
            },
            {
                "name": "@smithery/filesystem",
                "description": "Local filesystem operations",
                "category": "system",
                "relevance": "high",
            },
            {
                "name": "@modelcontextprotocol/server-brave-search",
                "description": "Web search capabilities",
                "category": "search",
                "relevance": "high",
            },
            {
                "name": "@modelcontextprotocol/server-slack",
                "description": "Slack messaging integration",
                "category": "communication",
                "relevance": "medium",
            },
            {
                "name": "@modelcontextprotocol/server-postgres",
                "description": "PostgreSQL database access",
                "category": "database",
                "relevance": "high",
            },
            {
                "name": "yahoo-finance-mcp",
                "description": "Yahoo Finance data (stocks, crypto, options)",
                "category": "financial",
                "relevance": "high",
            },
            {
                "name": "coinmarketcap-mcp",
                "description": "Cryptocurrency price data and market info",
                "category": "crypto",
                "relevance": "high",
            },
            {
                "name": "newsapi-mcp",
                "description": "News API for financial news aggregation",
                "category": "news",
                "relevance": "high",
            },
            {
                "name": "google-calendar-mcp",
                "description": "Google Calendar integration for scheduling",
                "category": "calendar",
                "relevance": "medium",
            },
            {
                "name": "stripe-mcp",
                "description": "Stripe payment and billing data",
                "category": "financial",
                "relevance": "medium",
            },
        ]


def main():
    """CLI entry point for MCP adapter."""
    import argparse

    parser = argparse.ArgumentParser(description="MCP Adapter for GitAgent")
    parser.add_argument(
        "command", choices=["search", "install", "list", "tools", "recommended"]
    )
    parser.add_argument("query", nargs="?", help="Search query or server name")
    parser.add_argument(
        "--category", help="Category filter (financial, crypto, news, calendar)"
    )
    parser.add_argument("--config", help="JSON config file for server")

    args = parser.parse_args()
    adapter = MCPAdapter()

    if args.command == "search":
        results = adapter.mcp_search(args.query or "", category=args.category)
        print(json.dumps(results, indent=2))

    elif args.command == "install":
        config = None
        if args.config:
            with open(args.config) as f:
                config = json.load(f)
        result = adapter.mcp_install(args.query, config=config)
        print(json.dumps(result, indent=2))

    elif args.command == "list":
        servers = adapter.installed_servers
        print(json.dumps(servers, indent=2))

    elif args.command == "tools":
        tools = adapter.mcp_list_tools()
        print(json.dumps(tools, indent=2))

    elif args.command == "recommended":
        servers = adapter.get_recommended_servers()
        print(json.dumps(servers, indent=2))


if __name__ == "__main__":
    main()
