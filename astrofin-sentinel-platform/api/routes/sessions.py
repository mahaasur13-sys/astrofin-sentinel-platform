"""api/routes/sessions.py — Session list + detail endpoints for React frontend."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException, Query

from api.schemas import AgentDecisionDetail, SessionDetailResponse, SessionListItem, SessionListResponse
from core.history_db import get_db as get_history_db
from db.session import get_db_manager

log = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/", response_model=SessionListResponse)
async def list_sessions(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200)):
    """Paginated session list for React SessionTable (DataGrid).

    Returns sessions sorted by created_at DESC.
    """
    db = get_history_db()
    sessions_data = db.list(limit=limit, offset=skip)
    total = db.stats().get("total_sessions", 0)

    items = []
    for s in sessions_data:
        items.append(
            SessionListItem(
                id=s.get("session_id", s.get("id", "")),
                timestamp=s.get("created_at", s.get("started_at", "")),
                symbol=s.get("symbol", "Unknown"),
                signal=s.get("final_signal", "NEUTRAL"),
                confidence=(s.get("final_confidence", 50) or 50) / 100.0,
                final_pnl=None,
            )
        )

    return SessionListResponse(items=items, total=total)


@router.get("/{session_id}/details", response_model=SessionDetailResponse)
async def get_session_details(session_id: str):
    """Returns full session context for React Context Drawer.

    Joins sessions + karl_decision_records to show Council Debate.
    """
    with get_db_manager().session() as db:
        from db.models import Session

        session = db.query(Session).filter(Session.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        from db.models import KARLDecisionRecord

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
                    agent_name=meta.get("agent_name", f"KARL ({str(d.decision_id)[:8]})"),
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
