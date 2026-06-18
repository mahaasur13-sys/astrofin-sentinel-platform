"""strategies/generator.py — ATOM-STEP-11: Strategy Generator (Genetic Programming)"""

import random
from dataclasses import dataclass, field

import numpy as np

from strategies.base import BaseStrategy, Regime, Signal, StrategyConfig, StrategyResult

# ── Gene definitions ──────────────────────────────────────────────────────


@dataclass
class Gene:
    name: str
    type: str  # "float", "int", "choice"
    default: any
    range_min: any = None
    range_max: any = None
    options: list = field(default_factory=list)
    mutation_scale: float = 0.2


GENES = {
    "confidence_threshold": Gene("confidence_threshold", "float", 30.0, 15.0, 55.0, mutation_scale=5.0),
    "position_size_pct": Gene("position_size_pct", "float", 15.0, 5.0, 30.0, mutation_scale=3.0),
    "regime_filter": Gene("regime_filter", "choice", "ALL", options=["ALL", "BULL_ONLY", "BEAR_ONLY"]),
    "signal_weights_bull": Gene("signal_weights_bull", "float", 0.7, 0.0, 1.0),
    "signal_weights_bear": Gene("signal_weights_bear", "float", 0.5, 0.0, 1.0),
    "atr_multiplier": Gene("atr_multiplier", "float", 2.0, 1.0, 4.0, mutation_scale=0.3),
    "use_momentum": Gene("use_momentum", "choice", True, options=[True, False]),
    "use_mean_reversion": Gene("use_mean_reversion", "choice", False, options=[True, False]),
    "lookback_fast": Gene("lookback_fast", "int", 10, 3, 30),
    "lookback_slow": Gene("lookback_slow", "int", 50, 20, 200),
    "entry_confirmation_required": Gene("entry_confirmation_required", "choice", True, options=[True, False]),
}

CHROMOSOME_KEYS = list(GENES.keys())


def random_chromosome() -> dict:
    return {k: _random_gene(k, v) for k, v in GENES.items()}


def _random_gene(name: str, gene: Gene):
    if gene.type == "float":
        return random.uniform(gene.range_min, gene.range_max)
    if gene.type == "int":
        return random.randint(gene.range_min, gene.range_max)
    if gene.type == "choice":
        return random.choice(gene.options)


def crossover(parent_a: dict, parent_b: dict) -> dict:
    child = {}
    for k in CHROMOSOME_KEYS:
        child[k] = random.choice([parent_a[k], parent_b[k]])
    return child


def mutate(chromosome: dict, rate: float = 0.15) -> dict:
    for k in CHROMOSOME_KEYS:
        if random.random() < rate:
            gene = GENES[k]
            if gene.type == "float":
                delta = random.uniform(-1, 1) * gene.mutation_scale
                chromosome[k] = float(np.clip(chromosome[k] + delta, gene.range_min, gene.range_max))
            elif gene.type == "int":
                delta = random.choice([-1, 1]) * random.randint(1, 3)
                chromosome[k] = int(np.clip(chromosome[k] + delta, gene.range_min, gene.range_max))
            elif gene.type == "choice":
                chromosome[k] = random.choice(gene.options)
    return chromosome


# ── Strategy from chromosome ──────────────────────────────────────────────


