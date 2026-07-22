"""api/routes/sessions.py — Session detail endpoint with KARL agent decisions."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException

from api.schemas import AgentDecisionDetail, SessionDetailResponse
from db.models import KARLDecisionRecord, Session
from db.session import get_db_manager

log = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


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
