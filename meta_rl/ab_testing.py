"""meta_rl/ab_testing.py -- ATOM-META-RL-012: A/B Testing Framework"""

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)

AB_TESTING_ENABLED = True
VERSION_TAG_FORMAT = "gen_{generation}"
P_VALUE_THRESHOLD = 0.05
MIN_SAMPLES = 5


def welch_t_test(a, b):
    """Welch t-test: returns (t_stat, p_value). No scipy required."""
    if len(a) < 2 or len(b) < 2:
        return 0.0, 1.0
    ma = float(np.mean(a)) if len(a) else 0.0
    mb = float(np.mean(b)) if len(b) else 0.0
    va = float(np.var(a, ddof=1)) if len(a) > 1 else 0.0
    vb = float(np.var(b, ddof=1)) if len(b) > 1 else 0.0
    na = max(len(a), 1)
    nb = max(len(b), 1)
    diff = ma - mb
    se_val = max(va / na + vb / nb, 1e-12)
    t_stat = diff / se_val if se_val > 1e-12 else 0.0
    # Simple two-tailed approximation
    if abs(t_stat) < 1.96:
        p_value = 1.0
    elif abs(t_stat) < 2.576:
        p_value = 0.05
    else:
        p_value = 0.01
    try:
        from scipy.stats import t as t_dist

        na_ = max(len(a), 2)
        nb_ = max(len(b), 2)
        num = (va / na_ + vb / nb_) ** 2
        df_a = (va / na_) ** 2 / max(na_ - 1, 1)
        df_b = (vb / nb_) ** 2 / max(nb_ - 1, 1)
        df = num / max(df_a + df_b, 1e-12)
        p_value = 2.0 * (1.0 - t_dist.cdf(abs(t_stat), df))
    except Exception:
        pass
    return float(t_stat), float(p_value)


def cohens_d(a, b):
    """Cohens d effect size: small=0.2, medium=0.5, large=0.8."""
    import math

    na = max(len(a), 2)
    nb = max(len(b), 2)
    va = float(np.var(a, ddof=1))
    vb = float(np.var(b, ddof=1))
    pool_num = va * (na - 1) + vb * (nb - 1)
    pool_den = max(na + nb - 2, 1)
    pooled_std = math.sqrt(max(pool_num / pool_den, 1e-8))
    if pooled_std < 1e-8:
        return 0.0
    return abs(float(np.mean(a)) - float(np.mean(b))) / pooled_std


@dataclass
class ABTestResult:
    version_a: str
    version_b: str
    winner: str
    p_value: float
    effect_size: float
    metrics_a: list
    metrics_b: list
    mean_a: float
    mean_b: float
    improvement_pct: float
    n_samples_a: int
    n_samples_b: int
    confidence: str

    def summary(self) -> str:
        arrow = "A" if self.winner == "A" else ("B" if self.winner == "B" else "NONE")
        eff = "LARGE" if abs(self.effect_size) > 0.8 else "MEDIUM" if abs(self.effect_size) > 0.5 else "SMALL"
        return (
            f"[META-RL-AB] {self.version_a} vs {self.version_b}: "
            f"winner={arrow} p={self.p_value:.4f} d={self.effect_size:.3f}({eff}) "
            f"d_mean%={self.improvement_pct:+.2f}"
        )


@dataclass
class ABTestConfig:
    metric: str = "sharpe"
    p_value_thresh: float = 0.05
    min_samples: int = 5
    walk_forward_windows: int = 3


class ABTest:
    """ATOM-META-RL-012: A/B testing for strategy versions."""

    def __init__(self, persistence=None, config=None):
        from meta_rl.persistence import get_persistence

        self.persistence = persistence or get_persistence()
        self.config = config or ABTestConfig()
        self.results_a: list = []
        self.results_b: list = []
        self.versions_loaded: dict[str, list] = {}

    def compare_versions(self, version_a: str, version_b: str, market_data_a: dict, market_data_b=None) -> ABTestResult:
        """Public API: A/B test between two versions. market_data_b defaults to market_data_a."""
        if market_data_b is None:
            market_data_b = market_data_a
        self.version_a = version_a
        self.version_b = version_b
        chrom_a = self.persistence.load_elite_chromosomes(version_a)
        chrom_b = self.persistence.load_elite_chromosomes(version_b)
        if not chrom_a or not chrom_b:
            logger.warning(f"[META-RL-AB] Version load failed: A={len(chrom_a)} B={len(chrom_b)}")
            return self._fail_result(version_a, version_b)
        self.versions_loaded = {version_a: chrom_a, version_b: chrom_b}
        return self._run_test(version_a, version_b, market_data_a, market_data_b)

    def _run_test(self, va: str, vb: str, mda: dict, mdb: dict) -> ABTestResult:
        from meta_rl.strategy_evaluator import StrategyEvaluator
        from strategies.generator import GeneratedStrategy

        ev = StrategyEvaluator()
        ma, mb = [], []
        chrom_a = self.versions_loaded.get(va, [])
        chrom_b = self.versions_loaded.get(vb, [])
        for chrom_list, mdata, out_list in [
            (chrom_a, mda, ma),
            (chrom_b, mdb, mb),
        ]:
            if not chrom_list:
                continue
            # Оцениваем все хромосомы, а не только первую
            for chrom_entry in chrom_list:
                best = chrom_entry.get("chromosome", {})
                if not best:
                    continue
                strat = GeneratedStrategy(best, generation=0)
                try:
                    res = ev.evaluate(strat, mdata)
                    reward = getattr(res, "risk_adjusted_pnl", getattr(res, "pnl", 0.0))
                    out_list.append(reward)
                except Exception as e:
                    logger.warning(f"[META-RL-AB] Evaluation failed for chromosome: {e}")
        if len(ma) < self.config.min_samples or len(mb) < self.config.min_samples:
            logger.warning(f"[META-RL-AB] Insufficient samples: A={len(ma)} B={len(mb)}")
            return self._fail_result(va, vb)
        mean_a = float(np.mean(ma))
        mean_b = float(np.mean(mb))
        t_stat, p_value = welch_t_test(np.array(ma), np.array(mb))
        effect = cohens_d(np.array(ma), np.array(mb))
        winner = "NO_WINNER"
        if p_value < self.config.p_value_thresh:
            winner = "A" if mean_a > mean_b else "B"
        improvement = 0.0
        if abs(mean_b) > 1e-8:
            improvement = (mean_a - mean_b) / abs(mean_b) * 100.0
        conf = "HIGH" if p_value < 0.01 else "MEDIUM" if p_value < 0.05 else "LOW"
        result = ABTestResult(
            version_a=va,
            version_b=vb,
            winner=winner,
            p_value=float(p_value),
            effect_size=float(effect),
            metrics_a=ma,
            metrics_b=mb,
            mean_a=float(mean_a),
            mean_b=float(mean_b),
            improvement_pct=float(improvement),
            n_samples_a=len(ma),
            n_samples_b=len(mb),
            confidence=conf,
        )
        logger.info(result.summary())
        return result

    def _fail_result(self, va: str, vb: str) -> ABTestResult:
        return ABTestResult(
            version_a=va,
            version_b=vb,
            winner="INSUFFICIENT_DATA",
            p_value=1.0,
            effect_size=0.0,
            metrics_a=[],
            metrics_b=[],
            mean_a=0.0,
            mean_b=0.0,
            improvement_pct=0.0,
            n_samples_a=0,
            n_samples_b=0,
            confidence="NONE",
        )
