"""Unit, transport, policy, and optional live tests for MCPAdapter."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters.mcp_adapter import (  # noqa: E402
    MCPAdapter,
    MCPAuthError,
    MCPProtocolError,
    MCPTimeoutError,
    MCPWriteDenied,
)

FAKE_SERVER = r'''
import json
import sys

for line in sys.stdin:
    request = json.loads(line)
    method = request.get("method")
    request_id = request.get("id")
    if method == "initialize":
        result = {"protocolVersion": "2024-11-05", "capabilities": {}, "serverInfo": {"name": "fake"}}
    elif method == "notifications/initialized":
        continue
    elif method == "tools/list":
        result = {"tools": [
            {"name": "search_repositories", "description": "Read-only repository search", "inputSchema": {"type": "object"}},
            {"name": "create_issue", "description": "Create a GitHub issue", "inputSchema": {"type": "object"}},
        ]}
    elif method == "tools/call":
        if request["params"]["name"] == "search_repositories":
            result = {"content": [{"type": "text", "text": json.dumps({"total_count": 1})}]}
        else:
            result = {"content": [{"type": "text", "text": "write"}]}
    else:
        result = {}
    if request_id is not None:
        print(json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result}), flush=True)
'''


def fake_command(tmp_path: Path) -> list[str]:
    script = tmp_path / "fake_mcp.py"
    script.write_text(FAKE_SERVER)
    return [sys.executable, str(script)]


class TestMCPAdapter:
    def test_init(self, tmp_path):
        adapter = MCPAdapter(storage_path=tmp_path)
        assert adapter.storage_path == tmp_path
        assert adapter.installed_servers == {}

    def test_search_returns_results(self):
        results = MCPAdapter().mcp_search("github")
        assert results and all("qualifiedName" in item for item in results)

    @pytest.mark.parametrize("category,query", [("financial", "financial data"), ("crypto", "crypto market data"), ("news", "news"), ("calendar", "calendar")])
    def test_search_categories(self, category, query):
        results = MCPAdapter().mcp_search(query, category=category)
        assert results
        assert all(MCPAdapter._category_match(item, category) for item in results)

    def test_fallback_servers(self):
        assert MCPAdapter()._get_fallback_servers("github")[0]["name"] == "@smithery/github"

    def test_wrap_tool(self):
        wrapped = MCPAdapter().wrap_tool({"name": "test_tool", "description": "A test tool", "inputSchema": {"type": "object"}})
        assert wrapped["name"] == "test_tool"
        assert wrapped["input_schema"] == {"type": "object"}
        assert wrapped["server"] == "unknown"

    def test_wrap_tools(self):
        assert [x["name"] for x in MCPAdapter().wrap_tools([{"name": "one"}, {"name": "two"}])] == ["one", "two"]

    def test_stdio_handshake_list_and_readonly_call(self, tmp_path):
        adapter = MCPAdapter.from_stdio(fake_command(tmp_path), timeout=3, retries=0)
        try:
            initialized = adapter.initialize()
            assert initialized["protocolVersion"] == "2024-11-05"
            assert [x["name"] for x in adapter.list_tools()] == ["search_repositories", "create_issue"]
            result = adapter.call_tool("search_repositories", {"q": "astrofin"})
            assert result["content"]
        finally:
            adapter.close()

    def test_stdio_write_denied_by_default(self, tmp_path, monkeypatch):
        monkeypatch.delenv("MCP_ALLOW_WRITE", raising=False)
        adapter = MCPAdapter.from_stdio(fake_command(tmp_path), timeout=3, retries=0)
        try:
            with pytest.raises(MCPWriteDenied):
                adapter.call_tool("create_issue", {"title": "blocked"})
        finally:
            adapter.close()

    def test_stdio_write_allowed_explicitly(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MCP_ALLOW_WRITE", "true")
        adapter = MCPAdapter.from_stdio(fake_command(tmp_path), timeout=3, retries=0)
        try:
            assert adapter.call_tool("create_issue", {})["content"]
        finally:
            adapter.close()

    def test_reconnect_after_close(self, tmp_path):
        adapter = MCPAdapter.from_stdio(fake_command(tmp_path), timeout=3, retries=0)
        adapter.initialize()
        adapter.close()
        assert adapter.reconnect()["protocolVersion"] == "2024-11-05"
        adapter.close()

    def test_invalid_stdio_response_is_protocol_error(self, tmp_path):
        script = tmp_path / "bad.py"
        script.write_text("import sys; print('not-json', flush=True); sys.stdin.readline()")
        adapter = MCPAdapter.from_stdio([sys.executable, str(script)], timeout=1, retries=0)
        try:
            with pytest.raises(MCPProtocolError):
                adapter.initialize()
        finally:
            adapter.close()

    def test_timeout_is_classified(self, tmp_path):
        script = tmp_path / "slow.py"
        script.write_text("import sys; sys.stdin.readline()")
        adapter = MCPAdapter.from_stdio([sys.executable, str(script)], timeout=0.2, retries=0)
        try:
            with pytest.raises(MCPTimeoutError):
                adapter.initialize()
        finally:
            adapter.close()

    def test_redacts_credentials_before_persisting(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SMITHERY_API_KEY", "secret-api-key")
        adapter = MCPAdapter(storage_path=tmp_path)
        monkeypatch.setattr(adapter, "_run_cli", lambda *args, **kwargs: subprocess.CompletedProcess(args=[], returncode=0, stdout="{}", stderr=""))
        result = adapter.mcp_install("example/server", {"api_key": "secret", "nested": {"token": "secret-token"}})
        assert result["status"] == "installed"
        persisted = json.loads((tmp_path / "installed_servers.json").read_text())
        assert "secret" not in json.dumps(persisted)
        assert "[REDACTED]" in json.dumps(persisted)

    def test_install_uses_no_secret_argv(self, tmp_path, monkeypatch):
        adapter = MCPAdapter(storage_path=tmp_path)
        monkeypatch.setenv("SMITHERY_API_KEY", "secret")
        seen = {}
        def fake_run(arguments, timeout=60):
            seen["arguments"] = arguments
            return subprocess.CompletedProcess(arguments, 0, "{}", "")
        monkeypatch.setattr(adapter, "_run_cli", fake_run)
        adapter.mcp_install("example/server")
        assert "secret" not in json.dumps(seen["arguments"])

    def test_mcp_list_tools_empty(self, tmp_path):
        assert MCPAdapter(storage_path=tmp_path).mcp_list_tools() == []

    def test_round_trip_install_list_wrap(self, tmp_path, monkeypatch):
        adapter = MCPAdapter(storage_path=tmp_path)
        tools = [{"name": "get_quote", "description": "read", "inputSchema": {"type": "object"}}, {"name": "get_news", "description": "read", "inputSchema": {"type": "object"}}, {"name": "get_calendar", "description": "read", "inputSchema": {"type": "object"}}]
        def fake_run(arguments, timeout=60):
            if arguments[:2] == ["mcp", "add"]:
                return subprocess.CompletedProcess(arguments, 0, "{}", "")
            raise AssertionError(arguments)
        monkeypatch.setattr(adapter, "_run_cli", fake_run)
        installed = adapter.mcp_install("astrofin/market-data")
        adapter.installed_servers[installed["connection_id"]]["tools"] = tools
        assert [x["name"] for x in adapter.mcp_list_tools()] == ["get_quote", "get_news", "get_calendar"]

    def test_recommended_servers(self):
        servers = MCPAdapter().get_recommended_servers()
        assert len(servers) >= 10
        assert {"financial", "crypto", "news", "calendar"}.issubset({x["category"] for x in servers})

    def test_search_deduplication(self):
        results = MCPAdapter().mcp_search("github")
        names = [x["qualifiedName"] for x in results]
        assert len(names) == len(set(names))


@pytest.mark.slow
@pytest.mark.skipif(os.environ.get("GITAGENT_MCP_LIVE") != "1", reason="Set GITAGENT_MCP_LIVE=1 for live MCP tests")
def test_real_github_mcp_readonly_call():
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not token:
        pytest.skip("GITHUB_PERSONAL_ACCESS_TOKEN is not configured in the protected secret store")
    adapter = MCPAdapter.from_stdio(["github-mcp-server", "stdio"], env={"GITHUB_PERSONAL_ACCESS_TOKEN": token}, timeout=30, retries=1)
    try:
        tools = adapter.list_tools()
        assert any(item.get("name") == "search_repositories" for item in tools)
        result = adapter.call_tool("search_repositories", {"query": "repo:mahaasur13-sys/astrofin-sentinel-platform"})
        assert result is not None
    finally:
        adapter.close()


class TestCLICommands:
    def _run(self, *args):
        return subprocess.run([sys.executable, "-m", "adapters.cli", *args], capture_output=True, text=True, cwd=Path(__file__).parent.parent)

    def test_list_agents_command(self):
        result = self._run("list-agents")
        assert result.returncode == 0
        assert "SynthesisAgent" in json.loads(result.stdout)

    def test_mcp_recommended_command(self):
        result = self._run("mcp-recommended")
        assert result.returncode == 0
        assert len(json.loads(result.stdout)) >= 10

    def test_mcp_search_command(self):
        result = self._run("mcp-search", "github")
        assert result.returncode == 0
        assert json.loads(result.stdout)
