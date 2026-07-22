# GitAgent Integration

Agent export/import system for AstroFinSentinelV5 with Smithery MCP tool integration.

## Overview

GitAgent provides:

- Portable JSON manifests for canonical AstroFin agents.
- Smithery registry search, MCP connection management, tool discovery, and tool calls.
- A GitAgent-compatible tool shape for MCP definitions.
- A documented LangGraph/n8n dashboard recommendation.

## Architecture

```text
integrations/gitagent/
├── adapters/
│   ├── cli.py           # Agent export/import and MCP commands
│   └── mcp_adapter.py   # Smithery CLI/API adapter
├── docs/
│   └── dashboard-evaluation.md
├── exported_agents/     # Portable JSON manifests
├── tests/
└── README.md
```

## Exported agents

The repository contains 10 exported manifests:

- AstroCouncil
- FundamentalAgent
- QuantAgent
- MacroAgent
- TechnicalAgent
- BullBot
- BearBot
- RiskAgent
- SentimentAgent
- SynthesisAgent

The CLI exports from the canonical `agents/_impl/` modules and records the module, class, domain, weight, description, and source path. `BullBot` and `BearBot` are GitAgent aliases for `BullResearcherAgent` and `BearResearcherAgent`.

```bash
python -m integrations.gitagent.adapters.cli list-agents
python -m integrations.gitagent.adapters.cli export-agent TechnicalAgent --output ./exported_agents
python -m integrations.gitagent.adapters.cli import-agent ./exported_agents/technicalagent_agent.json
```

## MCP Adapter

`MCPAdapter` uses the Smithery CLI when available and the public Smithery registry API for discovery. Search is read-only and works without credentials. Connecting a hosted server or calling its tools may require Smithery authentication, a namespace, OAuth, or server-specific configuration.

Smithery's current CLI flow is:

```text
smithery mcp search <term>
smithery mcp add <qualified-server-name> --id <connection-id>
smithery tool list <connection-id> --flat
smithery tool call <connection-id> <tool-name> '{"key":"value"}'
```

The adapter exposes:

```python
from integrations.gitagent.adapters.mcp_adapter import MCPAdapter

adapter = MCPAdapter()
servers = adapter.mcp_search("financial data", category="financial")
connection = adapter.mcp_install("financial-data/financial-data")
tools = adapter.mcp_list_tools()
wrapped = adapter.wrap_tool(tools[0]) if tools else None
```

`mcp_install()` creates a Smithery connection and persists the local connection record in `~/.gitagent/mcp/installed_servers.json`. It does not silently install an unaudited package into the AstroFin runtime. `mcp_list_tools()` discovers tools through the Smithery CLI/API, and `call_tool()` invokes a connected tool. The adapter preserves the original MCP definition in `original_def` and maps `inputSchema`/`outputSchema` to `input_schema`/`output_schema`.

### Relevant Smithery servers

These are discovery targets, not hard-coded data dependencies. Verify uptime, permissions, licensing, rate limits, and data provenance before production use.

| Qualified name | Category | AstroFin use |
|---|---|---|
| `financial-data/financial-data` | Financial | Market data, fundamentals, filings, macro indicators, and event calendars |
| `cfocoder/financial-modeling-prep-mcp-server` | Financial | Quotes, statements, ratios, technical indicators, news, SEC filings, earnings, and calendars |
| `crypto` | Crypto | Real-time and historical cryptocurrency market data |
| `truss44/mcp-crypto-price` | Crypto | Crypto prices and market analysis |
| `google/news` | News | Current and recent news for SentimentAgent |
| `kwp-lab/rss-reader-mcp` | News | RSS ingestion and article extraction |
| `googlecalendar` | Calendar | Availability and event management for scheduled workflows |
| `github` | Development | Repository, issue, pull-request, and workflow operations |

### CLI commands

Run commands from the repository root:

```bash
python -m integrations.gitagent.adapters.cli mcp-search "financial data" --category financial
python -m integrations.gitagent.adapters.cli mcp-search "crypto market data" --category crypto
python -m integrations.gitagent.adapters.cli mcp-install financial-data/financial-data
python -m integrations.gitagent.adapters.cli mcp-list
python -m integrations.gitagent.adapters.cli mcp-list-tools
python -m integrations.gitagent.adapters.cli mcp-call <connection-id> <tool-name> --arguments '{"symbol":"BTCUSDT"}'
python -m integrations.gitagent.adapters.cli mcp-recommended
```

For an authenticated Smithery namespace, set `SMITHERY_API_KEY` and `SMITHERY_NAMESPACE` in the runtime environment. Never commit either value. Server-specific secrets belong in the project's secret manager or environment, not in manifests or source code.

## Dashboard evaluation

See [`docs/dashboard-evaluation.md`](docs/dashboard-evaluation.md). The recommendation is **LangGraph for in-process agent orchestration and state, with n8n only at the ingestion/event boundary where its connectors add value**.

## Testing

```bash
ruff check integrations/gitagent
python -m pytest integrations/gitagent/tests -q --no-cov
```

The full repository test command also applies the repository-wide coverage gate and may fail independently of GitAgent tests when the global test configuration collects no coverage data.

## Status

- [x] Smithery search via CLI and public registry API.
- [x] Smithery connection/install command.
- [x] MCP tool listing, invocation, and GitAgent wrapping.
- [x] CLI commands: `mcp-search`, `mcp-install`, `mcp-list`, `mcp-list-tools`, and `mcp-call`.
- [x] Dashboard evaluation with hybrid recommendation.
- [x] 10-agent export/import round-trip.

## References

- [Smithery documentation](https://smithery.ai/docs)
- [Smithery CLI](https://smithery.ai/docs/concepts/cli)
- [Smithery server search](https://smithery.ai/servers)
- [Model Context Protocol](https://modelcontextprotocol.io)
