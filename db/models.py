"""db/models.py - SQLAlchemy models for AstroFin V5 (ATOM-DB-MIGRATION)

Note: Using Text columns instead of JSONB for maximum compatibility.
JSON stored as text is handled by the repository layer.
"""

import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class SignalDirection(enum.Enum):
    BUY = "BUY"
    LONG = "LONG"
    SELL = "SELL"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"
    HOLD = "HOLD"
    AVOID = "AVOID"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"


class VolatilityRegime(enum.Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


class QueryType(enum.Enum):
    NATURAL = "NATURAL"
    TECHNICAL = "TECHNICAL"
    FUNDAMENTAL = "FUNDAMENTAL"
    MACRO = "MACRO"
    QUANT = "QUANT"
    OPTIONS = "OPTIONS"
    SENTIMENT = "SENTIMENT"
    ASTRO = "ASTRO"
    ELECTION = "ELECTION"


class SessionStatus(enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class AgentPool(enum.Enum):
    TECHNICAL = "TECHNICAL"
    MACRO = "MACRO"
    ASTRO = "ASTRO"
    ELECTION = "ELECTION"
    SENTIMENT = "SENTIMENT"
    QUANT = "QUANT"
    FUNDAMENTAL = "FUNDAMENTAL"
    OPTIONS = "OPTIONS"


class Session(Base):
    __tablename__ = "sessions"
    session_id = Column(UUID(as_uuid=True), primary_key=True)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(20), nullable=False)
    query_type = Column(String(20), nullable=False)
    current_price = Column(Numeric(20, 8))
    session_status = Column(String(20), default="pending")
    final_signal = Column(String(20))
    final_confidence = Column(Integer)
    regime = Column(String(20), default="NORMAL")
    flows_run_json = Column(Text)
    thompson_selections_json = Column(Text)
    agent_count = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), default=func.now())
    finished_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=func.now())

    signals = relationship("AgentSignal", back_populates="session", cascade="all, delete-orphan")
    decisions = relationship("KARLDecisionRecord", back_populates="session")


class AgentSignal(Base):
    __tablename__ = "agent_signals"
    signal_id = Column(UUID(as_uuid=True), primary_key=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.session_id", ondelete="CASCADE"))
    agent_name = Column(String(100), nullable=False)
    agent_pool = Column(String(20))
    signal = Column(String(20))  # renamed from 'signal' to avoid column name conflict
    confidence = Column(Integer)
    reasoning = Column(Text)
    metadata_json = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now())

    session = relationship("Session", back_populates="signals")


class AstroPosition(Base):
    """Vedic planetary positions at decision time."""

    __tablename__ = "astro_positions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.session_id", ondelete="CASCADE"))
    planet = Column(String(20), nullable=False)
    longitude = Column(Numeric(10, 6))
    latitude = Column(Numeric(10, 6))
    speed = Column(Numeric(10, 6))
    nakshatra = Column(String(50))
    rashi = Column(String(20))
    metadata_json = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now())


class AuditLogRecord(Base):
    """Immutable audit log record."""

    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True))
    decision_id = Column(UUID(as_uuid=True))
    action = Column(String(20), nullable=False)
    details_json = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now())


class AgentBelief(Base):
    __tablename__ = "agent_beliefs"
    agent_name = Column(String(100), primary_key=True)
    pool_name = Column(String(20), nullable=False)
    alpha = Column(Numeric(10, 4), default=1.0)
    beta = Column(Numeric(10, 4), default=1.0)
    total_sessions = Column(Integer, default=0)
    total_successes = Column(Integer, default=0)
    avg_confidence = Column(Numeric(5, 2), default=50.0)
    updated_at = Column(DateTime(timezone=True), default=func.now())

    @property
    def mean(self):
        return float(self.alpha) / (float(self.alpha) + float(self.beta))


class AgentBeliefHistory(Base):
    __tablename__ = "agent_belief_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String(100), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.session_id", ondelete="SET NULL"))
    prior_alpha = Column(Numeric(10, 4))
    prior_beta = Column(Numeric(10, 4))
    posterior_alpha = Column(Numeric(10, 4))
    posterior_beta = Column(Numeric(10, 4))
    was_selected = Column(Boolean)
    was_successful = Column(Boolean)
    created_at = Column(DateTime(timezone=True), default=func.now())


class AgentSelectionLog(Base):
    __tablename__ = "agent_selection_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.session_id", ondelete="CASCADE"))
    agent_name = Column(String(100), nullable=False)
    pool_name = Column(String(20), nullable=False)
    was_called = Column(Boolean, nullable=False)
    success_flag = Column(Boolean)
    reward = Column(Numeric(10, 6))
    created_at = Column(DateTime(timezone=True), default=func.now())


