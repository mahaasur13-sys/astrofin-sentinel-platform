"""amre/audit.py — Decision Audit Trail (ATOM-KARL-009)
Воспроизводимая трассировка всех решений для дебага OAP drift,
анализа ошибок и backtest не только результатов, но и решений.
"""
from __future__ import annotations


import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

# =============================================================================
# ATOM-KARL-009: Full Decision Record
# =============================================================================


@dataclass
class TrajectorySnapshot:
    """Один шаг траектории решения"""

    trajectory_id: str
    depth: int
    action: str
    q_value: float
    advantage: float
    uncertainty: float
    confidence: int
    policy_used: str


@dataclass
class EnsembleMember:
    """Участник ансамбля"""

    agent_name: str
    signal: str
    confidence: int
    weight: float
    q_value: float


@dataclass
class TrajectoryScore:
    """Score of a candidate trajectory — used by karl_integration"""

    trajectory_id: str
    score: float
    regime: str
    signals: list[str]


@dataclass
class MarketSnapshot:
    """Market state snapshot at decision time"""

    symbol: str
    price: float
    regime: str
    volatility_score: float


@dataclass
class EnsembleSelection:
    """Agent selected in ensemble with weight"""

    agent_name: str
    weight: float
    q_value: float


@dataclass
class KPISnapshot:
    """Снимок KPI в момент решения"""

    oos_fail_rate: float
    entropy: float
    uncertainty: float
    avg_confidence: float
    sharpe_ratio: float
    win_rate: float
    regime_stability: float
    exploration_rate: float
    ttc_depth: int
    grounding_strength: float


@dataclass
class DecisionRecord:
    """Полная запись решения — воспроизводимая трассировка"""

    # Идентификация
    decision_id: str
    timestamp: str
    session_id: str

    # Состояние рынка
    symbol: str
    price: float
    timeframe: str
    regime: str
    state_hash: str  # Хеш состояния для воспроизводимости

    # Траектории
    top_trajectories: list[TrajectorySnapshot]

    # Ансамбль
    selected_ensemble: list[EnsembleMember]

    # Q-values
    q_values: list[float]
    q_star: float
    advantage: float

    # Неопределённость
    uncertainty_aleatoric: float
    uncertainty_epistemic: float
    uncertainty_total: float

    # Confidence
    confidence_raw: int
    confidence_final: int
    confidence_adjustments: list[str]

    # Решение
    final_action: str  # LONG / SHORT / NEUTRAL
    position_pct: float

    # KPI
    kpi_snapshot: KPISnapshot
    # Метаданные
    metadata: dict[str, Any]
    # Meta-RL → KARL: risk-adjusted PnL (ATOM-META-RL-005)
    risk_adjusted_pnl: float = 0.0

    def to_dict(self) -> dict:
        """Конвертация в dict для сериализации"""
        d = asdict(self)
        d["_version"] = "KARL-009-v1"  # bump to v2 for risk_adjusted_pnl
        d["_hash"] = self.compute_hash()
        return d

    def compute_hash(self) -> str:
        """Вычисляет хеш записи для верификации"""
        key_data = f"{self.decision_id}:{self.state_hash}:{self.q_star}:{self.final_action}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    @classmethod
    def from_dict(cls, d: dict) -> "DecisionRecord":
        """Восстановление из dict"""
        d.pop("_version", None)
        d.pop("_hash", None)
        return cls(**d)


# =============================================================================
# ATOM-META-RL-006: Meta-RL Decision Record
# =============================================================================
# Lightweight record for Meta-RL strategy discovery audit trail.
# Stored separately from KARL DecisionRecord to keep concerns decoupled.

META_RL_DECISION_RECORD_ENABLED = True  # feature flag
_META_RL_AUDIT_LOG: "AuditLog" = None  # lazy singleton


