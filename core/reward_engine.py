"""
core/reward_engine.py — ATOM-STEP-6: Reward Engine for Online RL
===============================================================
Computes trading rewards from market outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TradeOutcome:
    entry_price: float
    exit_price: float
    position_pct: float
    direction: str  # "LONG" or "SHORT"
    hold_duration_hours: float
    pnl_pct: float
    outcome_type: str  # "profit", "loss", "breakeven"


@dataclass
class RewardSignal:
    total_reward: float
    pnl_reward: float
    astro_bonus: float
    risk_penalty: float
    uncertainty_penalty: float
    metadata: dict


class RewardEngine:
    """
    Computes reward = PnL + AstroBonus - RiskPenalty - UncertaintyPenalty
    AstroBonus: if astro_alignment > 0 → positive reward multiplier
    RiskPenalty: penalizes oversized positions
    UncertaintyPenalty: penalizes high uncertainty estimates
    """

    def __init__(
        self,
        astro_weight: float = 0.15,
        risk_penalty_scale: float = 1.0,
        uncertainty_penalty_scale: float = 0.5,
    ):
        self.astro_weight = astro_weight
        self.risk_penalty_scale = risk_penalty_scale
        self.uncertainty_penalty_scale = uncertainty_penalty_scale

    def compute_reward(
        self,
        outcome: TradeOutcome,
        astro_alignment: float = 0.0,  # -1 to +1
        uncertainty: float = 0.0,  # 0 to 1
    ) -> RewardSignal:
        """Compute composite reward from trade outcome + astro factors."""
        pnl = outcome.pnl_pct
        position_pct = abs(outcome.position_pct)

        # Base PnL reward (signed — can be negative)
        pnl_reward = pnl * 100.0  # Scale to percentage points

        # Astro alignment bonus
        # astro_alignment in [-1, +1]: positive aligns with signal direction
        # Use it as a multiplier that can boost or slightly reduce reward
        astro_bonus = self.astro_weight * astro_alignment * abs(pnl_reward)

        # Risk penalty — penalize large positions (position_pct is fraction)
        risk_penalty = self.risk_penalty_scale * (position_pct**2) * abs(pnl_reward)

        # Uncertainty penalty — penalize acting under high uncertainty
        uncertainty_penalty = self.uncertainty_penalty_scale * uncertainty * abs(pnl_reward)

        total_reward = pnl_reward + astro_bonus - risk_penalty - uncertainty_penalty

        return RewardSignal(
            total_reward=total_reward,
            pnl_reward=pnl_reward,
            astro_bonus=astro_bonus,
            risk_penalty=risk_penalty,
            uncertainty_penalty=uncertainty_penalty,
            metadata={
                "astro_alignment": astro_alignment,
                "uncertainty": uncertainty,
                "position_pct": position_pct,
                "outcome_type": outcome.outcome_type,
                "pnl_pct": pnl,
            },
        )

    def batch_compute(
        self,
        outcomes: list[TradeOutcome],
        astro_alignments: list[float],
        uncertainties: list[float],
    ) -> list[RewardSignal]:
        """Compute rewards for a batch of trades."""
        return [
            self.compute_reward(o, a, u) for o, a, u in zip(outcomes, astro_alignments, uncertainties, strict=False)
        ]

    def discounted_reward(self, rewards: list[RewardSignal], gamma: float = 0.95) -> float:
        """Compute discounted cumulative reward."""
        total = 0.0
        for r in rewards:
            total = total * gamma + r.total_reward
        return total

    def summary_stats(self, rewards: list[RewardSignal]) -> dict:
        """Compute summary statistics from a list of rewards."""
        if not rewards:
            return {}
        total_rewards = [r.total_reward for r in rewards]
        pnl_rewards = [r.pnl_reward for r in rewards]
        return {
            "count": len(rewards),
            "mean_total": sum(total_rewards) / len(total_rewards),
            "sum_total": sum(total_rewards),
            "mean_pnl": sum(pnl_rewards) / len(pnl_rewards),
            "positive_count": sum(1 for r in total_rewards if r > 0),
            "negative_count": sum(1 for r in total_rewards if r < 0),
            "total_astro_bonus": sum(r.astro_bonus for r in rewards),
            "total_risk_penalty": sum(r.risk_penalty for r in rewards),
            "total_uncertainty_penalty": sum(r.uncertainty_penalty for r in rewards),
        }


if __name__ == "__main__":
    engine = RewardEngine()
    outcomes = [
        TradeOutcome(
            entry_price=100,
            exit_price=105,
            position_pct=0.1,
            direction="LONG",
            hold_duration_hours=24,
            pnl_pct=5.0,
            outcome_type="profit",
        ),
        TradeOutcome(
            entry_price=100,
            exit_price=98,
            position_pct=0.05,
            direction="SHORT",
            hold_duration_hours=12,
            pnl_pct=-2.0,
            outcome_type="loss",
        ),
    ]
    astro_alignments = [0.7, -0.3]
    uncertainties = [0.2, 0.6]
    rewards = engine.batch_compute(outcomes, astro_alignments, uncertainties)
    for i, r in enumerate(rewards):
        print(
            f"Trade {i + 1}: reward={r.total_reward:.4f}  pnl={r.pnl_reward:.4f}  astro={r.astro_bonus:.4f}  risk={r.risk_penalty:.4f}  unc={r.uncertainty_penalty:.4f}"
        )
    stats = engine.summary_stats(rewards)
    print(f"\nSummary: {stats}")
    print(f"Discounted (γ=0.95): {engine.discounted_reward(rewards):.4f}")
