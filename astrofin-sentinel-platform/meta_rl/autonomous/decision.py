"""meta_rl/autonomous/decision.py -- ATOM-META-RL-024: Decision audit trail"""

from __future__ import annotations

from dataclasses import dataclass

from meta_rl.types import AutonomousDecision

import logging
log = logging.getLogger(__name__)



@dataclass
class DecisionLogger:
    def log(self, decision: AutonomousDecision) -> None:
        log.info(
            f"[DECISION] obs={decision.observation.price} adj={decision.adjustment} res={decision.result}"
        )
