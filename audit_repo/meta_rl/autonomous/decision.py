"""meta_rl/autonomous/decision.py -- ATOM-META-RL-024: Decision audit trail"""

from __future__ import annotations

from dataclasses import dataclass

from meta_rl.types import AutonomousDecision


@dataclass
class DecisionLogger:
    def log(self, decision: AutonomousDecision) -> None:
        print(f"[DECISION] obs={decision.observation.price} adj={decision.adjustment} res={decision.result}")