class GeneratedStrategy(BaseStrategy):
    def __init__(self, chromosome: dict, generation: int = 1, parent_fitness: float = 0.0):
        cfg = StrategyConfig(
            name=f"gen_{generation}",
            description=self._build_description(chromosome),
            params=chromosome,
        )
        super().__init__(cfg)
        self.chromosome = chromosome
        self.generation = generation
        self.parent_fitness = parent_fitness
        self._fitness: float | None = None

    @property
    def name(self) -> str:
        return self.config.name

        # Авто-регистрация в реестре (Федеративная архитектура)
        from src.domain.evolution.plugin_registry import PluginRegistry

        PluginRegistry().register(self)

    def _build_description(self, c: dict) -> str:
        parts = [
            f"conf={c['confidence_threshold']:.0f}",
            f"pos={c['position_size_pct']:.0f}%",
            f"regime={c['regime_filter']}",
            f"atr={c['atr_multiplier']:.1f}",
            f"mom={'Y' if c['use_momentum'] else 'N'}",
            f"rev={'Y' if c['use_mean_reversion'] else 'N'}",
            f"lb={c['lookback_fast']}/{c['lookback_slow']}",
        ]
        return " | ".join(parts)

    # ── ИСПРАВЛЕННЫЙ МЕТОД evaluate ────────────────────────────────────────
    def evaluate(self, market_data: dict) -> StrategyResult:
        c = self.chromosome
        signal_raw = market_data.get("signal_strength", 50.0)  # уже 0–100
        regime = market_data.get("regime", Regime.NEUTRAL_R)

        # Regime filter
        rf = c["regime_filter"]
        if rf == "BULL_ONLY" and regime != Regime.BULL:
            return StrategyResult(Signal.NEUTRAL, 0, "Regime filter: not bull market", regime)
        if rf == "BEAR_ONLY" and regime != Regime.BEAR:
            return StrategyResult(Signal.NEUTRAL, 0, "Regime filter: not bear market", regime)

        # Signal computation
        signal_strength = signal_raw
        momentum = market_data.get("momentum", 0.0)
        mean_reversion = market_data.get("mean_reversion_signal", 0.0)

        bullish_score = (signal_strength / 100.0) * c["signal_weights_bull"]
        bearish_score = ((100 - signal_strength) / 100.0) * c["signal_weights_bear"]

        if momentum > 0 and c["use_momentum"]:
            bullish_score += momentum * 0.2
        if mean_reversion > 0 and c["use_mean_reversion"]:
            bearish_score += mean_reversion * 0.15

        score = (bullish_score - bearish_score) * 100

        if score > c["confidence_threshold"]:
            signal = Signal.LONG
            conf = min(95.0, abs(score))
        elif score < -c["confidence_threshold"]:
            signal = Signal.SHORT
            conf = min(95.0, abs(score))
        else:
            signal = Signal.NEUTRAL
            conf = 50.0 - abs(score) * 0.5

        reasoning = (
            f"Generated strategy [{self.generation}]: "
            f"bullish={bullish_score:.2f} bearish={bearish_score:.2f} "
            f"momentum={momentum:.2f} rev={mean_reversion:.2f}"
        )

        return StrategyResult(
            signal=signal,
            confidence=int(conf),
            reasoning=reasoning,
            regime=regime,
            metadata={"chromosome": c, "score": score},
        )

    @property
    def fitness(self) -> float | None:
        return self._fitness

    def set_fitness(self, fitness: float):
        self._fitness = fitness

    # ── ATOM-META-RL-008: Serialization ────────────────────────────────

    def to_dict(self) -> dict:
        """Serialize GeneratedStrategy to a portable dict."""
        return {
            "chromosome": dict(self.chromosome),
            "generation": self.generation,
            "parent_fitness": self.parent_fitness,
            "config": {
                "name": self.config.name,
                "description": self.config.description,
                "version": getattr(self.config, "version", "1.0.0"),
                "enabled": self.config.enabled,
                "min_confidence": getattr(self.config, "min_confidence", 50.0),
                "max_position_pct": getattr(self.config, "max_position_pct", 25.0),
                "params": dict(self.config.params),
            },
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GeneratedStrategy":
        """Deserialize a dict back into a fully-functional GeneratedStrategy."""
        try:
            chromosome = d["chromosome"]
            generation = int(d.get("generation", 1))
            parent_fitness = float(d.get("parent_fitness", 0.0))

            cfg_dict = d.get("config", {})
            cfg = StrategyConfig(
                name=cfg_dict.get("name", f"loaded_gen_{generation}"),
                description=cfg_dict.get("description", ""),
                version=cfg_dict.get("version", "1.0.0"),
                enabled=cfg_dict.get("enabled", True),
                min_confidence=cfg_dict.get("min_confidence", 50.0),
                max_position_pct=cfg_dict.get("max_position_pct", 25.0),
                params=cfg_dict.get("params", {}),
            )

            strategy = cls(
                chromosome=chromosome,
                generation=generation,
                parent_fitness=parent_fitness,
            )
            strategy.config = cfg
            strategy._enabled = cfg.enabled
            return strategy

        except Exception:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"[META-RL-SERIAL] Failed to deserialize strategy, generating random: {d.get('generation', '?')}"
            )
            return cls(chromosome=random_chromosome(), generation=1, parent_fitness=0.0)


