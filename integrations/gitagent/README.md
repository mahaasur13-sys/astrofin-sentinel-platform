# GitAgent Integration

GitAgent provides portable agent definitions and a Smithery MCP bridge for AstroFin Sentinel V5.

## Components

- `adapters/cli.py` — export/import and MCP commands.
- `adapters/mcp_adapter.py` — Smithery registry search, connection management, tool discovery, schema wrapping, and tool calls.
- `exported_agents/` — ten portable definitions: AstroCouncil, FundamentalAgent, QuantAgent, MacroAgent, TechnicalAgent, BullBot, BearBot, RiskAgent, SentimentAgent, and SynthesisAgent.
- `docs/dashboard-evaluation.md` — LangGraph/n8n architecture decision.

## MCP Adapter

Smithery's current documented workflow is **search → connect (`mcp add`) → list tools → call tool**. The adapter uses the Smithery REST registry endpoint (`https://api.smithery.ai/servers`) for discovery, then falls back to the `smithery` CLI when the API is unavailable. Configure `SMITHERY_API_KEY` when the registry requires authentication. The adapter stores only connection metadata under `~/.gitagent/mcp/`; it does not execute arbitrary server code in the AstroFin process.

```python
from integrations.gitagent.adapters.mcp_adapter import MCPAdapter

adapter = MCPAdapter()
servers = adapter.mcp_search("financial crypto market data")
connection = adapter.mcp_install("owner/server", config={"api_key": "configured-outside-source"})
tools = adapter.mcp_list_tools()
wrapped = adapter.wrap_tool(tools[0])
result = adapter.call_tool(connection["connection_id"], wrapped["name"], {"symbol": "BTCUSDT"})
```

Recommended capability targets for AstroFin are financial market data, crypto quotes, financial news/search, economic/earnings calendars, and GitHub operations. Registry entries are community maintained; review permissions, credentials, rate limits, and provenance before connecting a server to a production agent.

### CLI

Run from the repository root:

```bash
python -m integrations.gitagent.adapters.cli mcp-search "financial crypto market data"
python -m integrations.gitagent.adapters.cli mcp-install owner/server --config config.json
python -m integrations.gitagent.adapters.cli mcp-list
python -m integrations.gitagent.adapters.cli mcp-list-tools
python -m integrations.gitagent.adapters.cli mcp-recommended
```

`mcp-install` establishes a Smithery connection; it is not a local npm package installation. A real connection requires the Smithery CLI and any server-specific OAuth/API configuration.

## Agent Export/Import

```bash
python -m integrations.gitagent.adapters.cli export-agent TechnicalAgent --output ./exported_agents
python -m integrations.gitagent.adapters.cli import-agent ./integrations/gitagent/exported_agents/technicalagent_agent.json
python -m integrations.gitagent.adapters.cli list-agents
```

The canonical runtime registry is `agents/gitagent_registry.py`; active implementations are under `agents/_impl/`. The JSON files are portable GitAgent metadata and do not duplicate executable agent code.

## Dashboard Decision

Use LangGraph as the authoritative agent orchestration/state layer. Add n8n only at the boundary for scheduled ingestion, webhooks, normalization, and notifications. See `docs/dashboard-evaluation.md`.

## Testing

```bash
source .venv/bin/activate
pytest -q integrations/gitagent/tests
ruff check integrations/gitagent
```

The test suite covers REST/CLI search fallback, deduplication, connection persistence, MCP schema wrapping, tool listing, CLI commands, and recommended capability coverage.
