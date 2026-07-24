"""Evolution / GA Prometheus metrics — root workspace shim.

Original semantics preserved; all 13 metric registrations are idempotent via
the ``_safe`` helper. This avoids ``ValueError: Duplicated timeseries`` when
this module is reached through two different import paths (root
``meta_rl.metrics`` and the package shim ``astrofin-sentinel-v5/meta_rl/metrics.py``)
during test collection.

See KI-018 in docs/KNOWN_ISSUES.md.
"""

from __future__ import annotations

from typing import TypeVar

from prometheus_client import REGISTRY, Counter, Gauge, Histogram

_T = TypeVar("_T", Gauge, Counter, Histogram)


def _safe(metric_cls: type[_T], name: str, *args, **kwargs) -> _T:
    """Return existing metric from REGISTRY or create it idempotently.

    ``prometheus_client`` raises ``ValueError: Duplicated timeseries`` when a
    metric of the same name is registered twice against the default
    ``CollectorRegistry``. Because this shim can be reached through two
    different module paths (root ``meta_rl.metrics`` and the package shim
    ``astrofin-sentinel-v5/meta_rl/metrics.py``), construction is wrapped to
    return the already-registered collector instead of failing.
    """
    existing = REGISTRY._names_to_collectors.get(name)
    if existing is not None:
        return existing  # type: ignore[return-value]
    try:
        return metric_cls(name, *args, **kwargs)
    except ValueError:
        reg = REGISTRY._names_to_collectors.get(name)
        if reg is not None:
            return reg  # type: ignore[return-value]
        raise


## Counter: total number of strategies evaluated
# (no top-level metric here — see STRATEGIES_EVALUATED below)


## Gauge: current number of active strategies in the pool
strategies_active = _safe(
    Gauge,
    "astrofin_strategies_active",
    "Current number of active strategies in the pool",
)


## Histogram: duration of one generation of evolution (seconds)
evolution_duration_seconds = _safe(
    Histogram,
    "astrofin_evolution_duration_seconds",
    "Duration of evolution generation in seconds",
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, 120),
)

# ── Added for EvolutionEngine ─────────────────────────────────────────────────
EVOLUTION_RUNS = _safe(
    Counter, "astrofin_evolution_runs", "Total evolution runs started"
)
STRATEGIES_EVALUATED = _safe(
    Counter, "astrofin_strategies_evaluated", "Total strategies evaluated"
)
GENERATION_CURRENT = _safe(
    Gauge, "astrofin_generation_current", "Current generation number"
)
STRATEGY_EVALUATED_TOTAL = _safe(
    Counter,
    "astrofin_strategy_evaluated_total",
    "Total strategies evaluated across all runs",
)

# ── Additional metrics for EvolutionEngine ────────────────────────────────────
BEST_REWARD = _safe(Gauge, "astrofin_best_reward", "Best reward in current generation")
MEAN_REWARD = _safe(Gauge, "astrofin_mean_reward", "Mean reward of population")
REWARD_STD = _safe(Gauge, "astrofin_reward_std", "Standard deviation of reward")
POPULATION_SIZE = _safe(Gauge, "astrofin_population_size", "Current population size")
STRATEGIES_CREATED = _safe(
    Counter, "astrofin_strategies_created", "Total strategies created"
)
GENERATIONS_TOTAL = _safe(
    Counter, "astrofin_generations_total", "Total number of generations"
)
GENERATION_DURATION = _safe(
    Histogram,
    "astrofin_generation_duration_seconds",
    "Duration of each generation in seconds",
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, 120),
)
