"""
Pydantic models for input validation.
FIXED (audit 15.05.2026): Validates all inputs BEFORE they reach the orchestrator.
"""

from enum import Enum

from pydantic import BaseModel, Field, validator


class Timeframe(str, Enum):
    """Allowed timeframes for the Sentinel V5 orchestrator."""

    INTRADAY = "INTRADAY"
    SWING = "SWING"
    POSITION = "POSITION"
    LONG_TERM = "LONG_TERM"


class SentinelV5Request(BaseModel):
    """
    Validated input for the Sentinel V5 orchestrator.

    If Pydantic validation fails, the orchestrator never runs —
    this prevents IndexError and TypeError from invalid inputs.
    """

    user_query: str = Field(..., min_length=1, max_length=1000)
    symbol: str = Field(default="BTCUSDT", pattern=r"^[A-Z]{1,10}(USDT|USDC|BUSD)$")
    timeframe: Timeframe = Timeframe.SWING
    current_price: float = Field(default=0.0, ge=0.0)
    birth_data: dict | None = None
    include_technical: bool = True
    include_macro: bool = True
    include_astro: bool = True
    include_electional: bool = False
    session_id: str | None = None
    persist: bool = True
    thompson_k: int = Field(default=4, ge=1, le=10)

    @validator("user_query")
    def validate_query(cls, v):  # noqa: N805
        """Query must not be empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()

    @validator("symbol")
    def validate_symbol(cls, v):  # noqa: N805
        """Symbol must be uppercase and non-empty."""
        v = v.upper()
        if not v:
            raise ValueError("Symbol cannot be empty")
        return v
