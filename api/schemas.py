"""api/schemas.py — Pydantic contracts for React frontend."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AgentDecisionDetail(BaseModel):
    agent_name: str
    signal: str
    confidence: float
    reasoning: str
    rag_context: Optional[str] = None


class SessionDetailResponse(BaseModel):
    session_id: str
    symbol: str
    start_time: datetime
    end_time: Optional[datetime] = None
    final_signal: str
    final_pnl: Optional[float] = None
    agent_decisions: list[AgentDecisionDetail] = []
    broker_executed_price: Optional[float] = None
    broker_slippage: Optional[float] = None
    broker_fee: Optional[float] = None

class SessionListItem(BaseModel):
    id: str
    timestamp: datetime
    symbol: str
    signal: str
    confidence: float
    final_pnl: Optional[float] = None


class SessionListResponse(BaseModel):
    items: list[SessionListItem]
    total: int
