"""
agents/metrics.py
=================
Shared Prometheus metrics factory and `@track_agent_metrics` decorator
for AstroFin Sentinel V5 agents.

Convention (enforced by `scripts/validate_agent.py` and CI):

    Counter  name:  sentinel_<agent_snake>_runs_total
    Histogram name: sentinel_<agent_snake>_latency_seconds

`<agent_snake>` is the agent's name in lower_snake_case
(e.g. ``MacroAgent`` → ``macro_agent``).

Two usage patterns are supported:

Pattern A — factory + decorator (preferred)::

    from agents.metrics import (
        agent_counter, agent_latency, track_agent_metrics,
    )

    class MacroAgent(BaseAgent[AgentResponse]):
        @track_agent_metrics
        async def run(self, state: dict) -> AgentResponse:
            return await self.analyze(state)

That's it — the decorator registers a Counter and a Histogram
on demand, increments the Counter (labelled by signal), and times
the call.

Pattern B — manual instantiation (when the decorator is awkward,
e.g. legacy agents whose ``run()`` signature cannot be wrapped)::

    from agents.metrics import agent_counter, agent_latency

    RUNS = agent_counter("macro_agent")
    LATENCY = agent_latency("macro_agent")

    async def run(self, state: dict) -> AgentResponse:
        with LATENCY.time():
            response = await self.analyze(state)
            RUNS.labels(signal=response.signal.value).inc()
            return response

Both patterns produce the same metric names, so dashboards see one
metric per agent regardless of which pattern the author picked.
"""

from __future__ import annotations

import functools
import re
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from prometheus_client import Counter, Histogram

P = ParamSpec("P")
R = TypeVar("R")

# Standard latency buckets — 1ms to 5s. The 5ms bucket matches the P99
# budget called out in ``_template_agent.py``.
_DEFAULT_BUCKETS: tuple[float, ...] = (
    0.001,
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.5,
    1.0,
    5.0,
)

# Cache so a second call to ``agent_counter("macro_agent")`` returns the
# same object — prometheus_client raises on duplicate metric registration.
_COUNTER_CACHE: dict[str, Counter] = {}
_HISTOGRAM_CACHE: dict[str, Histogram] = {}

# We use ``_snake_case`` of the agent name as the metric suffix.
# PascalCase / camelCase / already-snake all collapse to lower_snake.
_NAME_RE = re.compile(r"(?<!^)(?=[A-Z])")


def _snake(name: str) -> str:
    """``MacroAgent`` → ``macro_agent``; ``TimeWindowAgent`` → ``time_window_agent``."""
    s = _NAME_RE.sub("_", name).lower().strip("_")
    # Collapse any double underscores created by acronym handling.
    s = re.sub(r"_+", "_", s)
    return s


def agent_counter(agent_name: str) -> Counter:
    """
    Return the canonical ``sentinel_<agent_snake>_runs_total`` Counter.

    The Counter is labelled by ``agent`` and ``signal``. Calling this
    multiple times with the same ``agent_name`` returns the same object.
    """
    snake = _snake(agent_name)
    if snake in _COUNTER_CACHE:
        return _COUNTER_CACHE[snake]
    counter = Counter(
        f"sentinel_{snake}_runs_total",
        f"Total runs of the {agent_name} agent, partitioned by signal.",
        labelnames=("agent", "signal"),
    )
    _COUNTER_CACHE[snake] = counter
    return counter


def agent_latency(agent_name: str) -> Histogram:
    """
    Return the canonical ``sentinel_<agent_snake>_latency_seconds`` Histogram.

    Labelled by ``agent``. Standard buckets cover 1ms–5s.
    """
    snake = _snake(agent_name)
    if snake in _HISTOGRAM_CACHE:
        return _HISTOGRAM_CACHE[snake]
    hist = Histogram(
        f"sentinel_{snake}_latency_seconds",
        f"Latency of the {agent_name} agent, in seconds.",
        labelnames=("agent",),
        buckets=_DEFAULT_BUCKETS,
    )
    _HISTOGRAM_CACHE[snake] = hist
    return hist


def track_agent_metrics(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator that times ``func`` and increments the per-agent run Counter.

    Works on async methods of BaseAgent subclasses::

        class MacroAgent(BaseAgent[AgentResponse]):
            @track_agent_metrics
            async def run(self, state: dict) -> AgentResponse:
                return await self.analyze(state)

    The decorator discovers the agent's display name from ``self.name`` —
    so the metric suffix stays consistent with the registry.
    """

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        # Resolve the agent name lazily (we need a live instance to read it).
        self_obj = args[0] if args else None
        agent_label = getattr(self_obj, "name", None) or func.__qualname__
        counter = agent_counter(agent_label)
        latency = agent_latency(agent_label)

        with latency.labels(agent=agent_label).time():
            result = await func(*args, **kwargs)

        # Best-effort signal labelling — agents that return AgentResponse
        # are labelled by signal; everything else is labelled "unknown".
        signal = getattr(result, "signal", None)
        signal_label = (
            signal.value if hasattr(signal, "value") else (signal or "unknown")
        )
        try:
            counter.labels(agent=agent_label, signal=str(signal_label)).inc()
        except Exception:  # noqa: BLE001 — never let metrics crash the agent
            pass
        return result

    return wrapper


__all__ = [
    "agent_counter",
    "agent_latency",
    "track_agent_metrics",
]
