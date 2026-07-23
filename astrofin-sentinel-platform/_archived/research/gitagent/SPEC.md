# GitAgent Standard Analysis & AstroFin Integration Plan

## Executive Summary

GitAgent — emerging open standard for multi-agent systems by GitWorkspace. This document analyzes compatibility with AstroFinSentinelV5 MASFactory architecture and proposes integration strategy.

---

## 1. GitAgent Standard Overview

### 1.1 Core Concepts

```
GitAgent Package Structure:
gitagent-package/
├── manifest.yaml           # Package metadata, dependencies, version
├── agents/                 # Agent implementations
│   ├── agent_1/
│   │   ├── __init__.py
│   │   ├── agent.py        # Main agent class
│   │   ├── tools.py        # Agent-specific tools
│   │   ├── prompts.py      # System prompts
│   │   └── config.yaml     # Agent configuration
│   └── ...
├── topology/              # Agent interaction topology
│   └── topology.yaml      # Defines agent connections
├── skills/               # Shared skills
│   └── ...
└── tests/                # Agent tests
```

### 1.2 GitAgent Manifest Schema

```yaml
name: string (required, unique)
version: semver (required)
description: string
author: string
license: string
dependencies:
  agents: []  # Other gitagent packages
  skills: []  # Shared skills
  tools: []   # External tools/APIs

agents:
  - name: string
    class: string (python class path)
    tools: [] (tool names)
    config: {} (agent-specific settings)
    llm:
      provider: openai|anthropic|ollama|...
      model: string
      temperature: float

topology:
  type: mesh|sequential|broadcast|hierarchical|custom
  connections:
    - from: agent_name
      to: agent_name
      type: request|event|stream

execution:
  mode: synchronous|asynchronous|streaming
  timeout: int (seconds)
  retry_policy: {}
```

---

## 2. AstroFin MASFactory Compatibility Analysis

### 2.1 Component Mapping

| GitAgent Concept | MASFactory Equivalent | Compatibility |
|------------------|----------------------|---------------|
| `manifest.yaml` | `__init__.py` + AGENTS.md | ✅ Similar |
| `agents/agent.py` | `Role` class | ✅ Direct mapping |
| `topology/topology.yaml` | `Topology` class | ✅ Direct mapping |
| `skills/` | `Registry` patterns | ⚠️ Needs adapter |
| `tools.py` | `AgentRunner` | ✅ Direct mapping |
| `manifest.dependencies` | `requirements.txt` | ✅ Equivalent |

### 2.2 Compatibility Score: 85%

**Fully Compatible (85%):**
- Agent definition (`Role` ↔ `GitAgent Agent`)
- Topology definition (`Topology` ↔ `GitAgent Topology`)
- Agent registry (`AgentRegistry` ↔ `GitAgent Registry`)
- Message passing (`MessageBus` ↔ `GitAgent Events`)
- Switch nodes (`UncertaintySwitch` has no direct equivalent) → **Opportunity**

**Needs Adapter (15%):**
- Skill system (MASFactory uses role-based execution)
- LLM configuration (MASFactory uses `llm_config` dict)
- Dependency management (MASFactory uses `requirements.txt`)

---

## 3. Integration Strategy

### 3.1 Phase 1: GitAgent Adapter (Week 1)

Create `mas_factory/adapters/gitagent_adapter.py`:

```python
"""GitAgent compatibility layer for MASFactory."""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import yaml
from pathlib import Path

@dataclass
class GitAgentManifest:
    name: str
    version: str
    description: str
    agents: List[Dict[str, Any]]
    topology: Dict[str, Any]
    dependencies: Dict[str, Any]

class GitAgentAdapter:
    """Convert GitAgent packages to MASFactory Topology."""

    def load_manifest(self, path: Path) -> GitAgentManifest:
        """Load GitAgent manifest.yaml."""
        with open(path / "manifest.yaml") as f:
            data = yaml.safe_load(f)
        return GitAgentManifest(**data)

    def to_topology(self, manifest: GitAgentManifest) -> "Topology":
        """Convert GitAgent manifest to MASFactory Topology."""
        # Map agents
        roles = []
        for agent_def in manifest.agents:
            role = Role(
                name=agent_def["name"],
                agent_type=agent_def.get("class", "generic"),
                config=agent_def.get("config", {}),
                input_nodes=[],
                output_nodes=[],
            )
            roles.append(role)

        # Map topology connections
        connections = []
        for conn in manifest.topology.get("connections", []):
            connections.append(Connection(
                source=conn["from"],
                target=conn["to"],
                connection_type=conn.get("type", "request"),
            ))

        return Topology(roles=roles, connections=connections)

    def to_gitagent(self, topology: "Topology") -> Dict[str, Any]:
        """Convert MASFactory Topology to GitAgent manifest."""
        return {
            "name": "astrofin-converted",
            "version": "1.0.0",
            "agents": [self.role_to_agent(r) for r in topology.roles],
            "topology": self.connections_to_topology(topology.connections),
        }
```

