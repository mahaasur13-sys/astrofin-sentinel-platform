"""api/routes/sessions.py — Session endpoints: list + detail with KARL agent decisions."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException

from api.schemas import (
    AgentDecisionDetail,
    SessionDetailResponse,
    SessionListItem,
    SessionListResponse,
)
from db.models import KARLDecisionRecord, Session
from db.session import get_db_manager

log = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/", response_model=SessionListResponse)
async def get_sessions_list(skip: int = 0, limit: int = 50):
    """Returns paginated list of sessions for SessionTable component.
    
    Args:
        skip: Number of records to skip (offset)
        limit: Maximum number of records to return (max 100)
    
    Returns:
        SessionListResponse with items and total count
    """
    limit = min(limit, 100)  # cap at 100 to prevent abuse
    
    with get_db_manager().session() as db:
        total = db.query(Session).count()
        sessions = (
            db.query(Session)
            .order_by(Session.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        items = []
        for s in sessions:
            # Get average confidence from KARL decisions for this session
            decisions = (
                db.query(KARLDecisionRecord)
                .filter(KARLDecisionRecord.session_id == str(s.session_id))
                .all()
            )
            confidences = [
                float(d.confidence_final)
                for d in decisions
                if d.confidence_final is not None
            ]
            avg_confidence = (
                sum(confidences) / len(confidences) if confidences else 0.0
            )
            
            items.append(
                SessionListItem(
                    id=str(s.session_id),
                    timestamp=s.created_at,
                    symbol=s.symbol,
                    signal=s.final_signal or "NEUTRAL",
                    confidence=avg_confidence / 100.0,  # normalize to 0-1 range
                    final_pnl=None,  # TODO: compute from broker execution data
                )
            )
        
        return SessionListResponse(items=items, total=total)


@router.get("/{session_id}/details", response_model=SessionDetailResponse)
async def get_session_details(session_id: str):
    """Returns full session context for React Context Drawer.

    Joins sessions + karl_decision_records to show Council Debate.
    """
    with get_db_manager().session() as db:
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        decisions = (
            db.query(KARLDecisionRecord)
            .filter(KARLDecisionRecord.session_id == str(session.session_id))
            .all()
        )

        agent_decisions = []
        for d in decisions:
            meta = {}
            if d.metadata_json:
                try:
                    meta = json.loads(d.metadata_json)
                except (json.JSONDecodeError, TypeError):
                    pass
            agent_decisions.append(
                AgentDecisionDetail(
                    agent_name=meta.get("agent_name", f"KARL ({d.decision_id[:8]})"),
                    signal=d.final_action if d.final_action else "NEUTRAL",
                    confidence=float(d.confidence_final) if d.confidence_final else 0,
                    reasoning=meta.get("reasoning", ""),
                    rag_context=meta.get("rag_context"),
                )
            )

        return SessionDetailResponse(
            session_id=str(session.session_id),
            symbol=session.symbol,
            start_time=session.created_at,
            end_time=session.finished_at,
            final_signal=session.final_signal or "NEUTRAL",
            final_pnl=None,
            agent_decisions=agent_decisions,
        )
