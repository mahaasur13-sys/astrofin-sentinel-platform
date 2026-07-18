"""GitAgent CLI for agent export/import and Smithery MCP connections."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .mcp_adapter import MCPAdapter

AGENT_NAMES = [
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

AGENT_KEYS = {
    "AstroCouncil": "astrocouncilagent",
    "FundamentalAgent": "fundamentalagent",
    "QuantAgent": "quantagent",
    "MacroAgent": "macroagent",
    "TechnicalAgent": "technical_agent",
    "BullBot": "bull_researcher",
    "BearBot": "bear_researcher",
    "RiskAgent": "risk_agent",
    "SentimentAgent": "sentiment_agent",
    "SynthesisAgent": "synthesisagent",
}


def export_agent(agent_name: str, output_dir: str = "./exported_agents") -> dict[str, Any]:
    """Export a registered agent definition to GitAgent JSON."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    try:
        from agents.gitagent_exporter import AGENTS

        key = AGENT_KEYS.get(agent_name, agent_name)
        definition = AGENTS.get(key)
        if definition is None:
            return {"status": "error", "message": f"Agent {agent_name} not found"}
        data = {
            "name": agent_name,
            "module": "agents._impl",
            "description": definition.get("description", ""),
            "tools": definition.get("capabilities", []),
            "instructions": definition.get("description", ""),
            "weight": definition.get("weight", 0.0),
            "domain": definition.get("domain", "unknown"),
        }
    except ImportError as exc:
        return {"status": "error", "message": f"Cannot import agent registry: {exc}"}
    output_file = output_path / f"{agent_name.lower()}_agent.json"
    output_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return {"status": "exported", "agent": agent_name, "file": str(output_file)}


def import_agent(agent_file: str) -> dict[str, Any]:
    """Load and validate a GitAgent JSON definition."""
    try:
        definition = json.loads(Path(agent_file).read_text())
    except FileNotFoundError:
        return {"status": "error", "message": f"File not found: {agent_file}"}
    except json.JSONDecodeError as exc:
        return {"status": "error", "message": f"Invalid JSON: {exc}"}
    return {
        "status": "imported",
        "agent": definition.get("name", "unknown"),
        "definition": definition,
    }


def list_agents() -> list[str]:
    """List all agents exported by this integration."""
    return AGENT_NAMES.copy()


def main() -> None:
    parser = argparse.ArgumentParser(description="GitAgent CLI")
    subparsers = parser.add_subparsers(dest="command")

    export_parser = subparsers.add_parser("export-agent")
    export_parser.add_argument("agent_name")
    export_parser.add_argument("--output", "-o", default="./exported_agents")
    import_parser = subparsers.add_parser("import-agent")
    import_parser.add_argument("agent_file")
    subparsers.add_parser("list-agents")

    search_parser = subparsers.add_parser("mcp-search", aliases=["mcp_search"])
    search_parser.add_argument("query")
    search_parser.add_argument("--category", "-c")
    install_parser = subparsers.add_parser("mcp-install", aliases=["mcp_install"])
    install_parser.add_argument("server_name")
    install_parser.add_argument("--config")
    subparsers.add_parser("mcp-list", aliases=["mcp_list"])
    subparsers.add_parser("mcp-list-tools", aliases=["mcp_list_tools"])
    subparsers.add_parser("mcp-recommended")

    args = parser.parse_args()
    if args.command == "export-agent":
        output = export_agent(args.agent_name, args.output)
    elif args.command == "import-agent":
        output = import_agent(args.agent_file)
    elif args.command == "list-agents":
        output = list_agents()
    elif args.command in {"mcp-search", "mcp_search"}:
        output = MCPAdapter().mcp_search(args.query, category=args.category)
    elif args.command in {"mcp-install", "mcp_install"}:
        config = json.loads(Path(args.config).read_text()) if args.config else None
        output = MCPAdapter().mcp_install(args.server_name, config=config)
    elif args.command in {"mcp-list", "mcp_list"}:
        output = MCPAdapter().installed_servers
    elif args.command in {"mcp-list-tools", "mcp_list_tools"}:
        output = MCPAdapter().mcp_list_tools()
    elif args.command == "mcp-recommended":
        output = MCPAdapter.get_recommended_servers()
    else:
        parser.print_help()
        return
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
