"""
AstroFin Sentinel v5 — Synthesis Agent (backward-compatible wrapper).

⚠️  DECOMPOSED (v1.0.0, feature/synthesis-decomposition).

Original 659-line monolithic file has been split into:
  agents/_impl/synthesis/
    ├── agent.py       : SynthesisAgent class
    ├── weights.py     : weight loading + category constants
    ├── classifier.py  : signal grouping + conflict detection
    ├── voter.py       : weighted voting + synthesis + guards
    ├── levels.py      : price level calculation
    └── formatting.py  : breakdown + source collection

All existing imports continue to work:
  from agents._impl.synthesis_agent import SynthesisAgent, run_synthesis_agent, create
"""
from agents._impl.synthesis.agent import SynthesisAgent, run_synthesis_agent, create

__all__ = ["SynthesisAgent", "run_synthesis_agent", "create"]
