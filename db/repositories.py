"""db/repositories.py — PostgreSQL CRUD Repositories (ATOM-DB-MIGRATION)

All repositories work with PostgreSQL when available,
fall back gracefully to SQLite when not.
"""
from __future__ import annotations


import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# ─── Import swap: PostgreSQL vs SQLite ────────────────────────────────────────

if os.getenv("DB_BACKEND", "postgresql").lower() == "postgresql":
    _BACKEND = "postgresql"
else:
    _BACKEND = "sqlite"

    def _get_sqlite_conn():
        import sqlite3
        from pathlib import Path

        root = Path(__file__).parent.parent
        db_path = root / "core" / "history.db"
        db_path.parent.mkdir(exist_ok=True)
        return sqlite3.connect(str(db_path))


# ─── JSON helpers ───────────────────────────────────────────────────────────────


def _d(obj) -> str:
    """Serialize to JSON string."""
    return json.dumps(obj, default=str) if obj is not None else "{}"


def _l(text: str) -> Any:
    """Deserialize from JSON string."""
    try:
        return json.loads(text) if text else []
    except (json.JSONDecodeError, TypeError):
        return []


def _ld(text: str) -> dict[str, Any]:
    try:
        return json.loads(text) if text else {}
    except (json.JSONDecodeError, TypeError):
        return {}


# ─── PostgreSQL repositories ───────────────────────────────────────────────────

