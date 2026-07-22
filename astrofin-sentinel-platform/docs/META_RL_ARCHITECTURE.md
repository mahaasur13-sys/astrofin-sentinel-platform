# Meta-RL Subsystem — Architecture

> **Audience:** engineers joining AstroFin Sentinel V5 who need to understand how strategies are born, evaluated, evolved, and validated.
> **Scope:** everything under `meta_rl/` (reward, evolution, walk-forward, persistence, ranking, A/B).
> **See also:** [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) for the top-level system context.

---

## 1. Mission

The Meta-RL subsystem **automatically generates, scores, evolves, and validates** trading strategies on top of the multi-agent ensemble. It is the "learning loop" of AstroFin Sentinel V5 — every loop iteration asks: *"given what worked last time, what should we try next?"*

Three invariants govern the design:

| ID | Invariant | Why |
|---|---|---|
| **ATOM-META-RL-004** | Reward is a function of **risk-adjusted** metrics only — never raw PnL. | Prevents overfitting to lucky windows. |
| **ATOM-META-RL-007** | Walk-forward validation gates every elite that graduates to live. | In-sample overfit strategies cannot reach production. |
| **ATOM-META-RL-009** | Evolution is **deterministic given a seed** — replay returns the same populations. | Auditability and bug reproduction. |

---

## 2. Pipeline at a glance

```mermaid
flowchart TB
    subgraph Inputs
        A[MetaAgent + market_data]
    end

    subgraph Generation
        A --> B[HyperOptimizer warm-up: 10 trials]
        B --> C[Initial Population: N strategies]
    end

    subgraph Loop[Per generation g = 1..G]
        C --> D[Evaluate: backtest → EvaluationResult]
        D --> E[RewardCalculator: risk-adjusted scalar]
        E --> F[Rank + Diversity Filter (NN-based)]
        F --> G{WF enabled?}
        G -- yes --> H[WalkForwardValidator: K splits]
        G -- no --> I[Score = reward]
        H --> I
        I --> J{Elite? top-N}
        J -- yes --> K[StrategyPool.add + A/B]
        J -- no --> L[Reproduce: crossover + mutation]
        L --> M[Next Generation]
        K --> M
        M --> N{Early stop? patience or alpha-decay}
        N -- no --> D
    end

    O[Best Strategy + lineage]
    P[A/B Test: live vs control]
    N -- yes --> O
    K --> P
```

---

## 3. Reward function

`meta_rl/reward.py::RewardCalculator.compute(result)` returns a scalar in roughly `[−2, +2]`.

```
reward = base
      + w_sharpe   * squashed(sharpe)            # logistic, capped
      + w_pnl      * normalize(risk_adj_pnl)
      - dd_penalty(adj_drawdown)                 # quadratic
      - w_exec     * clip(execution_cost, 0, 1)
      + stability_bonus(win_rate, n_trades)      # saturating
      - hard_dd_ceiling(adj_dd > soft_max)      # extra per unit
```

Key design choices (see `RewardConfig` for all knobs):

- **Sharpe** goes through `tanh(k*sharpe)` so a Sharpe of 5 does not dominate one of 1.5.
- **Drawdown** is quadratic (not linear) because convex penalties match investor pain asymmetry.
- **`compute()` never raises.** Any unexpected exception returns `base_reward` and logs at WARNING — a failed reward must not kill the loop.
- **Safety short-circuits** (insufficient trades, NaN, etc.) short-circuit to `base_reward`.

---

## 4. Evolution cycle

`meta_rl/evolution.py::EvolutionEngine.run(ensemble_seeds=3)` is the top-level entry.

| # | Phase | What happens | Source |
|---|---|---|---|
| 0 | Warm-up | `HyperOptimizer.optimize(n_trials=10)` adjusts `population_size`, `mutation_rate`, `crossover_rate` | `meta_rl/hyperopt.py` |
| 1 | Init | Seed `ensemble_seeds` independent populations from `MetaAgent` | `evolution.run` |
| 2 | Evaluate | Each strategy → `BacktestAdapter.run` → `EvaluationResult` | `meta_rl/backtest_adapter.py` |
| 3 | Score | `RewardCalculator.compute` | `meta_rl/reward.py` |
| 4 | Rank | Score + diversity penalty (NN-based filter) | `meta_rl/ranking.py`, `meta_rl/strategy_pool.py::diversity_filter` |
| 5 | Reproduce | Tournament selection → crossover → mutation → fill next gen | `meta_rl/strategy.py` |
| 6 | Walk-forward | For elites, refit on rolling windows and aggregate OOS score | `meta_rl/walkforward.py` |
| 7 | Stop check | Early stop on patience, or alpha-decay detector | `evolution._should_stop`, `_check_alpha_decay` |
| 8 | Persist | Save generation snapshot, lineage, visualizations | `evolution._save_generation`, `evolution._generate_visualizations` |

