"""
GitAgent CLI Adapter
Command-line interface for exporting and importing agents with MCP tool integration.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .mcp_adapter import MCPAdapter

# =============================================================================
# Agent Export/Import Functions
# =============================================================================


def export_agent(agent_name: str, output_dir: str = "./exported_agents") -> dict[str, Any]:
    """
    Export an agent from AstroFinSentinelV5 to GitAgent format.

    Args:
        agent_name: Name of agent to export (e.g., "TechnicalAgent", "AstroCouncil")
        output_dir: Directory to save exported agent

    Returns:
        Export result with status and file paths
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Import from AstroFinSentinelV5
    try:
        from AstroFinSentinelV5.agents import (
            astro_council_agent,
            bear_researcher,
            bull_researcher,
            fundamental_agent,
            macro_agent,
            quant_agent,
            risk_agent,
            sentiment_agent,
            synthesis_agent,
            technical_agent,
        )

        agent_map = {
            "AstroCouncil": astro_council_agent,
            "FundamentalAgent": fundamental_agent,
            "QuantAgent": quant_agent,
            "MacroAgent": macro_agent,
            "TechnicalAgent": technical_agent,
            "BullBot": bull_researcher,
            "BearBot": bear_researcher,
            "RiskAgent": risk_agent,
            "SentimentAgent": sentiment_agent,
            "SynthesisAgent": synthesis_agent,
        }

        if agent_name not in agent_map:
            return {"status": "error", "message": f"Agent {agent_name} not found"}

        agent_module = agent_map[agent_name]

        # Extract agent definition
        agent_def = {
            "name": agent_name,
            "module": agent_module.__name__,
            "description": getattr(agent_module, "__doc__", ""),
            "tools": getattr(agent_module, "tools", []),
            "instructions": getattr(agent_module, "instructions", ""),
        }

        # Save to file
        output_file = output_path / f"{agent_name.lower()}_agent.json"
        with open(output_file, "w") as f:
            json.dump(agent_def, f, indent=2)

        return {
            "status": "exported",
            "agent": agent_name,
            "file": str(output_file),
        }

    except ImportError as e:
        return {"status": "error", "message": f"Cannot import AstroFinSentinelV5: {e}"}


def import_agent(agent_file: str) -> dict[str, Any]:
    """
    Import an agent from GitAgent format into working memory.

    Args:
        agent_file: Path to agent JSON file

    Returns:
        Import result with agent definition
    """
    try:
        with open(agent_file) as f:
            agent_def = json.load(f)

        return {
            "status": "imported",
            "agent": agent_def.get("name", "unknown"),
            "definition": agent_def,
        }
    except FileNotFoundError:
        return {"status": "error", "message": f"File not found: {agent_file}"}
    except json.JSONDecodeError as e:
        return {"status": "error", "message": f"Invalid JSON: {e}"}


def list_agents() -> list[str]:
    """List all exported agents in the export directory."""
    return [
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
    ]


# =============================================================================
# MCP Integration Commands
# =============================================================================


def mcp_search_cli(query: str, category: str | None = None) -> list[dict[str, Any]]:
    """
    Search Smithery registry for MCP servers.

    Args:
        query: Search query
        category: Optional category filter

    Returns:
        List of matching servers
    """
    adapter = MCPAdapter()
    return adapter.mcp_search(query, category=category)


def mcp_install_cli(server_name: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Install an MCP server from Smithery.

    Args:
        server_name: Server name to install
        config: Optional configuration dict

    Returns:
        Installation result
    """
    adapter = MCPAdapter()
    return adapter.mcp_install(server_name, config=config)


def mcp_list_cli() -> dict[str, Any]:
    """
    List installed MCP servers.

    Returns:
        Dict of installed servers
    """
    adapter = MCPAdapter()
    return adapter.installed_servers


def mcp_tools_cli() -> list[dict[str, Any]]:
    """
    List available tools from installed MCP servers.

    Returns:
        List of tool definitions
    """
    adapter = MCPAdapter()
    return adapter.mcp_list_tools()


# =============================================================================
# Main CLI Entry Point
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="GitAgent CLI - Agent export/import with MCP integration"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Export command
    export_parser = subparsers.add_parser(
        "export-agent", help="Export agent from AstroFinSentinelV5"
    )
    export_parser.add_argument("agent_name", help="Name of agent to export")
    export_parser.add_argument(
        "--output", "-o", default="./exported_agents", help="Output directory"
    )

    # Import command
    import_parser = subparsers.add_parser("import-agent", help="Import agent from file")
    import_parser.add_argument("agent_file", help="Path to agent JSON file")

    # List command
    subparsers.add_parser("list-agents", help="List all available agents")

    # MCP commands
    mcp_search_parser = subparsers.add_parser("mcp-search", help="Search Smithery MCP registry")
    mcp_search_parser.add_argument("query", help="Search query")
    mcp_search_parser.add_argument(
        "--category", "-c", help="Category filter (financial, crypto, news, calendar)"
    )

    mcp_install_parser = subparsers.add_parser(
        "mcp-install", help="Install MCP server from Smithery"
    )
    mcp_install_parser.add_argument("server_name", help="Server name to install")
    mcp_install_parser.add_argument("--config", help="JSON config file")

    mcp_list_parser = subparsers.add_parser("mcp-list", help="List installed MCP servers")

    mcp_tools_parser = subparsers.add_parser("mcp-list-tools", help="List tools from MCP servers")

    mcp_recommend_parser = subparsers.add_parser(
        "mcp-recommended", help="Show recommended MCP servers"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "export-agent":
        result = export_agent(args.agent_name, args.output)
        print(json.dumps(result, indent=2))

    elif args.command == "import-agent":
        result = import_agent(args.agent_file)
        print(json.dumps(result, indent=2))

    elif args.command == "list-agents":
        agents = list_agents()
        print(json.dumps(agents, indent=2))

    elif args.command == "mcp-search":
        result = mcp_search_cli(args.query, args.category)
        print(json.dumps(result, indent=2))

    elif args.command == "mcp-install":
        config = None
        if args.config:
            with open(args.config) as f:
                config = json.load(f)
        result = mcp_install_cli(args.server_name, config=config)
        print(json.dumps(result, indent=2))

    elif args.command == "mcp-list":
        result = mcp_list_cli()
        print(json.dumps(result, indent=2))

    elif args.command == "mcp-list-tools":
        result = mcp_tools_cli()
        print(json.dumps(result, indent=2))

    elif args.command == "mcp-recommended":
        adapter = MCPAdapter()
        result = adapter.get_recommended_servers()
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
