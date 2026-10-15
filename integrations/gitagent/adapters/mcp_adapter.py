"""Unified MCP transports for GitAgent."""

from __future__ import annotations

import json
import os
import re
import select
import shutil
import subprocess
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import httpx


class MCPError(RuntimeError):
    """Base error for MCP transport and policy failures."""


class MCPAuthError(MCPError):
    """The server rejected authentication or authorization."""


class MCPTimeoutError(MCPError):
    """The server did not answer within the configured timeout."""


class MCPProtocolError(MCPError):
    """The server returned an invalid JSON-RPC message."""


class MCPToolError(MCPError):
    """The MCP server returned a tool execution error."""


class MCPWriteDenied(MCPError):
    """A write-capable tool was requested without explicit permission."""


class _StdioTransport:
    def __init__(
        self,
        command: list[str],
        env: Mapping[str, str] | None,
        cwd: str | Path | None,
        timeout: float,
    ) -> None:
        if not command:
            raise ValueError("stdio command must not be empty")
        self.command = list(command)
        self.env = dict(env or {})
        self.cwd = str(cwd) if cwd else None
        self.timeout = timeout
        self.process: subprocess.Popen[bytes] | None = None
        self._next_id = 0

    def start(self) -> None:
        if self.process and self.process.poll() is None:
            return
        child_env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
            "LANG": os.environ.get("LANG", "C.UTF-8"),
        }
        child_env.update(self.env)
        self.process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=child_env,
            cwd=self.cwd,
        )

    def _readable(self, timeout: float) -> bool:
        if not self.process or not self.process.stdout:
            raise MCPProtocolError("stdio process is not connected")
        ready, _, _ = select.select([self.process.stdout], [], [], timeout)
        return bool(ready)

    def _read_exact(self, size: int) -> bytes:
        if not self.process or not self.process.stdout:
            raise MCPProtocolError("stdio process is not connected")
        chunks: list[bytes] = []
        remaining = size
        deadline = time.monotonic() + self.timeout
        while remaining:
            left = deadline - time.monotonic()
            if left <= 0 or not self._readable(left):
                raise MCPTimeoutError("MCP stdio response timed out")
            chunk = self.process.stdout.read(remaining)
            if not chunk:
                raise MCPProtocolError("MCP stdio process closed its output")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def _read_message(self) -> dict[str, Any]:
        if not self.process or not self.process.stdout:
            raise MCPProtocolError("stdio process is not connected")
        deadline = time.monotonic() + self.timeout
        saw_output = False
        while True:
            left = deadline - time.monotonic()
            if left <= 0 or not self._readable(left):
                raise MCPTimeoutError("MCP stdio response timed out")
            line = self.process.stdout.readline()
            if not line:
                if self.process.poll() is not None:
                    if saw_output:
                        raise MCPProtocolError("MCP stdio process closed after invalid output")
                    raise MCPTimeoutError("MCP stdio process closed without a response")
                raise MCPProtocolError("MCP stdio process closed its output")
            saw_output = True
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith(b"{"):
                payload = stripped
            elif stripped.lower().startswith(b"content-length:"):
                try:
                    length = int(stripped.split(b":", 1)[1].strip())
                except (IndexError, ValueError) as exc:
                    raise MCPProtocolError("invalid Content-Length header") from exc
                while True:
                    header = self.process.stdout.readline()
                    if not header:
                        raise MCPProtocolError("MCP stdio headers ended unexpectedly")
                    if header in (b"\n", b"\r\n"):
                        break
                payload = self._read_exact(length)
            else:
                continue
            try:
                value = json.loads(payload.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise MCPProtocolError("invalid JSON-RPC response") from exc
            if not isinstance(value, dict):
                raise MCPProtocolError("JSON-RPC response must be an object")
            return value

    def request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        self.start()
        if not self.process or not self.process.stdin:
            raise MCPProtocolError("stdio process is not connected")
        is_notification = method.startswith("notifications/")
        if not is_notification:
            self._next_id += 1
        request_id = self._next_id if not is_notification else None
        request = {"jsonrpc": "2.0", "method": method}
        if request_id is not None:
            request["id"] = request_id
        if params is not None:
            request["params"] = params
        try:
            self.process.stdin.write((json.dumps(request) + "\n").encode("utf-8"))
            self.process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise MCPProtocolError("MCP stdio process is unavailable") from exc
        if is_notification:
            return None
        while True:
            response = self._read_message()
            if response.get("id") != request_id:
                continue
            error = response.get("error")
            if error:
                message = str(error.get("message", error)) if isinstance(error, dict) else str(error)
                lowered = message.lower()
                if "auth" in lowered or "token" in lowered or "unauthorized" in lowered:
                    raise MCPAuthError("MCP authentication failed")
                raise MCPToolError(message)
            return response.get("result")

    def close(self) -> None:
        process, self.process = self.process, None
        if not process:
            return
        if process.stdin:
            process.stdin.close()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=1)


