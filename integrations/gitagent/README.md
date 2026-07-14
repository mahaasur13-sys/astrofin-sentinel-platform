# GitAgent Integration

Agent export/import system for AstroFinSentinelV5 with MCP (Model Context Protocol) tool integration.

## Overview

GitAgent enables:
- **Agent Export/Import**: Export specialized agents from AstroFinSentinelV5 as portable JSON definitions
- **MCP Tool Integration**: Connect to Smithery MCP registry for dynamic tool discovery and installation
- **Multi-Agent Orchestration**: Support for complex agent workflows with state management

## Architecture

```
integrations/gitagent/
├── adapters/
│   ├── cli.py           # CLI for agent and MCP management
│   └── mcp_adapter.py   # Smithery MCP registry adapter
├── docs/
│   └── dashboard-evaluation.md
├── tests/
└── README.md
```

## Agents

### Exported Agents (Phase 1)
- [x] AstroCouncil - Master orchestration agent
- [x] FundamentalAgent - Fundamental market analysis
- [x] QuantAgent - Quantitative analysis
- [x] MacroAgent - Macroeconomic analysis

### Exported Agents (Phase 2)
- [x] TechnicalAgent - Technical chart analysis
- [x] BullBot - Bullish market researcher
- [x] BearBot - Bearish market researcher
- [x] RiskAgent - Risk assessment and management
- [x] SentimentAgent - Market sentiment analysis
- [x] SynthesisAgent - Multi-source synthesis

## MCP Integration

### Smithery MCP Registry

The adapter connects to [Smithery.ai](https://smithery.ai) MCP registry for dynamic tool discovery.

#### Recommended MCP Servers for AstroFinSentinelV5

| Server | Category | Description |
|--------|----------|-------------|
| `@smithery/github` | development | GitHub API integration |
| `@modelcontextprotocol/server-brave-search` | search | Web search capabilities |
| `yahoo-finance-mcp` | financial | Yahoo Finance data (stocks, crypto, options) |
| `coinmarketcap-mcp` | crypto | Cryptocurrency price data |
| `newsapi-mcp` | news | Financial news aggregation |
| `@modelcontextprotocol/server-postgres` | database | PostgreSQL database access |
| `@modelcontextprotocol/server-slack` | communication | Slack messaging |
| `google-calendar-mcp` | calendar | Google Calendar integration |

### CLI Commands

```bash
# Search for MCP servers
python -m adapters.cli mcp-search "github" --category development

# Install MCP server
python -m adapters.cli mcp-install "@smithery/github"

# List installed servers
python -m adapters.cli mcp-list

# List available tools
python -m adapters.cli mcp-list-tools

# Show recommended servers
python -m adapters.cli mcp-recommended
```

### MCP Adapter API

```python
from adapters.mcp_adapter import MCPAdapter

adapter = MCPAdapter()

# Search for servers
results = adapter.mcp_search("finance", category="financial")

# Install a server
result = adapter.mcp_install("yahoo-finance-mcp", config={"api_key": "..."})

# List available tools
tools = adapter.mcp_list_tools()

# Wrap MCP tool as GitAgent-compatible
wrapped = adapter.wrap_tool(tool_def)
```

## Agent Export/Import

```bash
# Export an agent
python -m adapters.cli export-agent TechnicalAgent --output ./exported_agents

# Import an agent
python -m adapters.cli import-agent ./exported_agents/technicalagent_agent.json

# List all agents
python -m adapters.cli list-agents
```

## Dashboard Evaluation

See [dashboard-evaluation.md](docs/dashboard-evaluation.md) for LangGraph vs n8n analysis and recommendations.

## Installation

```bash
# Install dependencies
pip install httpx

# Install Smithery CLI (optional, for full MCP support)
npm install -g @smithery/cli
```

## Testing

```bash
# Run MCP adapter tests
python -m pytest tests/ -v

# Test round-trip: search → install → wrap → use
python -m adapters.cli mcp-search "filesystem" | \
python -m adapters.cli mcp-install "@smithery/filesystem" && \
python -m adapters.cli mcp-list-tools
```

## Configuration

MCP adapter stores data in:
- `~/.gitagent/mcp/installed_servers.json` - Installed server registry
- `~/.gitagent/mcp/servers/` - Server installations

## Status

- [x] Phase 1: Core agent export (AstroCouncil, FundamentalAgent, QuantAgent, MacroAgent)
- [x] Phase 2: MCP Adapter for Smithery/GitHub tools ✅
- [x] Dashboard evaluation ✅ (see `docs/dashboard-evaluation.md`)
- [x] Phase 3: Export remaining agents ✅ (all 9+ agents exported and tested)

## References

- [Smithery.ai](https://smithery.ai) - MCP Registry
- [Model Context Protocol](https://modelcontextprotocol.io) - MCP Specification
- [LangGraph](https://langchain.com/langgraph/) - Agent Orchestration