if _BACKEND == "postgresql":
    from db.models import (
        AgentSignal,
        AstroPosition,
        AuditLogRecord,
        KARLDecisionRecord,
    )
    from db.session import pg_session

    class DecisionRecordRepository:
        @staticmethod
        def save(record: dict[str, Any]) -> str:
            with pg_session() as s:
                dr = KARLDecisionRecord(
                    decision_id=record["decision_id"],
                    session_id=record.get("session_id"),
                    symbol=record.get("symbol", "BTCUSDT"),
                    price=record.get("price", 0),
                    timeframe=record.get("timeframe", "SWING"),
                    regime=record.get("regime", "NORMAL"),
                    state_hash=record.get("state_hash"),
                    top_trajectories_json=_d(record.get("top_trajectories", [])),
                    selected_ensemble_json=_d(record.get("selected_ensemble", [])),
                    q_values_json=_d(record.get("q_values", [])),
                    q_star=record.get("q_star", 0.5),
                    advantage=record.get("advantage", 0),
                    uncertainty_aleatoric=record.get("uncertainty_aleatoric", 0.5),
                    uncertainty_epistemic=record.get("uncertainty_epistemic", 0.5),
                    uncertainty_total=record.get("uncertainty_total", 0.5),
                    confidence_raw=record.get("confidence_raw", 50),
                    confidence_final=record.get("confidence_final", 50),
                    confidence_adjustments_json=_d(record.get("confidence_adjustments", [])),
                    final_action=record.get("final_action", "NEUTRAL"),
                    position_pct=record.get("position_pct", 0),
                    kpi_snapshot_json=_d(record.get("kpi_snapshot", {})),
                    metadata_json=_d(record.get("metadata", {})),
                )
                s.add(dr)
                return record["decision_id"]

        @staticmethod
        def get_recent(limit: int = 10) -> list[dict]:
            with pg_session() as s:
                rows = s.query(KARLDecisionRecord).order_by(KARLDecisionRecord.created_at.desc()).limit(limit).all()
                return [_row_to_karl(r) for r in rows]

        @staticmethod
        def get_by_symbol(symbol: str, limit: int = 100) -> list[dict]:
            with pg_session() as s:
                rows = (
                    s.query(KARLDecisionRecord)
                    .filter(KARLDecisionRecord.symbol == symbol)
                    .order_by(KARLDecisionRecord.created_at.desc())
                    .limit(limit)
                    .all()
                )
                return [_row_to_karl(r) for r in rows]

        @staticmethod
        def count_by_action() -> dict[str, int]:
            with pg_session() as s:
                from sqlalchemy import func

                rows = (
                    s.query(
                        KARLDecisionRecord.final_action,
                        func.count(KARLDecisionRecord.decision_id),
                    )
                    .group_by(KARLDecisionRecord.final_action)
                    .all()
                )
                return {str(r[0]): r[1] for r in rows}

        @staticmethod
        def save_batch(records: list[dict]) -> int:
            with pg_session() as s:
                for record in records:
                    dr = KARLDecisionRecord(
                        decision_id=record["decision_id"],
                        session_id=record.get("session_id"),
                        symbol=record.get("symbol", "BTCUSDT"),
                        price=record.get("price", 0),
                        timeframe=record.get("timeframe", "SWING"),
                        regime=record.get("regime", "NORMAL"),
                        state_hash=record.get("state_hash"),
                        top_trajectories_json=_d(record.get("top_trajectories", [])),
                        selected_ensemble_json=_d(record.get("selected_ensemble", [])),
                        q_values_json=_d(record.get("q_values", [])),
                        q_star=record.get("q_star", 0.5),
                        advantage=record.get("advantage", 0),
                        uncertainty_aleatoric=record.get("uncertainty_aleatoric", 0.5),
                        uncertainty_epistemic=record.get("uncertainty_epistemic", 0.5),
                        uncertainty_total=record.get("uncertainty_total", 0.5),
                        confidence_raw=record.get("confidence_raw", 50),
                        confidence_final=record.get("confidence_final", 50),
                        confidence_adjustments_json=_d(record.get("confidence_adjustments", [])),
                        final_action=record.get("final_action", "NEUTRAL"),
                        position_pct=record.get("position_pct", 0),
                        kpi_snapshot_json=_d(record.get("kpi_snapshot", {})),
                        metadata_json=_d(record.get("metadata", {})),
                    )
                    s.add(dr)
                return len(records)

    class AgentSignalRepository:
        @staticmethod
        def save(
            session_id: str,
            agent_name: str,
            signal: str,
            confidence: int,
            reasoning: str,
            metadata: dict | None = None,
        ) -> None:
            with pg_session() as s:
                ag = AgentSignal(
                    session_id=session_id,
                    agent_name=agent_name,
                    signal=signal,
                    confidence=confidence,
                    reasoning=reasoning,
                    metadata_json=_d(metadata or {}),
                )
                s.add(ag)

        @staticmethod
        def get_by_session(session_id: str) -> list[dict]:
            with pg_session() as s:
                rows = (
                    s.query(AgentSignal)
                    .filter(AgentSignal.session_id == session_id)
                    .order_by(AgentSignal.created_at)
                    .all()
                )
                return [_row_to_signal(r) for r in rows]

    class AstroPositionRepository:
        @staticmethod
        def save(
            session_id: str,
            planet: str,
            longitude: float,
            latitude: float,
            speed: float,
            nakshatra: str,
            rashi: str,
            metadata: dict | None = None,
        ) -> None:
            with pg_session() as s:
                ap = AstroPosition(
                    session_id=session_id,
                    planet=planet,
                    longitude=longitude,
                    latitude=latitude,
                    speed=speed,
                    nakshatra=nakshatra,
                    rashi=rashi,
                    metadata_json=_d(metadata or {}),
                )
                s.add(ap)

        @staticmethod
        def get_by_session(session_id: str) -> list[dict]:
            with pg_session() as s:
                rows = s.query(AstroPosition).filter(AstroPosition.session_id == session_id).all()
                return [_row_to_astro(r) for r in rows]

    class AuditLogRepository:
        @staticmethod
        def save(
            session_id: str,
            decision_id: str,
            action: str,
            details: dict | None = None,
        ) -> None:
            with pg_session() as s:
                al = AuditLogRecord(
                    session_id=session_id,
                    decision_id=decision_id,
                    action=action,
                    details_json=_d(details or {}),
                )
                s.add(al)

        @staticmethod
        def get_recent(limit: int = 100) -> list[dict]:
            with pg_session() as s:
                rows = s.query(AuditLogRecord).order_by(AuditLogRecord.created_at.desc()).limit(limit).all()
                return [_row_to_audit(r) for r in rows]


# ─── SQLite fallback repositories ──────────────────────────────────────────────

