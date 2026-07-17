"""ROMA SaaS Pricing Engine — Dynamic GPU compute pricing."""

from dataclasses import dataclass
from typing import Dict, Any
from enum import Enum


class PricingTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# GPU_RATE: sell price per GPU-second (at base tier)
GPU_RATES = {
    "RTX3060": 0.000055,  # $0.20/hr sell
    "RTX4090": 0.000139,  # $0.50/hr sell
    "A100": 0.000555,  # $2.00/hr sell
    "H100": 0.001389,  # $5.00/hr sell
}

# GPU_COST: what WE pay per GPU-second (our cost basis)
GPU_COST = {
    "RTX3060": 0.000028,  # $0.10/hr cost
    "RTX4090": 0.000050,  # $0.18/hr cost
    "A100": 0.000250,  # $0.90/hr cost
    "H100": 0.000833,  # $3.00/hr cost
}

# Tier multipliers applied to base GPU rate
TIER_MULT = {
    PricingTier.FREE: 0.0,  # free tier: no charge
    PricingTier.PRO: 1.0,  # base rate
    PricingTier.ENTERPRISE: 2.5,  # premium SLA multiplier
}

# Monthly subscription base price
TIER_MONTHLY = {PricingTier.FREE: 0, PricingTier.PRO: 25, PricingTier.ENTERPRISE: 250}

# Monthly GPU-second quota per tier
TIER_QUOTA = {
    PricingTier.FREE: 3600,
    PricingTier.PRO: 180000,
    PricingTier.ENTERPRISE: 3600000,
}


# Load-based pricing multipliers
def load_mult(cluster_load: float) -> float:
    if cluster_load < 0.3:
        return 0.8  # idle: 20% off
    if cluster_load < 0.7:
        return 1.0  # normal
    if cluster_load < 0.9:
        return 1.5  # peak: 50% premium
    return 2.0  # saturated: 2×


# Region multipliers
REGION_MULT = {"us-east": 1.0, "eu-west": 1.2, "apac": 1.4}


@dataclass
class PriceQuote:
    gpu_seconds: float
    gpu_model: str
    tier: str
    base_cost: float
    load_mult: float
    region_mult: float
    total_cost: float
    currency: str = "USD"
    breakdown: Dict = None
    estimated_hours: float = 0.0


class PricingEngine:
    def quote(
        self,
        gpu_seconds,
        gpu_model="RTX4090",
        tier="pro",
        region_mult=1.0,
        cluster_load=0.5,
    ):
        gpu_rate = GPU_RATES.get(gpu_model, GPU_RATES["RTX4090"])
        tier_mult = TIER_MULT.get(PricingTier(tier), 1.0)
        lm = load_mult(cluster_load)
        # Free tier: quota only, no per-use charge
        if tier_mult == 0:
            return PriceQuote(
                gpu_seconds=gpu_seconds,
                gpu_model=gpu_model,
                tier=tier,
                base_cost=0.0,
                load_mult=lm,
                region_mult=region_mult,
                total_cost=0.0,
                breakdown={
                    "tier": tier,
                    "quota_free": True,
                    "monthly_quota_hrs": TIER_QUOTA.get(PricingTier(tier), 0) // 3600,
                    "gpu_per_hour": gpu_rate * 3600,
                },
                estimated_hours=gpu_seconds / 3600,
            )
        rate = gpu_rate * tier_mult * lm * region_mult
        total = gpu_seconds * rate
        return PriceQuote(
            gpu_seconds=gpu_seconds,
            gpu_model=gpu_model,
            tier=tier,
            base_cost=gpu_seconds * gpu_rate,
            load_mult=lm,
            region_mult=region_mult,
            total_cost=total,
            breakdown={
                "gpu_rate": gpu_rate,
                "tier_mult": tier_mult,
                "region_mult": region_mult,
                "load_mult": lm,
                "effective_rate": rate,
                "gpu_per_hour": rate * 3600,
                "monthly_quota_hrs": TIER_QUOTA.get(PricingTier(tier), 0) // 3600,
                "tier_monthly": TIER_MONTHLY.get(PricingTier(tier), 0),
            },
            estimated_hours=gpu_seconds / 3600,
        )


class ProfitCalculator:
    def __init__(self):
        self.cost_table = GPU_COST

    def margin(self, quote: PriceQuote) -> Dict[str, Any]:
        cost_per_sec = self.cost_table.get(quote.gpu_model, GPU_COST["RTX4090"])
        our_cost = quote.gpu_seconds * cost_per_sec
        rev = quote.total_cost
        profit = rev - our_cost
        gpm = (profit / rev * 100) if rev > 0 else 0
        return {
            "revenue": round(rev, 4),
            "cost": round(our_cost, 4),
            "profit": round(profit, 4),
            "GPM": round(gpm, 1),
            "markup": round(rev / our_cost, 2) if our_cost > 0 else 0,
        }


if __name__ == "__main__":
    pe = PricingEngine()
    pc = ProfitCalculator()
    print("=== ROMA GPU Pricing ===\n")
    print("-- GPU Sell Rates --")
    for g, rate in GPU_RATES.items():
        cost = GPU_COST[g]
        m = (rate - cost) / rate * 100
        print(
            f"  {g:8s}: sell=${rate*3600:.2f}/hr | cost=${cost*3600:.2f}/hr | GPM={m:.0f}%"
        )
    print("\n-- Tier Impact (RTX4090, 1hr) --")
    for t in ["free", "pro", "enterprise"]:
        q = pe.quote(3600, "RTX4090", t)
        print(
            f"  {t:12s}: {q.estimated_hours:.1f}hr = ${q.total_cost:.4f} | quota={q.breakdown['monthly_quota_hrs']}hr"
        )
    print("\n-- Load Impact (RTX4090, 1hr) --")
    for lbl, lv in [
        ("idle", 0.1),
        ("normal", 0.5),
        ("peak", 0.85),
        ("saturated", 0.97),
    ]:
        q = pe.quote(3600, "RTX4090", cluster_load=lv)
        print(f"  {lbl:12s}: ${q.total_cost:.4f} (×{q.load_mult})")
    print("\n-- Profitability (RTX4090, 10hr = 36000s) --")
    for g in ["RTX3060", "RTX4090", "A100", "H100"]:
        q = pe.quote(36000, g)
        m = pc.margin(q)
        print(
            f"  {g:8s}: rev=${m['revenue']:.4f} | cost=${m['cost']:.4f} | profit=${m['profit']:.4f} | GPM={m['GPM']:.1f}% | markup={m['markup']}×"
        )
    print("\n-- Full Quote Example (A100 PRO, 2hr, peak load) --")
    q = pe.quote(7200, "A100", "pro", cluster_load=0.85)
    m = pc.margin(q)
    print(
        f"  Cost: ${q.total_cost:.4f} | Profit: ${m['profit']:.4f} | GPM={m['GPM']:.1f}%"
    )
    print(
        f"  Breakdown: ${q.breakdown['gpu_rate']}/s × {q.breakdown['tier_mult']} × {q.breakdown['load_mult']} = ${q.breakdown['gpu_per_hour']:.4f}/hr"
    )