**Early stop** triggers when:
- Best reward has not improved for `early_stopping_patience` generations, **or**
- Alpha-decay detector (`evolution._check_alpha_decay`) detects an OOS→IS reward collapse (suggests regime change).

---

## 5. Walk-forward validation

`meta_rl/walkforward.py::WalkForwardValidator.validate(strategy, data)` is the **gate** for live promotion.

Default config (overridable per engine):

| Param | Default | Meaning |
|---|---|---|
| `n_splits` | 5 | Number of rolling-origin train/test windows |
| `train_window` | 100 | Bars used to fit |
| `test_window` | 20 | Bars held out for OOS scoring |
| `embargo` | 1 | Gap between train end and test start (anti-leak) |
| `aggregate` | `"mean"` | How to combine OOS scores: `mean` / `median` / `min` |

Output: `WalkForwardReport` with `splits: list[SplitMetrics]` and `summary()`. The aggregate OOS score is what `StrategyPool.add` compares against the in-sample reward — if OOS drops > 30%, the strategy is **rejected for live** even if it tops the leaderboard.

`run_walkforward_on_elites(...)` is the convenience wrapper used by `evolution.run` to validate the top-N from each generation in one pass.

---

## 6. Strategy pool & diversity

`meta_rl/strategy_pool.py::StrategyPool` is the persistent store of validated strategies.

Two design choices worth knowing:

1. **Diversity via NearestNeighbors (R7.1).** `diversity_filter` builds one `sklearn.neighbors.NearestNeighbors` index over the existing population's chromosome vectors, then queries each candidate's max cosine similarity. O(n·log n) instead of the prior O(n²) Python loop. Falls back to the legacy O(n*m) implementation if sklearn is missing — never blocks the loop.
2. **Cached chromosome hash (R7.2).** `ScoredStrategy.__slots__` includes `_chromosome_hash` (SHA256-prefix of the JSON-serialized chromosome), computed once in `__init__`. Equality and hashing still use UUID, but lineage export and audit logs now use the stable hash.

Downsampling (R7.4): equity curves longer than `max_points=1000` are bucket-averaged before persistence.

---

## 7. Persistence & replay

`meta_rl/persistence.py` and `meta_rl/versions_storage.py` write:

- `evolution_<session_id>.json` — full generation-by-generation snapshot.
- `strategies/<strategy_id>/` — chromosome, lineage, equity curve, walk-forward report.
- `visualizations/<generation>/` — Plotly HTMLs.

Replay (`meta_rl/replay.py::EvolutionReplay`) reads the snapshot and reconstructs the populations deterministically given the same seed — this is how we audit "why did strategy X come out?".

---

## 8. A/B testing (bridge to live)

`meta_rl/ab_testing.py` arms two strategies (control = current live, variant = new candidate) and tracks:

- Cumulative reward delta
- Drawdown divergence
- Statistical significance (Welch's t-test on per-trade PnL)

Promote to live only when **significance < 0.05 AND no drawdown regression > 20%**. See `docs/ab_testing.md` for the full protocol.

---

## 9. Reproducibility checklist

For a new engineer to reproduce a run:

```bash
# 1. Install (editable, pinned)
pip install -e .

# 2. Verify the dependency lock matches your commit
python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])"

# 3. Run with a fixed seed
PYTHONHASHSEED=0 astrofin evolve --seed 42 --market BTCUSDT --out runs/repro/

# 4. Replay
astrofin replay runs/repro/evolution_<sid>.json --verify
```

If steps 3 and 4 produce the **same** `best_strategy.chromosome_hash`, reproducibility holds (invariant ATOM-META-RL-009).

---

## 10. Where to read next

| Topic | File |
|---|---|
| Top-level system | `docs/ARCHITECTURE.md` |
| A/B testing protocol | `docs/ab_testing.md` |
| Reward config knobs | `meta_rl/reward.py::RewardConfig` |
| Multi-agent design | `docs/mas_design.md` |
| Phase 5 lag-window integration | `docs/phase5_lag_window_integration.md` |
