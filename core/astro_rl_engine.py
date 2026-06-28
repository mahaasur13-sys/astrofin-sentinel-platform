"""core/astro_rl_engine.py - ATOM-STEP-6: Astro RL Engine"""

from __future__ import annotations

import sys as _sys

_sys.path.insert(0, "")
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class AstroState:
    timestamp: datetime
    jd: float
    moon_longitude: float
    jupiter_longitude: float
    saturn_longitude: float
    moon_phase: float
    retrograde_mask: str
    nakshatra: int
    choghadiya: str
    state_hash: str = ""

    def __post_init__(self):
        if not self.state_hash:
            self.state_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        data = f"{self.timestamp.isoformat()}:{self.jd:.4f}:{self.moon_longitude:.2f}:{self.jupiter_longitude:.2f}:{self.saturn_longitude:.2f}"  # noqa: E501
        return hashlib.md5(data.encode()).hexdigest()[:8]


@dataclass
class AstroRLConfig:
    rebalance_interval_hours: int = 24
    min_astro_score: float = 0.45
    astro_weight: float = 0.15
    uncertainty_penalty_scale: float = 0.5
    risk_penalty_scale: float = 1.0
    learning_rate: float = 0.01
    gamma: float = 0.95


class AstroRLLoop:
    def __init__(self, config=None, reward_engine=None, trainer=None):
        self.config = config or AstroRLConfig()
        self.reward_engine = reward_engine
        self.trainer = trainer
        self.current_state = None
        self.experience_log = []
        self._state_history = []

    def observe(self, astro_state):
        self.current_state = astro_state
        self._state_history.append(astro_state)
        return {
            "state_hash": astro_state.state_hash,
            "moon_longitude": astro_state.moon_longitude,
            "nakshatra": astro_state.nakshatra,
            "choghadiya": astro_state.choghadiya,
        }

    def compute_alignment(self, signal_direction):
        if self.current_state is None:
            return 0.0
        moon, jup, sat = (
            self.current_state.moon_longitude,
            self.current_state.jupiter_longitude,
            self.current_state.saturn_longitude,
        )
        raw = (
            (1.0 if 0 <= moon <= 180 else -1.0) * 0.4
            + (1.0 if not (90 <= jup <= 270) else -0.5) * 0.3
            + (1.0 if (30 <= sat <= 60 or 150 <= sat <= 180 or 300 <= sat <= 330) else -0.5) * 0.3
            + (-0.3 if "M" in self.current_state.retrograde_mask else 0.0)
        )
        return max(-1.0, min(1.0, raw))

    def decide(self, signal_strength, uncertainty, regime="NORMAL"):
        if self.current_state is None:
            return {"position_pct": 0.0, "reason": "no_state"}
        alignment = self.compute_alignment("LONG")
        if not hasattr(self, "trainer") or self.trainer is None:
            pos = self.config.min_astro_score * (0.5 + 0.5 * alignment)
            return {
                "position_pct": max(0.0, min(pos, 0.15)),
                "astro_alignment": alignment,
                "reason": "no_trainer_fallback",
            }
        decision = self.trainer.decide_position(
            signal_strength=signal_strength,
            uncertainty=uncertainty,
            astro_alignment=alignment,
            regime=regime,
        )
        decision["astro_alignment"] = alignment
        decision["state_hash"] = self.current_state.state_hash
        return decision

    def record_and_update(self, exit_price, entry_price, direction, position_pct, hold_hours):
        if self.current_state is None or self.trainer is None:
            return {"updated": False, "reason": "no_state_or_trainer"}
        pnl = (exit_price - entry_price) / entry_price * 100.0
        if direction == "SHORT":
            pnl = -pnl
        from core.reward_engine import TradeOutcome

        outcome = TradeOutcome(
            entry_price=entry_price,
            exit_price=exit_price,
            position_pct=position_pct,
            direction=direction,
            hold_duration_hours=hold_hours,
            pnl_pct=pnl,
            outcome_type="profit" if pnl > 0 else "loss",
        )
        alignment = self.compute_alignment(direction)
        reward_signal = self.reward_engine.compute_reward(outcome, alignment, 0.5)
        self.trainer.record_experience(
            timestamp=self.current_state.timestamp,
            state_hash=self.current_state.state_hash,
            action_position_pct=position_pct,
            reward=reward_signal.total_reward,
            signal_strength=50.0,
            uncertainty=0.5,
            astro_alignment=alignment,
            actual_pnl=pnl,
        )
        update = self.trainer.update_policy()
        self.experience_log.append(
            {
                "timestamp": self.current_state.timestamp.isoformat(),
                "state_hash": self.current_state.state_hash,
                "pnl_pct": pnl,
                "reward": reward_signal.total_reward,
                "alignment": alignment,
                "update": update,
            }
        )
        return {
            "updated": True,
            "pnl_pct": pnl,
            "total_reward": reward_signal.total_reward,
            "alignment": alignment,
        }

    def status(self):
        return {
            "total_states": len(self._state_history),
            "total_experiences": self.trainer.state.total_experiences if self.trainer else 0,
            "current_episode": self.trainer.state.episode if self.trainer else 0,
            "best_reward": self.trainer.state.best_reward if self.trainer else None,
        }

    def save_log(self, path="models/astro_rl_log.json"):
        with open(path, "w") as f:
            json.dump(self.experience_log, f, indent=2, default=str)


if __name__ == "__main__":
    from core.online_trainer import OnlineTrainer, PolicyParams
    from core.reward_engine import RewardEngine

    re = RewardEngine(astro_weight=0.15)
    tr = OnlineTrainer(PolicyParams(), learning_rate=0.01)
    rl = AstroRLLoop(AstroRLConfig(), re, tr)
    print("ATOM-STEP-6: Astro RL Engine")
    print("=" * 60)
    now = datetime.utcnow()
    for day in range(7):
        ts = now - timedelta(days=6 - day)
        jd = 2451545.0 + (ts - datetime(2000, 1, 1)).total_seconds() / 86425.0
        state = AstroState(
            timestamp=ts,
            jd=jd,
            moon_longitude=(100 + day * 13) % 360,
            jupiter_longitude=(200 + day * 0.08) % 360,
            saturn_longitude=(320 + day * 0.03) % 360,
            moon_phase=(50 + day * 5) % 100,
            retrograde_mask="",
            nakshatra=(day * 3) % 27 + 1,
            choghadiya=[
                "Amrit",
                "Chaal",
                "Laabh",
                "Labh",
                "Char",
                "Naga",
                "Kaal",
                "Udveg",
            ][day % 8],
        )
        obs = rl.observe(state)
        print(
            f"  Day {day + 1}: moon={obs['moon_longitude']:.1f}  nak={obs['nakshatra']}  choghadiya={obs['choghadiya']}"
        )
        if day % 2 == 0:
            d = rl.decide(signal_strength=65.0, uncertainty=0.3, regime="NORMAL")
            print(f"    Decision: pos={d['position_pct']:.4f}  astro={d['astro_alignment']:+.3f}")
            rl.record_and_update(
                exit_price=102.0,
                entry_price=100.0,
                direction="LONG",
                position_pct=d["position_pct"],
                hold_hours=24.0,
            )
    print(f"  Status: {rl.status()}")
    rl.save_log()
    print("  Saved: models/astro_rl_log.json")
