from prometheus_client import Counter, Gauge, Histogram

## Counter: total number of strategies evaluated

## Gauge: current number of active strategies in the pool
strategies_active = Gauge("astrofin_strategies_active", "Current number of active strategies in the pool")

## Histogram: duration of one generation of evolution (seconds)
evolution_duration_seconds = Histogram(
    "astrofin_evolution_duration_seconds",
    "Duration of evolution generation in seconds",
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, 120),
)

# ── Added for EvolutionEngine ─────────────────────────────────────────────────
EVOLUTION_RUNS = Counter("astrofin_evolution_runs", "Total evolution runs started")
STRATEGIES_EVALUATED = Counter("astrofin_strategies_evaluated", "Total strategies evaluated")
GENERATION_CURRENT = Gauge("astrofin_generation_current", "Current generation number")
STRATEGY_EVALUATED_TOTAL = Counter("astrofin_strategy_evaluated_total", "Total strategies evaluated across all runs")

# ── Additional metrics for EvolutionEngine ────────────────────────────────────
BEST_REWARD = Gauge("astrofin_best_reward", "Best reward in current generation")
MEAN_REWARD = Gauge("astrofin_mean_reward", "Mean reward of population")
REWARD_STD = Gauge("astrofin_reward_std", "Standard deviation of reward")
POPULATION_SIZE = Gauge("astrofin_population_size", "Current population size")
STRATEGIES_CREATED = Counter("astrofin_strategies_created", "Total strategies created")
GENERATIONS_TOTAL = Counter("astrofin_generations_total", "Total number of generations")
GENERATION_DURATION = Histogram(
    "astrofin_generation_duration_seconds",
    "Duration of each generation in seconds",
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, 120),
)
