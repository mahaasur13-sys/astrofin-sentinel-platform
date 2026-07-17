# A/B Testing — ATOM-META-RL-012

## Overview

`meta_rl/ab_testing.py` implements statistical A/B testing for comparing two strategy versions (generations) using Welch's t-test and Cohen's d effect size.

## Key Functions

### Statistical Tests

- **`welch_t_test(a, b)`** — Welch's t-test (pure numpy; scipy fallback if available). Returns `(t_stat, p_value)`.
- **`cohens_d(a, b)`** — Effect size. Values: `|d| > 0.8` LARGE, `> 0.5` MEDIUM, `> 0.2` SMALL.

### Main Class: `ABTestRunner`

```python
runner = ABTestRunner(config=ABTestConfig(
    n_samples=100,
    p_value_thresh=0.05,
    min_samples=10,
))
result = runner.compare_versions("gen_5", "gen_6", market_data_a={...}, market_data_b={...})
```

### Iteration Over All Chromosomes

Each version (gen) may contain multiple chromosomes. `_run_test` iterates over **all** chromosomes in each version list:

```python
for chrom_list, mdata, out_list in [
    (chrom_a, mda, ma),
    (chrom_b, mdb, mb),
]:
    if not chrom_list:
        continue
    for chrom in chrom_list:          # ← all chromosomes, not just first
        best = chrom.get("chromosomes", [{}])[0]
        strat = GeneratedStrategy(best, generation=0)
        res = ev.evaluate(strat, mdata)
        reward = getattr(res, "risk_adjusted_pnl", getattr(res, "pnl", 0.0))
        out_list.append(reward)
```

This ensures the full chromosome list is evaluated, not just the first item.

### Result Interpretation

| `winner` | Meaning |
|----------|---------|
| `A` | Version A statistically better (p < 0.05) |
| `B` | Version B statistically better (p < 0.05) |
| `NO_WINNER` | p ≥ 0.05 — no significant difference |
| `INSUFFICIENT_DATA` | Not enough samples to decide |

### Confidence Levels

| p-value | Confidence |
|---------|------------|
| < 0.01 | HIGH |
| < 0.05 | MEDIUM |
| ≥ 0.05 | LOW |
| N/A | NONE (insufficient data) |

## Usage Example

```python
from meta_rl.ab_testing import ABTestRunner, ABTestConfig

runner = ABTestRunner()
result = runner.compare_versions(
    version_a="gen_5",
    version_b="gen_6",
    market_data_a={"BTCUSDT": price_series_a},
    market_data_b={"BTCUSDT": price_series_b},
)
print(result.summary())
# [META-RL-AB] gen_5 vs gen_6: winner=B p=0.0231 d=0.631(MEDIUM) d_mean%=+12.34 conf=MEDIUM
```
