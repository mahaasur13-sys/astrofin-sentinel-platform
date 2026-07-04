# GitAgent Changelog

All notable changes to the GitAgent integration are documented here.

## [ATOM-GITAGENT-002] — 2026-07-04

### Phase A: MCP Adapter for Smithery/GitHub Tools — COMPLETE

- **Adapters**:
  - `adapters/mcp_adapter.py` (496 lines) — `MCPAdapter` class implementing:
    - `mcp_search(query, category=None)` — Live Smithery registry search via REST API + CLI fallback + offline keyword DB
    - `mcp_install(server_name, config=None)` — Dynamic installation via `@smithery/cli` with npm fallback
    - `mcp_list_tools()` — Lists tools from all installed MCP servers
    - `mcp_uninstall(install_id)` — Removes installed servers
    - `wrap_tool(tool_def)` — Wraps MCP tools as GitAgent-compatible definitions
    - `get_recommended_servers()` — Curated 10-server list for financial/trading use cases
  - Persistence: `~/.gitagent/mcp/installed_servers.json` + `~/.gitagent/mcp/servers/`

- **CLI Commands** (in `adapters/cli.py`):
  - `export-agent <name>` — Export AstroFinSentinelV5 agent to JSON
  - `import-agent <file>` — Import agent JSON back to working memory
  - `list-agents` — List all 10 available agents
  - `mcp-search <query> [--category]` — Search Smithery registry
  - `mcp-install <name> [--config]` — Install MCP server
  - `mcp-list` — List installed MCP servers
  - `mcp-list-tools` — List tools from installed servers
  - `mcp-recommended` — Show curated 10-server recommendation list

### Phase B: LangGraph vs n8n Dashboard Evaluation — COMPLETE

- `docs/dashboard-evaluation.md` (144 lines) — Full analysis with:
  - LangGraph strengths (state machines, checkpointing, sub-graphs)
  - n8n strengths (data ingestion, event-driven flows, no-code)
  - **Recommendation**: Hybrid — LangGraph for orchestration, n8n for data ingestion
  - Mermaid architecture diagram
  - 3-phase implementation strategy

### Phase C: Export Remaining Agents — COMPLETE

All 10 agents exported to `exported_agents/*.json`:
- AstroCouncil (L7 supervisor)
- FundamentalAgent (L6)
- QuantAgent (L6)
- MacroAgent (L6)
- TechnicalAgent (L6)
- BullBot (L5)
- BearBot (L5)
- RiskAgent (L8)
- SentimentAgent (L5)
- SynthesisAgent (L7)

### Tests

- `tests/test_mcp_adapter.py` (142 lines, 12 tests) — All passing ✅
  - Adapter init, search, category filter, fallback DB, tool wrap, install, list, recommended, deduplication
  - CLI command execution (list-agents, mcp-recommended, mcp-search)
- `tests/test_validator.py` (461 lines) — Agent validator tests

### Verification (2026-07-04)

- ✅ `pytest tests/test_mcp_adapter.py` — 12/12 pass
- ✅ `mcp-search github` → 10 results (live Smithery API)
- ✅ `mcp-search finance --category financial` → 8 results
- ✅ `mcp-search crypto --category crypto` → 8 results
- ✅ `mcp-search news --category news` → 10 results
- ✅ `mcp-search calendar --category calendar` → 9 results
- ✅ Round-trip import test: all 10/10 agents pass `import-agent`

### Files Delivered

| File | Lines | Status |
|------|-------|--------|
| `adapters/mcp_adapter.py` | 496 | NEW |
| `adapters/cli.py` | 263 | UPDATED (MCP commands added) |
| `README.md` | 155 | UPDATED (MCP section) |
| `docs/dashboard-evaluation.md` | 144 | NEW |
| `tests/test_mcp_adapter.py` | 142 | NEW |
| `exported_agents/*.json` | 10 files | NEW (all 10 agents) |

---

## [ATOM-GITAGENT-001] — Earlier

### Phase 1+2: Core Agent Export — COMPLETE

- AstroCouncil, FundamentalAgent, QuantAgent, MacroAgent exported
- CLI `export-agent` / `import-agent` commands implemented
