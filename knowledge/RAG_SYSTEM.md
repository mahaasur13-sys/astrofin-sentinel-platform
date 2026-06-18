# AstroFin Sentinel v5 — RAG Knowledge System

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                    RAG-First Multi-Agent System                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   User Query ──► Router Agent                                        │
│                      │                                                │
│         ┌────────────┼────────────┐                                  │
│         ▼            ▼            ▼                                  │
│    Technical    Astro       Electional    ← 3 специализированных      │
│      Team      Council        Agent          потока                   │
│         │            │            │                                  │
│         └────────────┼────────────┘                                  │
│                      ▼                                                │
│               Synthesis Agent                                         │
│                      │                                                │
│                      ▼                                                │
│              Final Recommendation                                     │
│                                                                       │
│   ┌─────────────────────────────────────────────────────────────┐     │
│   │              SHARED KNOWLEDGE BASE (RAG)                    │     │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │     │
│   │  │ Astrology/   │  │ Technical/  │  │ Trading /       │   │     │
│   │  │ Vedic        │  │ Indicators   │  │ Risk Mgmt       │   │     │
│   │  └─────────────┘  └─────────────┘  └─────────────────┘   │     │
│   └─────────────────────────────────────────────────────────────┘     │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

## RAG Index Structure

```
knowledge/
├── chunks/                    # Source markdown files
│   ├── astrology/
│   │   ├── nakshatras.md      # 27 lunar mansions + trading rules
│   │   ├── choghadiya.md      # 8 daily periods, Muhurta scoring
│   │   └── muhurta.md         # Timing system, formulas, examples
│   ├── technical/
│   │   ├── indicators.md       # RSI, MACD, Bollinger Bands
│   │   └── ellott_wave.md     # Elliott Wave theory + Fib ratios
│   └── trading/
│       ├── position_sizing.md  # Kelly criterion, risk-based sizing
│       └── risk_management.md  # Drawdown rules, dynamic scaling
├── indexes/                   # FAISS binary indexes (built by build_index.py)
│   ├── astrology.index        # 17 chunks, 768-dim, nomic-embed-text
│   ├── technical.index        # 6 chunks, 768-dim
│   └── trading.index          # 6 chunks, 768-dim
├── rag_retriever.py           # FAISS-backed retrieval interface
└── build_index.py             # Index build CLI
```

## Retrieval Flow

```
Agent Query
    │
    ▼
[Embedding]          ← nomic-embed-text via Ollama API (768-dim)
    │
    ▼
[FAISS Search]       ← IndexFlatIP (cosine sim via L2-normalized vectors)
    │
    ▼
[Cross-domain merge] ← dedup by source+title, sort by score
    │
    ▼
[Context Window]     ← top-k chunks → agent context
    │
    ▼
Agent Response       ← always with citation metadata
```

## Index Build CLI

```bash
# Build all indexes
python knowledge/build_index.py build

# Build specific domain
python knowledge/build_index.py build --domain astrology

# Rebuild existing indexes
python knowledge/build_index.py build --rebuild

# Check stats
python knowledge/build_index.py stats

# Test search
python knowledge/build_index.py search "nakshatra for trading" --domain astrology
```

## Retriever CLI

```bash
# Interactive stats
python knowledge/rag_retriever.py

# Direct search (agent tool interface)
python knowledge/rag_retriever.py "RSI overbought" --domain technical --top-k 3
```

## Agent Integration

```python
from knowledge.rag_retriever import retrieve_knowledge, RAGRetriever

# Tool interface (called by agents)
result = retrieve_knowledge(
    query="best nakshatra for entry",
    domain="astrology",     # optional filter
    top_k=5
)

# Direct class usage
retriever = RAGRetriever()
chunks = retriever.retrieve("momentum indicators", top_k=3)
stats = retriever.stats()  # {'astrology': {'indexed_chunks': 17, ...}, ...}
```

## Domains

| Domain | Agents | Index | Chunks |
|--------|--------|-------|--------|
| `astrology` | AstroCouncil, ElectionalAgent | `astrology.index` | 17 |
| `technical` | MarketAnalyst, WaveAgents | `technical.index` | 6 |
| `trading` | All agents | `trading.index` | 6 |

**Embedding model:** `nomic-embed-text` via Ollama (`localhost:11434`)
**Dimension:** 768
**Index type:** FAISS `IndexFlatIP` (inner product = cosine similarity on normalized vectors)
