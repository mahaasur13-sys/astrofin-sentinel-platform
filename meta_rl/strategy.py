"""meta_rl/strategy.py — Strategy type for Meta-RL (ATOM-META-RL-008)"""

import uuid
from typing import Any


class Strategy:
    """Trading strategy with chromosome, generation tracking, and full serialization."""

    def __init__(
        self,
        name: str = "UnnamedStrategy",
        strategy_type: str = "ma_crossover",
        parameters: dict[str, Any] | None = None,
        assets: list[str] | None = None,
        timeframe: str = "1h",
        risk_profile: str = "medium",
        generation: int = 0,
        parent_ids: list[str] | None = None,
        reward_history: list[float] | None = None,
        chromosome: dict[str, Any] | None = None,
        id: str | None = None,
    ):
        self.id = id or str(uuid.uuid4())[:12]
        self.name = name
        self.strategy_type = strategy_type
        self.parameters = parameters or {}
        self.assets = assets or ["BTCUSDT"]
        self.timeframe = timeframe
        self.risk_profile = risk_profile
        self.generation = generation
        self.parent_ids = parent_ids or []
        self.reward_history = reward_history or []
        self.chromosome = chromosome or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "strategy_type": self.strategy_type,
            "parameters": self.parameters,
            "assets": self.assets,
            "timeframe": self.timeframe,
            "risk_profile": self.risk_profile,
            "generation": self.generation,
            "parent_ids": self.parent_ids,
            "reward_history": self.reward_history,
            "chromosome": self.chromosome,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Strategy":
        """Восстанавливает Strategy из словаря (для persistence)."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", "UnnamedStrategy"),
            strategy_type=data.get("strategy_type", "ma_crossover"),
            parameters=data.get("parameters", {}),
            assets=data.get("assets", ["BTCUSDT"]),
            timeframe=data.get("timeframe", "1h"),
            risk_profile=data.get("risk_profile", "medium"),
            generation=data.get("generation", 0),
            parent_ids=data.get("parent_ids", []),
            reward_history=data.get("reward_history", []),
            chromosome=data.get("chromosome", {}),
        )

    def __repr__(self) -> str:
        return f"Strategy({self.name}, gen={self.generation}, id={self.id})"
