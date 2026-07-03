"""Tests for MCP Adapter"""

from __future__ import annotations
import json
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters.mcp_adapter import MCPAdapter


class TestMCPAdapter:
    """Test suite for MCPAdapter."""


    def test_init(self, tmp_path):
        """Test adapter initialization."""
        adapter = MCPAdapter(storage_path=str(tmp_path))
        assert adapter.storage_path == tmp_path
        assert isinstance(adapter.installed_servers, dict)

    def test_search_returns_results(self):
        """Test that search returns actual MCP servers."""
        adapter = MCPAdapter()
        results = adapter.mcp_search("github")
        assert isinstance(results, list)
        assert len(results) > 0
        # Check first result has expected fields
        if isinstance(results[0], dict):
            assert "name" in results[0] or "qualifiedName" in results[0]

    def test_search_with_category(self):
        """Test search with category filter."""
        adapter = MCPAdapter()
        results = adapter.mcp_search("finance", category="financial")
        assert isinstance(results, list)

    def test_fallback_servers(self):
        """Test fallback server database."""
        adapter = MCPAdapter()
        fallback = adapter._get_fallback_servers("github")
        assert len(fallback) > 0
        assert fallback[0]["name"] == "@smithery/github"

    def test_wrap_tool(self):
        """Test tool wrapping."""
        adapter = MCPAdapter()
        tool_def = {
            "name": "test_tool",
            "description": "A test tool",
            "inputSchema": {"type": "object"}
        }
        wrapped = adapter.wrap_tool(tool_def)
        assert wrapped["name"] == "test_tool"
        assert wrapped["description"] == "A test tool"
        assert wrapped["server"] == "unknown"
        assert "original_def" in wrapped

    def test_install_returns_pending(self):
        """Test install returns proper structure."""
        adapter = MCPAdapter()
        # This will fail due to no auth, but should return proper structure
        result = adapter.mcp_install("@smithery/filesystem")
        assert "status" in result
        assert result["status"] in ["pending", "installed", "failed", "timeout"]
        assert "name" in result

    def test_list_tools_empty(self):
        """Test list tools with no installed servers."""
        adapter = MCPAdapter(storage_path="/tmp/nonexistent")
        tools = adapter.mcp_list_tools()
        assert tools == []

    def test_recommended_servers(self):
        """Test recommended servers list."""
        adapter = MCPAdapter()
        servers = adapter.get_recommended_servers()
        assert len(servers) >= 10
        assert all("name" in s for s in servers)
        assert all("description" in s for s in servers)

    def test_search_deduplication(self):
        """Test that search results are deduplicated."""
        adapter = MCPAdapter()
        results = adapter.mcp_search("github")
        names = []
        for r in results:
            if isinstance(r, dict):
                name = r.get("name", r.get("qualifiedName", ""))
                names.append(name)
        assert len(names) == len(set(names)), "Duplicate server names found"


class TestCLICommands:
    """Test CLI command execution."""

    def test_list_agents_command(self):
        """Test list-agents CLI command."""
        import subprocess
        result = subprocess.run(
            ["python", "-m", "adapters.cli", "list-agents"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0
        agents = json.loads(result.stdout)
        assert "AstroCouncil" in agents
        assert "TechnicalAgent" in agents

    def test_mcp_recommended_command(self):
        """Test mcp-recommended CLI command."""
        import subprocess
        result = subprocess.run(
            ["python", "-m", "adapters.cli", "mcp-recommended"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0
        servers = json.loads(result.stdout)
        assert len(servers) >= 10

    def test_mcp_search_command(self):
        """Test mcp-search CLI command."""
        import subprocess
        result = subprocess.run(
            ["python", "-m", "adapters.cli", "mcp-search", "github"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0
        results = json.loads(result.stdout)
        assert isinstance(results, list)
        assert len(results) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