# ── Genetic Algorithm ──────────────────────────────────────────────────────


@dataclass
class GAPopulation:
    strategies: list[GeneratedStrategy]
    fitnesses: list[float]

    @property
    def best(self) -> tuple[BaseStrategy, float]:
        idx = int(np.argmax(self.fitnesses))
        return self.strategies[idx], self.fitnesses[idx]

    @property
    def avg_fitness(self) -> float:
        return float(np.mean(self.fitnesses))


def select_parents(population: GAPopulation, tournament_size: int = 3) -> tuple:
    strategies = list(zip(population.strategies, population.fitnesses, strict=False))
    selected = random.sample(strategies, min(tournament_size, len(strategies)))
    best = max(selected, key=lambda x: x[1])
    return best[0]


def evolve(
    population: list[GeneratedStrategy],
    fitness_fn,
    n_generations: int = 20,
    population_size: int = 20,
    elite_size: int = 3,
    mutation_rate: float = 0.20,
) -> list[GeneratedStrategy]:
    """Run genetic algorithm. Returns best strategies."""
    for i, s in enumerate(population):
        s.set_fitness(fitness_fn(s))

    fitnesses = [s.fitness for s in population]
    pop = GAPopulation(strategies=population, fitnesses=fitnesses)

    best_ever = pop.best
    history = [best_ever[1]]

    for gen in range(1, n_generations + 1):
        sorted_strategies = [
            s for s, f in sorted(zip(pop.strategies, pop.fitnesses, strict=False), key=lambda x: x[1], reverse=True)
        ]
        new_pop = list(sorted_strategies[:elite_size])
        current_gen = sorted_strategies[0].generation

        while len(new_pop) < population_size:
            a = select_parents(pop)
            b = select_parents(pop)
            child_chromosome = crossover(a.chromosome, b.chromosome)
            child_chromosome = mutate(child_chromosome, rate=mutation_rate)
            child = GeneratedStrategy(child_chromosome, generation=current_gen + 1, parent_fitness=a.fitness)
            new_pop.append(child)

        pop = GAPopulation(strategies=new_pop, fitnesses=[0.0] * len(new_pop))
        for s in pop.strategies:
            s.set_fitness(fitness_fn(s))
        pop.fitnesses = [s.fitness for s in pop.strategies]

        if pop.best[1] > best_ever[1]:
            best_ever = pop.best
        history.append(best_ever[1])

        if gen % 5 == 0 or gen == n_generations or pop.avg_fitness == pop.best[1]:
            print(
                f"  Gen {gen:3d}: avg={pop.avg_fitness:8.2f}  best={pop.best[1]:8.2f}  "
                f"spread={max(pop.fitnesses) - min(pop.fitnesses):8.2f}"
            )

    print(f"\n  Best strategy fitness: {best_ever[1]:.2f}")
    return [s for s, f in sorted(zip(pop.strategies, pop.fitnesses, strict=False), key=lambda x: x[1], reverse=True)]


