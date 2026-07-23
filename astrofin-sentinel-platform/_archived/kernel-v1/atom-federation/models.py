from dataclasses import dataclass
from typing import List


@dataclass
class ConsensusResult:
    theta_hash: str
    source: str
    is_quorum: bool
    voters: List[str]
    confidence: float = 0.0