else:
    # SQLite versions — using core/history_db
    from core.history_db import list_sessions, save_session

    class DecisionRecordRepository:
        @staticmethod
        def save(record: dict[str, Any]) -> str:
            try:
                save_session(record)
                return record["decision_id"]
            except Exception as e:
                logger.warning(f"[SQLite] DecisionRecordRepository.save failed: {e}")
                return record["decision_id"]

        @staticmethod
        def get_recent(limit: int = 10) -> list[dict]:
            try:
                sessions = list_sessions(limit=limit)
                return [s for s in sessions if "decision_id" in s]
            except Exception:
                return []

        @staticmethod
        def get_by_symbol(symbol: str, limit: int = 100) -> list[dict]:
            try:
                sessions = list_sessions(limit=limit)
                return [s for s in sessions if s.get("symbol") == symbol]
            except Exception:
                return []

        @staticmethod
        def count_by_action() -> dict[str, int]:
            return {}

        @staticmethod
        def save_batch(records: list[dict]) -> int:
            for r in records:
                DecisionRecordRepository.save(r)
            return len(records)

    class AgentSignalRepository:
        @staticmethod
        def save(
            session_id: str,
            agent_name: str,
            signal: str,
            confidence: int,
            reasoning: str,
            metadata: dict | None = None,
        ) -> None:
            pass  # SQLite: signals stored inside session JSON

        @staticmethod
        def get_by_session(session_id: str) -> list[dict]:
            return []

    class AstroPositionRepository:
        @staticmethod
        def save(
            session_id: str,
            planet: str,
            longitude: float,
            latitude: float,
            speed: float,
            nakshatra: str,
            rashi: str,
            metadata: dict | None = None,
        ) -> None:
            pass

        @staticmethod
        def get_by_session(session_id: str) -> list[dict]:
            return []

    class AuditLogRepository:
        @staticmethod
        def save(
            session_id: str,
            decision_id: str,
            action: str,
            details: dict | None = None,
        ) -> None:
            pass

        @staticmethod
        def get_recent(limit: int = 100) -> list[dict]:
            return []


# ─── Row-to-dict helpers (PostgreSQL only) ─────────────────────────────────────


def _row_to_karl(r) -> dict:
    return {
        "decision_id": r.decision_id,
        "session_id": r.session_id,
        "symbol": r.symbol,
        "price": float(r.price) if r.price else None,
        "timeframe": r.timeframe,
        "regime": r.regime,
        "state_hash": r.state_hash,
        "top_trajectories": _l(r.top_trajectories_json),
        "selected_ensemble": _l(r.selected_ensemble_json),
        "q_values": _l(r.q_values_json),
        "q_star": float(r.q_star) if r.q_star else None,
        "advantage": float(r.advantage) if r.advantage else None,
        "uncertainty_aleatoric": float(r.uncertainty_aleatoric) if r.uncertainty_aleatoric else None,
        "uncertainty_epistemic": float(r.uncertainty_epistemic) if r.uncertainty_epistemic else None,
        "uncertainty_total": float(r.uncertainty_total) if r.uncertainty_total else None,
        "confidence_raw": r.confidence_raw,
        "confidence_final": r.confidence_final,
        "confidence_adjustments": _l(r.confidence_adjustments_json),
        "final_action": r.final_action,
        "position_pct": float(r.position_pct) if r.position_pct else None,
        "kpi_snapshot": _ld(r.kpi_snapshot_json),
        "metadata": _ld(r.metadata_json),
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _row_to_signal(r) -> dict:
    return {
        "signal_id": r.signal_id,
        "session_id": r.session_id,
        "agent_name": r.agent_name,
        "signal": r.signal,
        "confidence": r.confidence,
        "reasoning": r.reasoning,
        "metadata": _ld(r.metadata_json),
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _row_to_astro(r) -> dict:
    return {
        "id": r.id,
        "session_id": r.session_id,
        "planet": r.planet,
        "longitude": float(r.longitude) if r.longitude else None,
        "latitude": float(r.latitude) if r.latitude else None,
        "speed": float(r.speed) if r.speed else None,
        "nakshatra": r.nakshatra,
        "rashi": r.rashi,
        "metadata": _ld(r.metadata_json),
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _row_to_audit(r) -> dict:
    return {
        "id": r.id,
        "session_id": r.session_id,
        "decision_id": r.decision_id,
        "action": r.action,
        "details": _ld(r.details_json),
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


# ─── Stats ─────────────────────────────────────────────────────────────────────


def is_postgres_available() -> bool:
    if _BACKEND == "sqlite":
        return False
    try:
        from db.session import is_postgres_available as _check

        return _check()
    except Exception:
        return False


def get_all_stats() -> dict:
    stats = {"backend": _BACKEND, "postgres_available": False}
    try:
        stats["postgres_available"] = is_postgres_available()
        if stats["postgres_available"]:
            with pg_session() as s:
                stats["decision_records"] = s.query(KARLDecisionRecord).count()
                stats["agent_signals"] = s.query(AgentSignal).count()
                stats["astro_positions"] = s.query(AstroPosition).count()
                stats["audit_records"] = s.query(AuditLogRecord).count()
    except Exception as e:
        stats["error"] = str(e)
    return stats