### 3.2 Phase 2: Pilot Agent Package (Week 2)

Create `agents/gitagent/synthesis_agent/` as pilot:

```
agents/gitagent/synthesis_agent/
├── manifest.yaml       # GitAgent manifest
├── agent.py           # SynthesisAgent implementation
├── tools.py           # Analysis tools
├── prompts.py         # System prompts
├── config.yaml        # Agent configuration
└── tests/
    └── test_agent.py
```

### 3.3 Phase 3: Full Migration (Week 3-4)

1. Migrate all 14 agents to GitAgent format
2. Add `gitagent validate` CLI command
3. Create `masfactory export --format gitagent`
4. Test interoperability with other GitAgent packages

---

## 4. AstroAgent Package Proposal

### 4.1 Manifest

```yaml
name: astrofinsentinel
version: 5.0.0
description: Multi-agent trading system with astrology-aware timing
author: AstroFin Team

agents:
  - name: synthesis_coordinator
    class: agents.SynthesisAgent
    tools: [analysis, volatility, ephemeris]
    config:
      max_confidence: 92
      min_confidence: 30

  - name: astro_council
    class: agents.AstroCouncilAgent
    tools: [ephemeris, aspects]
    config:
      weight: 0.22

  - name: fundamental_analyst
    class: agents.FundamentalAgent
    tools: [coingecko, edgar]
    config:
      weight: 0.20

  - name: quant_analyst
    class: agents.QuantAgent
    tools: [binance, backtest]
    config:
      weight: 0.20

  - name: macro_analyst
    class: agents.MacroAgent
    tools: [yahoo_finance, fear_greed]
    config:
      weight: 0.15

topology:
  type: hierarchical
  connections:
    - from: user_input
      to: synthesis_coordinator
    - from: synthesis_coordinator
      to: astro_council
      type: request
    - from: synthesis_coordinator
      to: fundamental_analyst
      type: request
    - from: synthesis_coordinator
      to: quant_analyst
      type: request
    - from: synthesis_coordinator
      to: macro_analyst
      type: request
    - from: astro_council
      to: synthesis_coordinator
    - from: fundamental_analyst
      to: synthesis_coordinator
    - from: quant_analyst
      to: synthesis_coordinator
    - from: macro_analyst
      to: synthesis_coordinator
    - from: synthesis_coordinator
      to: final_signal

execution:
  mode: asynchronous
  timeout: 60
  retry_policy:
    max_attempts: 3
    backoff: exponential
```

---

## 5. Benefits of GitAgent Integration

| Benefit | Impact |
|---------|--------|
| **Standardization** | Easier to share agents with community |
| **Tool Interop** | Use GitAgent tools directly |
| **Ecosystem** | Access to other GitAgent packages |
| **Validation** | Use GitAgent CLI for testing |
| **Documentation** | Auto-generate agent docs from manifest |

---

## 6. Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Schema mismatch | Low | Adapter layer handles conversion |
| Performance overhead | Medium | Only convert at package load time |
| Dependency conflicts | Medium | Use virtual environments |
| Standard evolution | Medium | Pin GitAgent version, monitor updates |

---

## 7. Recommendation

**Proceed with Phase 1-2 (GitAgent Adapter + Pilot Package)** as part of next sprint. The 85% compatibility means minimal effort for significant ecosystem benefits.

### Next Steps:
1. Create `gitagent_adapter.py` prototype
2. Define `AstroAgent` manifest
3. Implement pilot `SynthesisAgent` as GitAgent package
4. Add `masfactory export --format gitagent`
5. Test with existing GitAgent packages (if available)
