"""
agents/_impl/_template_agent.py
================================
Canonical template for a new AstroFin Sentinel V5 agent.

Use it as a starting point. Read every `# TODO` and the docstrings below
before you copy it.

Quick start:
    cp agents/_impl/_template_agent.py agents/_impl/my_new_agent.py
    # Rename TemplateAgent -> MyNewAgent everywhere (autocomplete does it in 3s).
    # Implement analyze(state).
    python scripts/validate_agent.py agents/_impl/my_new_agent.py
    pytest -q tests/test_my_new_agent_agent.py

The contract — every agent MUST:
    1. Subclass BaseAgent[AgentResponse] (R1 in the linter).
    2. Call super().__init__() with name, instructions_path, domain, weight.
    3. Implement async def run(self, state: dict) -> AgentResponse.
    4. Use @require_ephemeris if it touches planetary positions (R2).
    5. Consume all data through data_room.blueprint (R3, R4).
    6. Return a fully-populated AgentResponse — never a bare dict.
    7. Define a top-level `run_<agent_name>()` convenience function so the
       orchestrator / registry can call it without instantiating the class.
    8. Export at least one Prometheus metric (R6 in the architecture doc).

The contract — every agent SHOULD:
    - Be deterministic for a given state (no `random` without seeded RNG).
    - Run under 50ms on a hot state (P99 budget: 5ms / agent).
    - Log at INFO on start, DEBUG on each RAG fetch, WARNING on graceful
      degradation.
    - Tag every log line with `agent=<self.name>` and `session_id`.
"""
from __future__ import annotations

import logging
from typing import Any

from prometheus_client import Counter, Histogram

from agents._impl.ephemeris_decorator import EphemerisUnavailableError, require_ephemeris
from core.base_agent import EPHEMERIS_UNAVAILABLE, UNKNOWN, AgentResponse, BaseAgent, SignalDirection

logger = logging.getLogger(__name__)


# ─── Prometheus metrics (declare once per agent; keep names unique) ───────────

# TODO: rename "template" to your agent name (e.g. "my_new_agent").
# Use snake_case for the metric suffix, PascalCase for the label.
TEMPLATE_RUNS_TOTAL = Counter(
    "sentinel_template_runs_total",
    "Total runs of the template agent, partitioned by signal.",
    labelnames=("agent", "signal"),
)
TEMPLATE_LATENCY_SECONDS = Histogram(
    "sentinel_template_latency_seconds",
    "Latency of the template agent.",
    labelnames=("agent",),
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.5, 1.0, 5.0),
)


class TemplateAgent(BaseAgent[AgentResponse]):
    """
    TemplateAgent — replace this docstring with what your agent does.

    Domain:        # TODO: pick one of the 6 DDD bounded contexts.
                   # (astro | fundamental | macro | quant | technical | risk | sentiment | research)
    Weight:        # TODO: 0.05 - 0.30; tune in backtest.
    Data inputs:   # TODO: list the data_room.*() calls you make.
    Signal:        # TODO: LONG / SHORT / NEUTRAL / AVOID, plus a one-line rationale.
    """

    # TODO: rename class to MyNewAgent. Also update class name in the
    # convenience function at the bottom of this file.

    def __init__(self) -> None:
        """
        Initialize the agent.

        Do NOT do I/O here. The constructor must be cheap (<1ms) so the
        orchestrator can pre-warm agents without surprise latency.
        """
        super().__init__(
            name="TemplateAgent",  # TODO
            instructions_path="agents/TemplateAgent_instructions.md",  # TODO: create this file
            domain="quant",  # TODO
            weight=0.0,  # TODO
        )

    @require_ephemeris
    async def analyze(self, state: dict[str, Any]) -> AgentResponse:
        """
        Core analysis method.

        Args:
            state: SentinelState dict from the orchestrator. Always has:
                   - symbol: str
                   - current_price: float
                   - timeframe: str
                   - regime: str (one of LOW / NORMAL / HIGH / EXTREME)
                   May also have: positions, history, rag_context, ...

        Returns:
            AgentResponse. Must have:
            - signal in {LONG, SHORT, NEUTRAL, AVOID}
            - confidence in [0, 100]
            - reasoning: a human-readable, ≤2-paragraph justification
            - sources: list of RAG chunk IDs consulted (may be empty)
            - metadata: dict; on graceful degradation, set
              metadata["degraded"] = True and
              metadata["degradation_reason"] = "<MACHINE_READABLE>"

        Raises:
            Never. Convert every exception to a degraded AgentResponse.
        """
        symbol = state.get("symbol", "BTCUSDT")
        # TODO: implement the actual analysis.

        # ── Step 1: pull data from the Data Room ───────────────────────
        # try:
        #     tick = data_room.blueprint.get_price(symbol, asof=state.get("asof"))
        #     quality = tick.quality
        # except DataRoomError as e:
        #     return self._degraded(reason="DATA_ROOM_TIMEOUT", msg=str(e))

        # ── Step 2: pull planetary positions if applicable ─────────────
        # try:
        #     positions = core.ephemeris.get_planetary_positions(...)
        # except EphemerisUnavailableError as e:
        #     return self._degraded(reason="EPHEMERIS_UNAVAILABLE", msg=str(e))

        # ── Step 3: optional RAG ───────────────────────────────────────
        # chunks = self.retrieve(f"{symbol} macro outlook")
        # for c in chunks:
        #     self.sources.append(c["id"])

        # ── Step 4: compute the signal ────────────────────────────────
        # This is the part you actually write.

        # ── Step 5: assemble the response ──────────────────────────────
        response = AgentResponse(
            agent_name=self.name,
            signal=SignalDirection.NEUTRAL,  # TODO
            confidence=50,  # TODO
            reasoning="Template agent — replace with real reasoning.",  # TODO
            sources=self.sources,
            metadata={
                "data_quality": 1.0,  # set from the tick
            },
        )
        TEMPLATE_RUNS_TOTAL.labels(agent=self.name, signal=response.signal.value).inc()
        return response

    async def run(self, state: dict[str, Any]) -> AgentResponse:
        """
        Public entry point. Wraps `analyze` with the latency histogram
        and a defensive try/except so a single agent can never crash
        the orchestrator.
        """
        with TEMPLATE_LATENCY_SECONDS.labels(agent=self.name).time():
            try:
                return await self.analyze(state)
            except EphemerisUnavailableError as e:
                # @require_ephemeris raised before we got to analyze.
                return self._degraded(EPHEMERIS_UNAVAILABLE, str(e))
            except Exception as e:  # noqa: BLE001 — last-resort guard
                logger.exception("agent_run_unhandled", extra={"agent": self.name})
                return self._degraded(UNKNOWN, repr(e))

    # NOTE: `_degraded(reason, msg)` is inherited from BaseAgent.
    # Standard reason constants live in core/base_agent.py:
    #   EPHEMERIS_UNAVAILABLE, DATA_ROOM_TIMEOUT, DATA_ROOM_ERROR,
    #   RAG_UNAVAILABLE, TIMEOUT, UNKNOWN
    # Do NOT redefine it locally.


# ─── Convenience runner ──────────────────────────────────────────────────────
# The registry calls this. Do not change the signature.

async def run_template_agent(state: dict[str, Any]) -> AgentResponse:
    """Convenience runner used by `agents/gitagent_registry.py`."""
    return await TemplateAgent().run(state)


__all__ = ["TemplateAgent", "run_template_agent"]
