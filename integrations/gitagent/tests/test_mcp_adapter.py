"""Tests for the Smithery MCP adapter and GitAgent CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters.mcp_adapter import MCPAdapter


def test_init_uses_empty_state(tmp_path: Path) -> None:
    adapter = MCPAdapter(storage_path=tmp_path)
    assert adapter.storage_path == tmp_path
    assert adapter.installed_servers == {}


def test_search_normalizes_and_deduplicates(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    adapter = MCPAdapter(storage_path=tmp_path)
    monkeypatch.setattr(
        adapter,
        "_api_search",
        lambda query, page_size: [{"qualifiedName": "a"}, {"name": "a"}, {"name": "b"}],
    )
    assert [item["name"] for item in adapter.mcp_search("finance")] == ["a", "b"]


def test_search_cli_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    adapter = MCPAdapter(storage_path=tmp_path)
    monkeypatch.setattr(
        adapter, "_api_search", lambda query, page_size: (_ for _ in ()).throw(OSError("offline"))
    )
    monkeypatch.setattr(
        adapter,
        "_run_cli",
        lambda args, timeout=None: {"ok": True, "payload": {"servers": [{"name": "github"}]}},
    )
    assert adapter.mcp_search("github")[0]["name"] == "github"


def test_wrap_tool() -> None:
    wrapped = MCPAdapter().wrap_tool(
        {"name": "search", "description": "Search", "inputSchema": {"type": "object"}},
        "github",
        "github",
    )
    assert wrapped["name"] == "search"
    assert wrapped["input_schema"] == {"type": "object"}
    assert wrapped["server"] == "github"
    assert wrapped["protocol"] == "mcp"


def test_install_persists_connection(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    adapter = MCPAdapter(storage_path=tmp_path)
    monkeypatch.setattr(adapter, "_run_cli", lambda args, timeout=None: {"ok": True, "payload": {}})
    result = adapter.mcp_install("owner/server", {"token": "configured"})
    assert result["status"] == "installed"
    assert "owner-server" in adapter.installed_servers
    assert json.loads((tmp_path / "installed_servers.json").read_text())


def test_list_tools_wraps_cli_tools(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    adapter = MCPAdapter(storage_path=tmp_path)
    adapter.installed_servers = {"github": {"name": "owner/github"}}
    monkeypatch.setattr(
        adapter,
        "_run_cli",
        lambda args, timeout=None: {"ok": True, "payload": {"tools": [{"name": "issues"}]}},
    )
    tools = adapter.mcp_list_tools()
    assert tools[0]["name"] == "issues"
    assert tools[0]["connection_id"] == "github"


def test_recommended_servers_cover_required_capabilities() -> None:
    capabilities = {item["capability"] for item in MCPAdapter.get_recommended_servers()}
    assert {
        "market-data",
        "crypto-market-data",
        "financial-news",
        "economic-calendar",
        "github-operations",
    } <= capabilities


def test_api_payload_without_names_uses_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    adapter = MCPAdapter(storage_path=tmp_path)
    monkeypatch.setattr(adapter, "_api_search", lambda query, page_size: [{}])
    results = adapter.mcp_search("crypto")
    assert results
    assert all(item["name"] for item in results)


def test_export_import_round_trip_all_supported_agents(tmp_path: Path) -> None:
    env = {**__import__("os").environ, "PYTHONPATH": str(Path(__file__).parents[3])}
    for name in [
        "AstroCouncil",
        "FundamentalAgent",
        "QuantAgent",
        "MacroAgent",
        "TechnicalAgent",
        "BullBot",
        "BearBot",
        "RiskAgent",
        "SentimentAgent",
        "SynthesisAgent",
    ]:
        exported = subprocess.run(
            [
                "python",
                "-m",
                "integrations.gitagent.adapters.cli",
                "export-agent",
                name,
                "--output",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        payload = json.loads(exported.stdout)
        assert exported.returncode == 0
        assert payload["status"] == "exported"
        imported = subprocess.run(
            [
                "python",
                "-m",
                "integrations.gitagent.adapters.cli",
                "import-agent",
                payload["file"],
            ],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert json.loads(imported.stdout)["status"] == "imported"


def test_cli_list_agents_and_mcp_list(tmp_path: Path) -> None:
    env = {**__import__("os").environ, "PYTHONPATH": str(Path(__file__).parents[3])}
    result = subprocess.run(
        ["python", "-m", "integrations.gitagent.adapters.cli", "list-agents"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0
    assert "TechnicalAgent" in json.loads(result.stdout)
    result = subprocess.run(
        ["python", "-m", "integrations.gitagent.adapters.cli", "mcp-list"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0
    assert isinstance(json.loads(result.stdout), dict)