class MCPAdapter:
    """Connect to stdio or Smithery MCP servers through one synchronous API."""

    api_base = "https://api.smithery.ai"
    _write_markers = re.compile(
        r"(?:^|[_-])(create|update|delete|remove|write|push|merge|close|cancel|set|add|edit|modify|comment|assign|fork|dispatch|release|publish|upload|move|rename|archive|enable|disable)(?:$|[_-])",
        re.IGNORECASE,
    )

    def __init__(
        self,
        storage_path: str | Path | None = None,
        *,
        transport: str = "smithery",
        server: str | None = None,
        command: list[str] | None = None,
        env: Mapping[str, str] | None = None,
        cwd: str | Path | None = None,
        timeout: float = 30.0,
        retries: int = 2,
    ) -> None:
        self.storage_path = Path(storage_path or Path.home() / ".gitagent" / "mcp")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.transport_name = transport.lower()
        if self.transport_name not in {"stdio", "smithery"}:
            raise ValueError("transport must be 'stdio' or 'smithery'")
        self.server = server
        self.timeout = timeout
        self.retries = max(0, retries)
        self.allow_write = os.environ.get("MCP_ALLOW_WRITE", "").lower() == "true"
        self._stdio: _StdioTransport | None = None
        self._initialized = False
        self._tools: list[dict[str, Any]] = []
        if self.transport_name == "stdio":
            if command is None:
                raise ValueError("stdio transport requires command")
            self._stdio = _StdioTransport(command, env, cwd, timeout)
        self.installed_servers: dict[str, dict[str, Any]] = {}
        self._load_installed()

    @classmethod
    def from_stdio(
        cls,
        command: list[str],
        *,
        env: Mapping[str, str] | None = None,
        cwd: str | Path | None = None,
        timeout: float = 30.0,
        retries: int = 2,
    ) -> MCPAdapter:
        return cls(
            transport="stdio",
            command=command,
            env=env,
            cwd=cwd,
            timeout=timeout,
            retries=retries,
        )

    @classmethod
    def from_smithery(
        cls,
        server: str,
        *,
        storage_path: str | Path | None = None,
        timeout: float = 30.0,
        retries: int = 2,
    ) -> MCPAdapter:
        return cls(
            storage_path=storage_path,
            transport="smithery",
            server=server,
            timeout=timeout,
            retries=retries,
        )

    def _config_path(self) -> Path:
        return self.storage_path / "installed_servers.json"

    def _load_installed(self) -> None:
        path = self._config_path()
        if not path.exists():
            return
        try:
            value = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            value = {}
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
            candidates = (line.strip() for line in text.splitlines())
            for candidate in candidates:
                if candidate and candidate[0] in "[{":
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        continue
        return None

    @staticmethod
    def _extract_servers(value: Any) -> list[dict[str, Any]]:
        if isinstance(value, dict):
            value = value.get("servers", value.get("results", value.get("data", [])))
        return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []

    @staticmethod
    def _extract_tools(value: Any) -> list[dict[str, Any]]:
        if isinstance(value, dict):
            value = value.get("tools", value.get("data", []))
        return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []

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
        return [executable] if executable else ["npx", "--yes", "smithery@latest"]

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

    @staticmethod
    def _api_headers() -> dict[str, str]:
        token = os.environ.get("SMITHERY_API_KEY")
        return {"Authorization": f"Bearer {token}"} if token else {}

    @staticmethod
    def _smithery_namespace() -> str | None:
        namespace = os.environ.get("SMITHERY_NAMESPACE", "").strip()
        return namespace or None

    @staticmethod
    def _contains_sensitive_config(value: Any) -> bool:
        sensitive = ("key", "token", "secret", "password", "credential", "authorization")
        if isinstance(value, dict):
            return any(
                any(word in str(key).lower() for word in sensitive)
                or MCPAdapter._contains_sensitive_config(item)
                for key, item in value.items()
            )
        if isinstance(value, list):
            return any(MCPAdapter._contains_sensitive_config(item) for item in value)
        return False

    @staticmethod
    def _redact_config(value: Any) -> Any:
        sensitive = ("key", "token", "secret", "password", "credential", "authorization")
        if isinstance(value, dict):
            return {
                key: "[REDACTED]" if any(word in key.lower() for word in sensitive) else MCPAdapter._redact_config(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [MCPAdapter._redact_config(item) for item in value]
        return value

    @staticmethod
    def _redact_text(value: str) -> str:
        value = re.sub(r"(?i)(bearer\s+)[^\s,;]+", r"\1[REDACTED]", value)
        value = re.sub(r"(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]+)", "[REDACTED]", value)
        for secret_name in ("GITHUB_PERSONAL_ACCESS_TOKEN", "SMITHERY_API_KEY"):
            secret = os.environ.get(secret_name)
            if secret:
                value = value.replace(secret, "[REDACTED]")
        return value

    def _get_fallback_servers(self, query: str) -> list[dict[str, Any]]:
        entries = [
            {"name": "@smithery/github", "qualifiedName": "github", "displayName": "GitHub", "description": "Manage repositories, issues, pull requests, and workflows.", "category": "development", "source": "fallback"},
            {"name": "financial-data/financial-data", "qualifiedName": "financial-data/financial-data", "displayName": "FinancialData.Net", "description": "Stocks, crypto, forex, fundamentals, filings, macro indicators, and event calendars.", "category": "financial", "source": "fallback"},
            {"name": "cfocoder/financial-modeling-prep-mcp-server", "qualifiedName": "cfocoder/financial-modeling-prep-mcp-server", "displayName": "Financial Modeling Prep", "description": "Quotes, statements, ratios, technical indicators, news, SEC filings, earnings, and calendars.", "category": "financial", "source": "fallback"},
            {"name": "google/news", "qualifiedName": "google/news", "displayName": "Google News", "description": "Current and recent news search for sentiment and event monitoring.", "category": "news", "source": "fallback"},
            {"name": "kwp-lab/rss-reader-mcp", "qualifiedName": "kwp-lab/rss-reader-mcp", "displayName": "RSS Reader", "description": "Read RSS feeds and extract current article content.", "category": "news", "source": "fallback"},
            {"name": "crypto", "qualifiedName": "crypto", "displayName": "Crypto.com", "description": "Access real-time and historical cryptocurrency market data.", "category": "crypto", "source": "fallback"},
            {"name": "truss44/mcp-crypto-price", "qualifiedName": "truss44/mcp-crypto-price", "displayName": "Crypto Price & Market Analysis Server", "description": "Real-time cryptocurrency price data and market analysis.", "category": "crypto", "source": "fallback"},
            {"name": "node2flow/bitkub", "qualifiedName": "node2flow/bitkub", "displayName": "Bitkub", "description": "Crypto exchange market data, OHLCV, order books, and dry-run orders.", "category": "crypto", "source": "fallback"},
            {"name": "googlecalendar", "qualifiedName": "googlecalendar", "displayName": "Google Calendar", "description": "Schedule events, check availability, and manage calendars.", "category": "calendar", "source": "fallback"},
            {"name": "node2flow/google-calendar", "qualifiedName": "node2flow/google-calendar", "displayName": "Google Calendar", "description": "Create events, manage calendars, and check availability.", "category": "calendar", "source": "fallback"},
            {"name": "upstash/context7-mcp", "qualifiedName": "upstash/context7-mcp", "displayName": "Context7", "description": "Retrieve current documentation for libraries and APIs.", "category": "research", "source": "fallback"},
            {"name": "exa", "qualifiedName": "exa", "displayName": "Exa", "description": "Search the web and retrieve current research results.", "category": "news", "source": "fallback"},
        ]
        lower = query.lower()
        if lower == "github":
            return [entries[0], {"name": "@modelcontextprotocol/server-github", "qualifiedName": "modelcontextprotocol/server-github", "description": "GitHub MCP tools for repositories and issues.", "category": "development", "source": "fallback"}]
        if lower == "filesystem":
            return [{"name": "@smithery/filesystem", "qualifiedName": "@smithery/filesystem", "description": "Filesystem operations for local agent workflows.", "category": "system", "source": "fallback"}, {"name": "@modelcontextprotocol/server-filesystem", "qualifiedName": "@modelcontextprotocol/server-filesystem", "description": "Filesystem MCP server.", "category": "system", "source": "fallback"}]
        if not lower:
            return entries
        return [item for item in entries if lower in json.dumps(item, ensure_ascii=False).lower()]

    def mcp_search(self, query: str, category: str | None = None) -> list[dict[str, Any]]:
        """Search the Smithery registry, preferring the public API then CLI."""
        results: list[dict[str, Any]] = []
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(f"{self.api_base}/servers", params={"q": query, "pageSize": 20}, headers=self._api_headers())
            if response.is_success:
                results.extend(self._extract_servers(response.json()))
        except (httpx.HTTPError, ValueError):
            results = []
        if not results:
            try:
                completed = self._run_cli(["mcp", "search", query], timeout=30)
                if completed.returncode == 0:
                    results.extend(self._extract_servers(self._json_from_output(completed.stdout)))
            except (FileNotFoundError, subprocess.SubprocessError):
                results = []
        if not results:
            results = self._get_fallback_servers(query)
        unique: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in results:
            qualified_name = self._qualified_name(item)
            if qualified_name and qualified_name not in seen:
                seen.add(qualified_name)
                normalized = dict(item)
                normalized.setdefault("name", qualified_name)
                normalized["qualifiedName"] = qualified_name
                unique.append(normalized)
        if category:
            unique = [item for item in unique if self._category_match(item, category)]
        return unique[:20]

    def mcp_install(self, server_name: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
        """Register a Smithery connection without putting credentials in argv."""
        qualified_name = server_name.strip()
        connection_id = self._connection_id(qualified_name)
        result: dict[str, Any] = {"status": "pending", "name": qualified_name, "connection_id": connection_id, "storage_path": str(self.storage_path), "transport": "smithery"}
        command = ["mcp", "add", qualified_name, "--id", connection_id]
        namespace = self._smithery_namespace()
        if namespace:
            command.extend(["--namespace", namespace])
        if config and not self._contains_sensitive_config(config):
            command.extend(["--config", json.dumps(config, separators=(",", ":"))])
        try:
            completed = self._run_cli(command, timeout=90)
        except subprocess.TimeoutExpired:
            return {**result, "status": "timeout", "error": "Smithery CLI timed out"}
        except (FileNotFoundError, subprocess.SubprocessError) as exc:
            return {**result, "status": "failed", "error": self._redact_text(str(exc))}
        payload = self._json_from_output(completed.stdout)
        if completed.returncode != 0:
            error = self._redact_text(completed.stderr.strip() or "Smithery connection failed")
            failed = {**result, "status": "failed", "error": error}
            if payload is not None:
                failed["response"] = payload
            return failed
        self.installed_servers[connection_id] = {
            "name": qualified_name,
            "connection_id": connection_id,
            "transport": "smithery",
            "config": self._redact_config(config or {}),
        }
        self._save_installed()
        return {**result, "status": "installed", "response": payload}

    def _resolve_connection(self, server: str | None = None) -> str:
        value = server or self.server
        if not value:
            raise MCPError("Smithery transport requires server or connection id")
        if value in self.installed_servers:
            return value
        for connection_id, info in self.installed_servers.items():
            if info.get("name") == value:
                return connection_id
        return self._connection_id(value)

    def _smithery_tools(self, connection_id: str) -> list[dict[str, Any]]:
        info = self.installed_servers.get(connection_id, {})
        local_tools = info.get("tools", [])
        tools = [item for item in local_tools if isinstance(item, dict)] if isinstance(local_tools, list) else []
        if tools:
            return tools
        try:
            command = ["tool", "list", connection_id, "--flat", "--limit", "1000"]
            namespace = self._smithery_namespace()
            if namespace:
                command.extend(["--namespace", namespace])
            completed = self._run_cli(command, timeout=int(self.timeout))
        except (FileNotFoundError, subprocess.SubprocessError) as exc:
            raise MCPError(self._redact_text(str(exc))) from exc
        if completed.returncode != 0:
            message = self._redact_text(completed.stderr.strip() or "Smithery tool listing failed")
            if "auth" in message.lower() or "unauthorized" in message.lower() or "token" in message.lower():
                raise MCPAuthError("Smithery authentication failed")
            raise MCPError(message)
        return self._extract_tools(self._json_from_output(completed.stdout))

    def _initialize_once(self) -> dict[str, Any]:
        if self.transport_name == "stdio":
            assert self._stdio is not None
            result = self._stdio.request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "gitagent", "version": "1.0"}})
            self._stdio.request("notifications/initialized")
            return result if isinstance(result, dict) else {"result": result}
        connection_id = self._resolve_connection()
        self._tools = self._smithery_tools(connection_id)
        return {"protocolVersion": "smithery-cli", "connectionId": connection_id}

    def initialize(self) -> dict[str, Any]:
        """Perform the MCP handshake and make the adapter ready for calls."""
        if self._initialized:
            return {"status": "initialized", "transport": self.transport_name}
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                result = self._initialize_once()
                self._initialized = True
                if isinstance(result, dict):
                    return result
                return {"result": result}
            except (MCPAuthError, MCPToolError, MCPProtocolError, MCPTimeoutError, MCPError) as exc:
                last_error = exc
                self.close()
                if attempt < self.retries:
                    time.sleep(min(0.25 * (attempt + 1), 1.0))
        assert last_error is not None
        raise last_error

    def _list_tools_once(self, server: str | None = None) -> list[dict[str, Any]]:
        if self.transport_name == "stdio":
            assert self._stdio is not None
            result = self._stdio.request("tools/list", {})
            self._tools = self._extract_tools(result)
        else:
            connection_id = self._resolve_connection(server)
            self._tools = self._smithery_tools(connection_id)
        return self._tools

    def list_tools(self, server: str | None = None) -> list[dict[str, Any]]:
        """Return raw MCP tool definitions for the configured server."""
        if self.transport_name == "smithery" and server and server != self.server:
            self.server = server
            self._initialized = False
        self.initialize()
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                return self._list_tools_once(server)
            except (MCPAuthError, MCPToolError, MCPProtocolError, MCPTimeoutError, MCPError) as exc:
                last_error = exc
                if attempt < self.retries:
                    self.reconnect()
        assert last_error is not None
        raise last_error

    def _assert_tool_allowed(self, name: str, description: str = "") -> None:
        if self._write_markers.search(name) or self._write_markers.search(description):
            if not self.allow_write:
                raise MCPWriteDenied("write-capable MCP tool blocked; set MCP_ALLOW_WRITE=true explicitly")

    def _call_once(self, name: str, params: dict[str, Any], server: str | None = None) -> Any:
        if self.transport_name == "stdio":
            assert self._stdio is not None
            tool = next((item for item in self._tools if item.get("name") == name), {})
            self._assert_tool_allowed(name, str(tool.get("description", "")))
            return self._stdio.request("tools/call", {"name": name, "arguments": params})
        connection_id = self._resolve_connection(server)
        tool = next((item for item in self._tools if item.get("name") == name), {})
        self._assert_tool_allowed(name, str(tool.get("description", "")))
        try:
            command = [
                "tool",
                "call",
                connection_id,
                name,
                json.dumps(params, separators=(",", ":")),
            ]
            namespace = self._smithery_namespace()
            if namespace:
                command.extend(["--namespace", namespace])
            completed = self._run_cli(command, timeout=int(self.timeout))
        except subprocess.TimeoutExpired as exc:
            raise MCPTimeoutError("Smithery tool call timed out") from exc
        except (FileNotFoundError, subprocess.SubprocessError) as exc:
            raise MCPError(self._redact_text(str(exc))) from exc
        if completed.returncode != 0:
            message = self._redact_text(completed.stderr.strip() or "MCP tool invocation failed")
            if "auth" in message.lower() or "unauthorized" in message.lower() or "token" in message.lower():
                raise MCPAuthError("Smithery authentication failed")
            raise MCPToolError(message)
        return self._json_from_output(completed.stdout) or completed.stdout.strip()

    def call_tool(self, name: str, params: dict[str, Any] | str | None = None, server: Any = None) -> Any:
        """Call a read-only MCP tool, or a write tool only with explicit opt-in."""
        legacy_connection: str | None = None
        if isinstance(params, str) and isinstance(server, dict):
            legacy_connection, name, params, server = name, params, server, None
        arguments = params if isinstance(params, dict) else {}
        if legacy_connection:
            server = legacy_connection
        self.list_tools(server if self.transport_name == "smithery" else None)
        tool = next((item for item in self._tools if item.get("name") == name), None)
        if tool is None:
            raise MCPToolError(f"unknown MCP tool: {name}")
        self._assert_tool_allowed(name, str(tool.get("description", "")))
        write = bool(self._write_markers.search(name))
        attempts = 0 if write else self.retries
        last_error: Exception | None = None
        for attempt in range(attempts + 1):
            try:
                return self._call_once(name, arguments, server if self.transport_name == "smithery" else None)
            except (MCPAuthError, MCPWriteDenied, MCPToolError) as exc:
                raise exc
            except (MCPProtocolError, MCPTimeoutError, MCPError) as exc:
                last_error = exc
                if attempt < attempts:
                    self.reconnect()
        assert last_error is not None
        raise last_error

    def reconnect(self) -> dict[str, Any]:
        """Recreate the transport and repeat the handshake."""
        self.close()
        return self.initialize()

    def close(self) -> None:
        """Release child-process resources; Smithery connections remain server-side."""
        if self._stdio:
            self._stdio.close()
        self._initialized = False

    def mcp_list_tools(self, server: str | None = None) -> list[dict[str, Any]]:
        """Return GitAgent-wrapped tools for one or all installed Smithery servers."""
        if self.transport_name == "stdio":
            return self.wrap_tools(self.list_tools())
        selected = [server] if server else list(self.installed_servers)
        wrapped: list[dict[str, Any]] = []
        for connection_id in selected:
            resolved = self._resolve_connection(connection_id)
            tools = self._smithery_tools(resolved)
            info = self.installed_servers.get(resolved, {})
            for tool in tools:
                enriched = dict(tool)
                enriched["_server"] = info.get("name", connection_id)
                enriched["_connection_id"] = resolved
                wrapped.append(self.wrap_tool(enriched))
        return wrapped

    def mcp_uninstall(self, connection_id: str) -> dict[str, str]:
        """Remove a Smithery connection and its local metadata."""
        if connection_id not in self.installed_servers:
            return {"status": "error", "message": f"Server {connection_id} not found"}
        try:
            command = ["mcp", "remove", connection_id]
            namespace = self._smithery_namespace()
            if namespace:
                command.extend(["--namespace", namespace])
            completed = self._run_cli(command, timeout=30)
            error = self._redact_text(completed.stderr.strip()) if completed.returncode else ""
        except (FileNotFoundError, subprocess.SubprocessError) as exc:
            error = self._redact_text(str(exc))
        del self.installed_servers[connection_id]
        self._save_installed()
        message = f"Removed local record: {error}" if error else f"Uninstalled {connection_id}"
        return {"status": "success", "message": message}

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

    def wrap_tools(self, tool_defs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert multiple MCP definitions to GitAgent tool definitions."""
        return [self.wrap_tool(tool_def) for tool_def in tool_defs]

    def get_recommended_servers(self) -> list[dict[str, Any]]:
        """Return discovery targets relevant to AstroFin."""
        return [
            {"name": "financial-data/financial-data", "category": "financial", "description": "Stocks, crypto, forex, fundamentals, filings, macro indicators, and event calendars.", "discovery_query": "financial market data fundamentals SEC macro", "relevance": "high"},
            {"name": "cfocoder/financial-modeling-prep-mcp-server", "category": "financial", "description": "Quotes, statements, ratios, technical indicators, news, SEC filings, earnings, and calendars.", "discovery_query": "financial modeling prep market data", "relevance": "high"},
            {"name": "google/news", "category": "news", "description": "Current and recent news search for sentiment and event monitoring.", "discovery_query": "financial news search", "relevance": "high"},
            {"name": "kwp-lab/rss-reader-mcp", "category": "news", "description": "Read RSS feeds and extract current article content.", "discovery_query": "RSS news feeds", "relevance": "medium"},
            {"name": "crypto", "category": "crypto", "description": "Real-time and historical cryptocurrency market data.", "discovery_query": "crypto market data", "relevance": "high"},
            {"name": "truss44/mcp-crypto-price", "category": "crypto", "description": "Real-time crypto prices and market analysis.", "discovery_query": "crypto price market analysis", "relevance": "high"},
            {"name": "node2flow/bitkub", "category": "crypto", "description": "Crypto exchange ticker, OHLCV, order book, and dry-run order tools.", "discovery_query": "crypto exchange market data", "relevance": "medium"},
            {"name": "googlecalendar", "category": "calendar", "description": "Calendar availability and event-management tools.", "discovery_query": "calendar availability events", "relevance": "medium"},
            {"name": "node2flow/google-calendar", "category": "calendar", "description": "Google Calendar scheduling and availability.", "discovery_query": "Google Calendar MCP", "relevance": "medium"},
            {"name": "github", "category": "development", "description": "Repository, issue, pull-request, and workflow tools.", "discovery_query": "github", "relevance": "high"},
            {"name": "upstash/context7-mcp", "category": "research", "description": "Current documentation and API reference retrieval.", "discovery_query": "documentation search", "relevance": "medium"},
            {"name": "exa", "category": "news", "description": "Web research useful for news and sentiment inputs.", "discovery_query": "web search news", "relevance": "high"},
        ]
