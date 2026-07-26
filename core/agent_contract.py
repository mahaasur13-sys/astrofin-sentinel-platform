"""core/agent_contract.py — Pydantic contract for agent I/O validation (D2+F3)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

SignalDirection = Literal["LONG", "SHORT", "HOLD", "BUY", "SELL", "NEUTRAL"]


class AgentOutput(BaseModel):
    """Validated agent response contract."""

    signal: SignalDirection = Field(..., description="Trading signal direction")
    confidence: float = Field(..., ge=0.0, le=100.0, description="Confidence 0-100")
    reasoning: str = Field(default="", description="Agent reasoning trace")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extra telemetry")

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(100.0, v))

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


class AgentInput(BaseModel):
    """Validated agent input contract."""

    symbol: str = Field(..., min_length=1, description="Trading pair symbol")
    timeframe: str = Field(default="1d", description="OHLCV timeframe")
    prompt: str = Field(default="", description="User prompt")
    regime: str = Field(default="NORMAL", description="Volatility regime")

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()
