"""
Synthesis decomposition (v1.0.0 — feature/synthesis-decomposition, PR pending).

Original 659-line synthesis_agent.py split into:
- agent.py      : SynthesisAgent class + analyze/run logic
- weights.py    : weight loading + category constants
- classifier.py : signal grouping + conflict detection
- voter.py      : voting, synthesis, guards
- levels.py     : price level calculation
- formatting.py : breakdown formatting + source collection

Backward-compatible imports kept in agents/_impl/synthesis_agent.py.
"""
from agents._impl.synthesis.agent import SynthesisAgent, create, run_synthesis_agent

__all__ = ["SynthesisAgent", "run_synthesis_agent", "create"]