class KARLDecisionRecord(Base):
    __tablename__ = "karl_decision_records"
    decision_id = Column(UUID(as_uuid=True), primary_key=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.session_id", ondelete="SET NULL"))
    symbol = Column(String(20))
    price = Column(Numeric(20, 8))
    timeframe = Column(String(20))
    regime = Column(String(20))
    state_hash = Column(String(32))
    top_trajectories_json = Column(Text)
    selected_ensemble_json = Column(Text)
    q_values_json = Column(Text)
    q_star = Column(Numeric(8, 6))
    advantage = Column(Numeric(8, 6))
    uncertainty_aleatoric = Column(Numeric(6, 4))
    uncertainty_epistemic = Column(Numeric(6, 4))
    uncertainty_total = Column(Numeric(6, 4))
    confidence_raw = Column(Integer)
    confidence_final = Column(Integer)
    confidence_adjustments_json = Column(Text)
    final_action = Column(String(20))
    position_pct = Column(Numeric(6, 4))
    kpi_snapshot_json = Column(Text)
    metadata_json = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now())

    session = relationship("Session", back_populates="decisions")


class OAPValidationHistory(Base):
    __tablename__ = "oap_validation_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    decision_id = Column(UUID(as_uuid=True))
    status = Column(String(20))
    confidence = Column(Integer)
    position_pct = Column(Numeric(6, 4))
    confidence_boost = Column(Integer)
    regime = Column(String(20))
    issues_json = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now())


class KPIMetrics(Base):
    __tablename__ = "kpi_metrics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    decision_id = Column(UUID(as_uuid=True))
    metric_name = Column(String(50), nullable=False)
    metric_value = Column(Numeric(12, 6))
    regime = Column(String(20))
    created_at = Column(DateTime(timezone=True), default=func.now())


class RewardCalibration(Base):
    __tablename__ = "reward_calibration"
    id = Column(Integer, primary_key=True, autoincrement=True)
    n_bins = Column(Integer, default=10)
    slope = Column(Numeric(8, 6), default=1.0)
    intercept = Column(Numeric(8, 6), default=0.0)
    calibration_error = Column(Numeric(8, 6))
    fitted = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), default=func.now())


class BacktestRun(Base):
    __tablename__ = "backtest_runs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.session_id", ondelete="SET NULL"))
    symbol = Column(String(20), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    timeframe = Column(String(20))
    win_rate = Column(Numeric(5, 4))
    sharpe_ratio = Column(Numeric(8, 4))
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    avg_win_pct = Column(Numeric(8, 4))
    avg_loss_pct = Column(Numeric(8, 4))
    total_return_pct = Column(Numeric(10, 4))
    max_drawdown_pct = Column(Numeric(10, 4))
    avg_confidence = Column(Numeric(5, 2))
    initial_capital = Column(Numeric(20, 8))
    final_capital = Column(Numeric(20, 8))
    created_at = Column(DateTime(timezone=True), default=func.now())


class RAGEmbedding(Base):
    """Vector embeddings for RAG — uses JSON for embedding vector."""

    __tablename__ = "rag_embeddings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_id = Column(String(100), nullable=False)
    domain = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    embedding_json = Column(Text)  # vector stored as JSON array
    metadata_json = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now())


class KARLTrajectory(Base):
    """Complete trajectory for KARL replay buffer."""

    __tablename__ = "karl_trajectories"
    trajectory_id = Column(String(100), primary_key=True)
    symbol = Column(String(20))
    regime = Column(String(20))
    outcome = Column(Numeric(10, 6))
    total_reward = Column(Numeric(10, 6))
    sharpe_ratio = Column(Numeric(8, 4))
    max_drawdown = Column(Numeric(8, 4))
    win_rate = Column(Numeric(5, 4))
    trade_count = Column(Integer)
    avg_confidence = Column(Numeric(5, 2))
    regime_stability = Column(Numeric(5, 4))
    steps_json = Column(Text)
    metadata_json = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now())

    steps = relationship("KARLTrajectoryStep", back_populates="trajectory")


class KARLTrajectoryStep(Base):
    """Individual step within a KARL trajectory."""

    __tablename__ = "karl_trajectory_steps"
    id = Column(Integer, primary_key=True, autoincrement=True)
    trajectory_id = Column(String(100), ForeignKey("karl_trajectories.trajectory_id", ondelete="CASCADE"))
    step_index = Column(Integer)
    state_json = Column(Text)
    action = Column(String(20))
    reward = Column(Numeric(10, 6))
    confidence = Column(Integer)
    regime = Column(String(20))
    created_at = Column(DateTime(timezone=True), default=func.now())

    trajectory = relationship("KARLTrajectory", back_populates="steps")
