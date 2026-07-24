"""
GitAgent CLI Adapter
Command-line interface for exporting and importing agents with MCP tool integration.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .mcp_adapter import MCPAdapter


def _emit_json(value: Any) -> None:
    """Write machine-readable CLI output to stdout."""
    sys.stdout.write(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


# =============================================================================
# Agent Export/Import Functions
# =============================================================================


def export_agent(agent_name: str, output_dir: str = "./exported_agents") -> dict[str, Any]:
    """Export a canonical AstroFin agent as a portable GitAgent manifest."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    agent_map = {
        "AstroCouncil": ("agents._impl.astro_council.agent", "AstroCouncilAgent"),
        "FundamentalAgent": ("agents._impl.fundamental_agent", "FundamentalAgent"),
        "QuantAgent": ("agents._impl.quant_agent", "QuantAgent"),
        "MacroAgent": ("agents._impl.macro_agent", "MacroAgent"),
        "TechnicalAgent": ("agents._impl.technical_agent", "TechnicalAgent"),
        "BullBot": ("agents._impl.bull_researcher", "BullResearcherAgent"),
        "BearBot": ("agents._impl.bear_researcher", "BearResearcherAgent"),
        "RiskAgent": ("agents._impl.risk_agent", "RiskAgent"),
        "SentimentAgent": ("agents._impl.sentiment_agent", "SentimentAgent"),
        "SynthesisAgent": ("agents._impl.synthesis_agent", "SynthesisAgent"),
    }
    if agent_name not in agent_map:
        return {"status": "error", "message": f"Agent {agent_name} not found"}

    module_name, class_name = agent_map[agent_name]
    try:
        module = __import__(module_name, fromlist=[class_name])
        agent_class = getattr(module, class_name)
        agent = agent_class()
    except (ImportError, AttributeError, TypeError) as exc:
        return {"status": "error", "message": f"Cannot load {agent_name}: {exc}"}

    agent_def = {
        "name": agent_name,
        "module": module_name,
        "class": class_name,
        "description": (agent_class.__doc__ or module.__doc__ or "").strip(),
        "domain": getattr(agent, "domain", "unknown"),
        "weight": getattr(agent, "weight", 0.0),
        "tools": getattr(module, "tools", []),
        "instructions": getattr(module, "instructions", ""),
        "source": "agents/_impl",
    }
    output_file = output_path / f"{agent_name.lower()}_agent.json"
    output_file.write_text(json.dumps(agent_def, indent=2, ensure_ascii=False) + "\n")
    return {"status": "exported", "agent": agent_name, "file": str(output_file)}


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
    """Return installed Smithery MCP connections."""
    return MCPAdapter().installed_servers


def mcp_tools_cli() -> list[dict[str, Any]]:
    """Return tools exposed by installed Smithery MCP connections."""
    return MCPAdapter().mcp_list_tools()


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
        "mcp-install", help="Connect MCP server through Smithery"
    )
    mcp_install_parser.add_argument("server_name", help="Smithery qualified server name")
    mcp_install_parser.add_argument("--config", help="JSON config file")

    subparsers.add_parser("mcp-list", help="List installed Smithery MCP connections")
    subparsers.add_parser("mcp-list-tools", help="List tools from MCP connections")

    mcp_call_parser = subparsers.add_parser("mcp-call", help="Call a connected MCP tool")
    mcp_call_parser.add_argument("connection_id")
    mcp_call_parser.add_argument("tool_name")
    mcp_call_parser.add_argument("--arguments", default="{}", help="Tool arguments as JSON")

    subparsers.add_parser("mcp-recommended", help="Show recommended MCP servers")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "export-agent":
        result = export_agent(args.agent_name, args.output)
        _emit_json(result)

    elif args.command == "import-agent":
        result = import_agent(args.agent_file)
        _emit_json(result)

    elif args.command == "list-agents":
        agents = list_agents()
        _emit_json(agents)

    elif args.command == "mcp-search":
        result = mcp_search_cli(args.query, args.category)
        _emit_json(result)

    elif args.command == "mcp-install":
        config = None
        if args.config:
            with open(args.config) as f:
                config = json.load(f)
        result = mcp_install_cli(args.server_name, config=config)
        _emit_json(result)

    elif args.command == "mcp-list":
        _emit_json(mcp_list_cli())

    elif args.command == "mcp-list-tools":
        _emit_json(mcp_tools_cli())

    elif args.command == "mcp-call":
        arguments = json.loads(args.arguments)
        result = MCPAdapter().call_tool(args.connection_id, args.tool_name, arguments)
        _emit_json(result)

    elif args.command == "mcp-recommended":
        _emit_json(MCPAdapter().get_recommended_servers())


if __name__ == "__main__":
    main()