@dataclass
class MetaRLDecisionRecord:
    """
    ATOM-META-RL-006: Lightweight audit record for Meta-RL strategy evaluations.

    Created automatically after each ScoredStrategy evaluation in MetaAgent.
    Provides full traceability between Meta-RL discovery runs and KARL DecisionRecord.

    Stored in a separate audit log (not mixed with live-trading KARL records).
    """

    # Strategy identity
    decision_id: str
    timestamp: str
    session_id: str
    strategy_id: str
    generation: int
    parent_ids: tuple

    # Strategy parameters (chromosome)
    strategy_params: dict
    strategy_name: str

    # Evaluation results
    pnl: float
    sharpe: float
    max_drawdown: float
    trades: int
    win_rate: float
    execution_cost: float

    # ATOM-META-RL-005: Risk-adjusted PnL
    risk_adjusted_pnl: float
    risk_adjustment_reason: str | None

    # Reward
    reward: float
    reward_history: list

    # Market context
    regime: str
    symbol: str

    # Metadata
    metadata: dict[str, Any]

    def to_dict(self) -> dict:
        """Serialize to dict for storage."""
        return {
            "decision_id": self.decision_id,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "strategy_id": self.strategy_id,
            "generation": self.generation,
            "parent_ids": list(self.parent_ids),
            "strategy_params": self.strategy_params,
            "strategy_name": self.strategy_name,
            "pnl": self.pnl,
            "sharpe": self.sharpe,
            "max_drawdown": self.max_drawdown,
            "trades": self.trades,
            "win_rate": self.win_rate,
            "execution_cost": self.execution_cost,
            "risk_adjusted_pnl": self.risk_adjusted_pnl,
            "risk_adjustment_reason": self.risk_adjustment_reason,
            "reward": self.reward,
            "reward_history": list(self.reward_history),
            "regime": self.regime,
            "symbol": self.symbol,
            "metadata": self.metadata or {},
            "_version": "META-RL-006-v1",
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MetaRLDecisionRecord":
        """Deserialize from dict."""
        d.pop("_version", None)
        return cls(**d)


def get_meta_rl_audit_log():
    """Get or create the Meta-RL audit log singleton."""
    global _META_RL_AUDIT_LOG
    if _META_RL_AUDIT_LOG is None:
        _META_RL_AUDIT_LOG = _MetaRLAuditLog()
    return _META_RL_AUDIT_LOG


class _MetaRLAuditLog:
    """
    Separate audit log for Meta-RL strategy discovery records.
    Decoupled from KARL AuditLog to avoid mixing live-trading and backtest records.
    """

    def __init__(self):
        self.records: list[MetaRLDecisionRecord] = []
        self._by_generation: dict[int, list[MetaRLDecisionRecord]] = {}
        self._by_strategy_id: dict[str, list[MetaRLDecisionRecord]] = {}

    def record(self, record: MetaRLDecisionRecord):
        """Add a MetaRLDecisionRecord to the log."""
        self.records.append(record)

        # Index by generation
        if record.generation not in self._by_generation:
            self._by_generation[record.generation] = []
        self._by_generation[record.generation].append(record)

        # Index by strategy_id
        if record.strategy_id not in self._by_strategy_id:
            self._by_strategy_id[record.strategy_id] = []
        self._by_strategy_id[record.strategy_id].append(record)

    def get_by_generation(self, generation: int) -> list[MetaRLDecisionRecord]:
        return self._by_generation.get(generation, [])

    def get_by_strategy_id(self, strategy_id: str) -> list[MetaRLDecisionRecord]:
        return self._by_strategy_id.get(strategy_id, [])

    def get_recent(self, n: int = 10) -> list[MetaRLDecisionRecord]:
        return self.records[-n:]

    def get_all(self) -> list[MetaRLDecisionRecord]:
        return list(self.records)

    def summary(self) -> dict:
        """Statistics for Meta-RL audit log."""
        if not self.records:
            return {"total": 0, "generations": 0}
        gens = sorted(set(r.generation for r in self.records))
        rewards = [r.reward for r in self.records]
        return {
            "total": len(self.records),
            "generations": len(gens),
            "min_generation": min(gens),
            "max_generation": max(gens),
            "mean_reward": round(sum(rewards) / len(rewards), 4),
            "max_reward": round(max(rewards), 4),
        }


def record_meta_rl_decision(
    scored: Any,
    market_data: dict,
    session_id: str = "default",
) -> MetaRLDecisionRecord | None:
    """
    ATOM-META-RL-006: Factory — create and record a MetaRLDecisionRecord
    from a ScoredStrategy after evaluation.

    Called automatically by MetaAgent.evaluate_population().

    Fail-safe: if recording fails, logs error and returns None (never raises).

    Args:
        scored: ScoredStrategy instance with .strategy, .evaluation, .reward,
                .reward_history, .generation, .parent_ids, .id
        market_data: dict with 'regime', 'symbol', etc.
        session_id: session identifier for grouping records

    Returns:
        MetaRLDecisionRecord if successful, None if failed
    """
    if not META_RL_DECISION_RECORD_ENABLED:
        return None

    import logging
    import uuid
    from datetime import datetime, timezone

    logger = logging.getLogger(__name__)

    try:
        # Extract strategy params
        if hasattr(scored.strategy, "chromosome"):
            params = scored.strategy.chromosome
        elif hasattr(scored.strategy, "config") and hasattr(scored.strategy.config, "params"):
            params = scored.strategy.config.params
        else:
            params = {}

        # Extract evaluation
        ev = scored.evaluation
        pnl = getattr(ev, "pnl", 0.0)
        sharpe = getattr(ev, "sharpe", 0.0)
        max_dd = getattr(ev, "max_drawdown", 0.0)
        trades = getattr(ev, "trades", 0)
        win_rate = getattr(ev, "win_rate", 0.0)
        exec_cost = getattr(ev, "execution_cost", 0.0)
        risk_adj_pnl = getattr(ev, "risk_adjusted_pnl", 0.0)
        risk_adj_reason = getattr(ev, "risk_adjustment_reason", None)

        # Strategy metadata
        strategy_name = (
            (getattr(scored.strategy, "config", None) and getattr(scored.strategy.config, "name", None))
            or getattr(scored.strategy, "name", "unknown")
            or "unknown"
        )

        record = MetaRLDecisionRecord(
            decision_id=f"METARL_{uuid.uuid4().hex[:12].upper()}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=session_id,
            strategy_id=scored.id,
            generation=scored.generation,
            parent_ids=scored.parent_ids,
            strategy_params=params,
            strategy_name=strategy_name,
            pnl=pnl,
            sharpe=sharpe,
            max_drawdown=max_dd,
            trades=trades,
            win_rate=win_rate,
            execution_cost=exec_cost,
            risk_adjusted_pnl=risk_adj_pnl,
            risk_adjustment_reason=risk_adj_reason,
            reward=scored.reward,
            reward_history=list(scored.reward_history) if scored.reward_history else [],
            regime=market_data.get("regime", "NEUTRAL_R"),
            symbol=market_data.get("symbol", "BTCUSDT"),
            metadata={
                "source": "meta_rl_evaluate_population",
                "evaluation_trades": trades,
            },
        )

        audit_log = get_meta_rl_audit_log()
        audit_log.record(record)

        logger.info(
            f"[META-RL-AUDIT] Recorded decision: "
            f"id={record.decision_id} "
            f"gen={record.generation} "
            f"strategy_id={record.strategy_id} "
            f"reward={record.reward:.4f} "
            f"risk_adj_pnl={record.risk_adjusted_pnl:+.4f} "
            f"sharpe={record.sharpe:.3f}"
        )

        return record

    except Exception as e:
        logger.warning(f"[META-RL-AUDIT] Failed to record MetaRLDecisionRecord: {e}")
        return None


class AuditLog:
    """Хранилище всех DecisionRecord с индексами для быстрого поиска"""

    def __init__(self):
        self.records: list[DecisionRecord] = []
        self._by_symbol: dict[str, list[DecisionRecord]] = {}
        self._by_regime: dict[str, list[DecisionRecord]] = {}
        self._by_action: dict[str, list[DecisionRecord]] = {}

    def record(self, record: DecisionRecord):
        """Добавить запись решения"""
        self.records.append(record)

        # Индексация
        if record.symbol not in self._by_symbol:
            self._by_symbol[record.symbol] = []
        self._by_symbol[record.symbol].append(record)

        if record.regime not in self._by_regime:
            self._by_regime[record.regime] = []
        self._by_regime[record.regime].append(record)

        if record.final_action not in self._by_action:
            self._by_action[record.final_action] = []
        self._by_action[record.final_action].append(record)

    def get_recent(self, n: int = 10) -> list[DecisionRecord]:
        return self.records[-n:]

    def get_by_symbol(self, symbol: str) -> list[DecisionRecord]:
        return self._by_symbol.get(symbol, [])

    def get_by_regime(self, regime: str) -> list[DecisionRecord]:
        return self._by_regime.get(regime, [])

    def get_by_action(self, action: str) -> list[DecisionRecord]:
        return self._by_action.get(action, [])

    def find_by_state_hash(self, state_hash: str) -> DecisionRecord | None:
        """Воспроизвести конкретное решение по хешу состояния"""
        for r in self.records:
            if r.state_hash == state_hash:
                return r
        return None

    def find_similar(self, regime: str, action: str, n: int = 5) -> list[DecisionRecord]:
        """Найти похожие решения для анализа"""
        candidates = self._by_regime.get(regime, [])
        return [r for r in candidates if r.final_action == action][-n:]

    def summary(self) -> dict[str, Any]:
        """Статистика по всем решениям"""
        if not self.records:
            return {"total": 0, "avg_confidence": 0, "pass_rate": 0}

        total = len(self.records)
        avg_conf = sum(r.confidence_final for r in self.records) / total

        # Группировка по action
        action_dist = {}
        for r in self.records:
            action_dist[r.final_action] = action_dist.get(r.final_action, 0) + 1

        # Regime distribution
        regime_dist = {}
        for r in self.records:
            regime_dist[r.regime] = regime_dist.get(r.regime, 0) + 1

        # Success rate по confidence
        high_conf = [r for r in self.records if r.confidence_final >= 70]
        success_rate = len(high_conf) / total if total > 0 else 0

        return {
            "total": total,
            "avg_confidence_final": round(avg_conf, 1),
            "action_distribution": action_dist,
            "regime_distribution": regime_dist,
            "high_confidence_ratio": round(success_rate, 3),
            "avg_q_star": round(sum(r.q_star for r in self.records) / total, 4),
            "avg_uncertainty": round(sum(r.uncertainty_total for r in self.records) / total, 4),
        }

    def analyze_drift(self) -> dict[str, Any]:
        """Анализ OAP drift — деградирует ли система глобально"""
        if len(self.records) < 10:
            return {"status": "insufficient_data", "records": len(self.records)}

        # Разбиваем на квинтейли по времени
        n = len(self.records)
        q1 = self.records[: n // 4]
        q4 = self.records[-n // 4 :]

        def avg_metrics(recs):
            return {
                "avg_conf": sum(r.confidence_final for r in recs) / len(recs),
                "avg_q": sum(r.q_star for r in recs) / len(recs),
                "avg_unc": sum(r.uncertainty_total for r in recs) / len(recs),
            }

        m1 = avg_metrics(q1)
        m4 = avg_metrics(q4)

        drift_conf = m1["avg_conf"] - m4["avg_conf"]
        drift_q = m1["avg_q"] - m4["avg_q"]
        drift_unc = m4["avg_unc"] - m1["avg_unc"]

        return {
            "status": "degrading" if drift_conf < -5 or drift_unc > 0.1 else "stable",
            "confidence_drift": round(drift_conf, 2),
            "q_star_drift": round(drift_q, 4),
            "uncertainty_drift": round(drift_unc, 4),
            "recent_high_conf_pct": round(len([r for r in q4 if r.confidence_final >= 70]) / len(q4), 3),
        }

    def export_json(self) -> str:
        """Экспорт всех записей в JSON для внешнего анализа"""
        return json.dumps([r.to_dict() for r in self.records], indent=2, default=str)

    def import_json(self, json_str: str):
        """Импорт записей из JSON"""
        data = json.loads(json_str)
        for d in data:
            self.record(DecisionRecord.from_dict(d))


# =============================================================================
# Global singleton
# =============================================================================

_AUDIT_LOG: AuditLog | None = None


def get_audit_log() -> AuditLog:
    global _AUDIT_LOG
    if _AUDIT_LOG is None:
        _AUDIT_LOG = AuditLog()
    return _AUDIT_LOG


def record_decision(**kwargs) -> DecisionRecord:
    """Фабрика для создания DecisionRecord"""
    record = DecisionRecord(**kwargs)
    get_audit_log().record(record)
    return record


# =============================================================================
# Convenience builders для интеграции с другими модулями
# =============================================================================


def build_decision_record(
    decision_id: str,
    session_id: str,
    symbol: str,
    price: float,
    timeframe: str,
    regime: str,
    state_hash: str,
    top_trajectories: list[dict],
    selected_ensemble: list[dict],
    q_values: list[float],
    q_star: float,
    uncertainty: dict[str, float],
    confidence_raw: int,
    confidence_final: int,
    confidence_adjustments: list[str],
    final_action: str,
    position_pct: float,
    kpi_snapshot: dict[str, float],
    metadata: dict[str, Any] | None = None,
    # ATOM-META-RL-005: Meta-RL → KARL flow
    risk_adjusted_pnl: float = 0.0,
) -> DecisionRecord:
    """Удобный builder для создания DecisionRecord из данных системы"""

    # Конвертируем траектории
    traj_snapshots = [
        TrajectorySnapshot(
            trajectory_id=t.get("id", f"traj_{i}"),
            depth=t.get("depth", 0),
            action=t.get("action", "UNKNOWN"),
            q_value=t.get("q_value", 0.0),
            advantage=t.get("advantage", 0.0),
            uncertainty=t.get("uncertainty", 0.5),
            confidence=t.get("confidence", 50),
            policy_used=t.get("policy", "default"),
        )
        for i, t in enumerate(top_trajectories)
    ]

    # Конвертируем ансамбль
    ensemble_members = [
        EnsembleMember(
            agent_name=e.get("name", "unknown"),
            signal=e.get("signal", "NEUTRAL"),
            confidence=e.get("confidence", 50),
            weight=e.get("weight", 0.0),
            q_value=e.get("q_value", 0.0),
        )
        for e in selected_ensemble
    ]

    # Вычисляем advantage
    advantage = max(q_values) - q_star if q_values else 0.0

    # KPI snapshot
    kpi = KPISnapshot(
        oos_fail_rate=kpi_snapshot.get("oos_fail_rate", 0.0),
        entropy=kpi_snapshot.get("entropy", 0.5),
        uncertainty=kpi_snapshot.get("uncertainty", 0.5),
        avg_confidence=kpi_snapshot.get("avg_confidence", 50.0),
        sharpe_ratio=kpi_snapshot.get("sharpe_ratio", 0.0),
        win_rate=kpi_snapshot.get("win_rate", 0.0),
        regime_stability=kpi_snapshot.get("regime_stability", 1.0),
        exploration_rate=kpi_snapshot.get("exploration_rate", 0.1),
        ttc_depth=kpi_snapshot.get("ttc_depth", 3),
        grounding_strength=kpi_snapshot.get("grounding_strength", 0.8),
    )

    return DecisionRecord(
        decision_id=decision_id,
        timestamp=datetime.now().isoformat(),
        session_id=session_id,
        symbol=symbol,
        price=price,
        timeframe=timeframe,
        regime=regime,
        state_hash=state_hash,
        top_trajectories=traj_snapshots,
        selected_ensemble=ensemble_members,
        q_values=q_values,
        q_star=q_star,
        advantage=advantage,
        uncertainty_aleatoric=uncertainty.get("aleatoric", 0.5),
        uncertainty_epistemic=uncertainty.get("epistemic", 0.5),
        uncertainty_total=uncertainty.get("total", 0.5),
        confidence_raw=confidence_raw,
        confidence_final=confidence_final,
        confidence_adjustments=confidence_adjustments,
        final_action=final_action,
        position_pct=position_pct,
        kpi_snapshot=kpi,
        metadata=metadata or {},
        risk_adjusted_pnl=risk_adjusted_pnl,
    )