def fitness_from_backtest(strategy: GeneratedStrategy, market_history: list) -> float:
    """Fitness = Sharpe ratio * win_rate - drawdown_penalty."""
    if not market_history:
        return 0.0

    equity = 100_000.0
    pos = 0.0
    entry_price = 0.0
    equity_curve = [equity]
    wins, losses, total = 0, 0, 0
    peak = equity
    max_dd = 0.0

    for bar in market_history:
        bar["regime"] = Regime(bar.get("regime", "NEUTRAL_R"))
        result = strategy.evaluate(bar)
        conf = strategy.chromosome["confidence_threshold"]

        if result.signal == Signal.LONG and result.confidence >= conf and pos == 0:
            pos = 1
            entry_price = bar["close"]
            equity -= bar["close"] * 0.001
        elif result.signal == Signal.SHORT and result.confidence >= conf and pos == 0:
            pos = -1
            entry_price = bar["close"]
            equity -= bar["close"] * 0.001
        elif result.signal == Signal.NEUTRAL and pos != 0:
            pnl = (bar["close"] - entry_price) * pos * 0.001
            equity += pnl
            if pnl > 0:
                wins += 1
            else:
                losses += 1
            total += 1
            pos = 0.0

        equity_curve.append(equity)
        peak = max(peak, equity)
        dd = (peak - equity) / peak if peak > 0 else 0
        max_dd = max(max_dd, dd)

    if pos != 0:
        pnl = (market_history[-1]["close"] - entry_price) * pos * 0.001
        equity += pnl
        if pnl > 0:
            wins += 1
        else:
            losses += 1
        total += 1

    total_return = (equity - 100_000.0) / 100_000.0
    win_rate = wins / max(1, total)
    sharpe = total_return / max(0.01, max_dd + 0.001) if total_return > 0 else -max_dd * 5

    fitness = sharpe * win_rate * 100 - max_dd * 50
    return max(-500.0, fitness)


def generate_synthetic_history(n_days: int = 252) -> list:
    """Generate synthetic market history with proper OHLCV bars for backtesting."""
    history = []
    price = 50_000.0
    regime = Regime.NEUTRAL_R

    for i in range(n_days):
        regimes = [Regime.BULL, Regime.BEAR, Regime.NEUTRAL_R, Regime.VOLATILE]
        regime = random.choice(regimes)

        drift = {"BULL": 0.001, "BEAR": -0.0008, "NEUTRAL": 0.0001, "VOLATILE": 0.0002}[regime.value]
        vol = {"BULL": 0.015, "BEAR": 0.018, "NEUTRAL": 0.010, "VOLATILE": 0.030}[regime.value]

        ret = np.random.normal(drift, vol)
        open_price = price
        close_price = price * (1 + ret)
        high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, vol / 2)))
        low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, vol / 2)))
        volume = np.random.uniform(1000, 5000)

        price = close_price

        mom = np.random.uniform(-0.1, 0.1) + (0.05 if regime == Regime.BULL else -0.05)
        mr = np.random.uniform(-0.05, 0.05)

        signal_base = 50.0 + (25.0 if regime == Regime.BULL else -20.0 if regime == Regime.BEAR else 0.0)
        history.append(
            {
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume,
                "regime": regime,
                "signal_strength": signal_base + np.random.uniform(-15, 15),
                "momentum": mom + (0.08 if regime == Regime.BULL else -0.06 if regime == Regime.BEAR else 0),
                "mean_reversion_signal": mr,
                "atr": close_price * 0.02,
                "timestamp": i,
            }
        )

    return history


def run_meta_rl(n_generations: int = 25, population_size: int = 20) -> list[GeneratedStrategy]:
    """Run the full Meta-RL pipeline."""
    print("=" * 60)
    print("ATOM-STEP-11: META-RL AUTO-STRATEGY")
    print("=" * 60)
    print(f"  Population: {population_size}  Generations: {n_generations}")

    population = [GeneratedStrategy(random_chromosome()) for _ in range(population_size)]
    history = generate_synthetic_history(252)

    def fitness_fn(s):
        return fitness_from_backtest(s, history)

    print("\n  Evolving strategies...\n")
    best_strategies = evolve(population, fitness_fn, n_generations, population_size)

    print("\n  Top 3 strategies:")
    for i, s in enumerate(best_strategies[:3], 1):
        c = s.chromosome
        print(
            f"    {i}. Fitness={s.fitness:.2f} | "
            f"conf={c['confidence_threshold']:.0f} pos={c['position_size_pct']:.0f}% "
            f"regime={c['regime_filter']} atr={c['atr_multiplier']:.1f} "
            f"mom={'Y' if c['use_momentum'] else 'N'}"
        )

    return best_strategies


if __name__ == "__main__":
    top = run_meta_rl(n_generations=25, population_size=20)
    print(f"\n  Saved {len(top)} strategies to strategies/")
