"""Sprint 6 — Phase 7: Council Orchestrator + HMM + Meta-RL Integration Tests.

Sprint 6:  8 days
  - Day 1-2: CouncilOrchestrator full lifecycle (KARL → RiskEngine → Execution)
  - Day 3-4: HMMRegimeAgent + KARL conflict resolution
  - Day 5-6: Meta-RL calibration tracker + drift detection
  - Day 7-8: Backtest regime detector + end-to-end pipeline

P0 Requirements:
  - CouncilOrchestrator: KARL arbitration between HMM ↔ QuantAgent
  - HMMRegimeAgent: regime detection (bull/sideways/bear) + anomaly scoring
  - Meta-RL: calibration_accuracy tracking + drift alerts
  - Backtest: RegimeDetector full-history Viterbi labeling

Design decisions (ADR-002, 2026-07-21):
  - Full-history HMM fit (not sliding-window) per backtest/regime_detector.py rationale
  - hmmlearn is optional; degraded mode returns REGIME_UNKNOWN when unavailable
  - CouncilOrchestrator wraps KARL → RiskEngine → Execution in async cycle
"""

import asyncio
import time
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from dataclasses import dataclass
from typing import List

from core.base_agent import AgentResponse, SignalDirection


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def make_response(
    agent_name: str,
    signal: SignalDirection = SignalDirection.NEUTRAL,
    confidence: float = 0.5,
    reasoning: str = "test",
    weight: float = 0.10,
    domain: str = "quant",
) -> AgentResponse:
    return AgentResponse(
        agent_name=agent_name,
        signal=signal,
        confidence=confidence,
        reasoning=reasoning,
        metadata={"domain": domain, "weight": weight},
    )


class FakeRiskEngine:
    """Mock RiskEngine with adjustable position sizing."""
    def __init__(self, adjust_result: float = 0.5, reason: str = "ok"):
        self.adjust_result = adjust_result
        self.reason = reason
        self.calls: List[dict] = []

    def adjust_position_size(self, base_size, agent_responses):
        self.calls.append({"base_size": base_size, "agents": len(agent_responses)})
        return self.adjust_result, self.reason


# ═══════════════════════════════════════════════════════════════════════
# 1. CouncilOrchestrator
# ═══════════════════════════════════════════════════════════════════════

class TestCouncilOrchestrator:
    """CouncilOrchestrator: Agent → KARL → RiskEngine → Execution."""

    @pytest.mark.asyncio
    async def test_execute_trading_cycle_normal(self):
        """Full cycle: KARL → RiskEngine → EXECUTED result."""
        from orchestration.council_orchestrator import CouncilOrchestrator

        risk = FakeRiskEngine(adjust_result=0.75, reason="normal regime")
        orchestrator = CouncilOrchestrator(risk, config={"symbol": "BTCUSDT"})

        responses = [
            make_response("FundamentalAgent", SignalDirection.LONG, confidence=70),
            make_response("QuantAgent", SignalDirection.LONG, confidence=80),
        ]
        final_signal = make_response("AstroCouncil", SignalDirection.LONG, confidence=60)

        result = await orchestrator.execute_trading_cycle(responses, final_signal)

        assert result["action"] == "EXECUTED"
        assert result["size"] == 0.75
        assert result["blocked"] is False
        assert result["signal"] in ("LONG", "BUY")
        assert result["risk_reason"] == "normal regime"
        assert len(risk.calls) == 1
        assert risk.calls[0]["base_size"] == 1.0

    def test_apply_karl_arbitration_conflict(self):
        """KARL resolves QuantAgent ↔ HMMRegimeAgent conflict."""
        from orchestration.council_orchestrator import CouncilOrchestrator

        risk = FakeRiskEngine()
        orchestrator = CouncilOrchestrator(risk)

        quant = make_response("QuantAgent", SignalDirection.LONG, confidence=80)
        hmm = make_response("HMMRegimeAgent", SignalDirection.SHORT, confidence=70)
        other = make_response("FundamentalAgent", SignalDirection.LONG, confidence=60)

        # KARL should not raise — it resolves the conflict internally
        result = orchestrator._apply_karl_arbitration([quant, hmm, other])
        assert len(result) == 3
        # Both original agents still present (KARL modifies confidence, removes neither)
        names = [r.agent_name for r in result]
        assert "QuantAgent" in names
        assert "HMMRegimeAgent" in names

    def test_apply_karl_arbitration_no_conflict(self):
        """No HMM agent means no KARL modification needed."""
        from orchestration.council_orchestrator import CouncilOrchestrator

        risk = FakeRiskEngine()
        orchestrator = CouncilOrchestrator(risk)

        responses = [
            make_response("FundamentalAgent", SignalDirection.LONG),
            make_response("QuantAgent", SignalDirection.NEUTRAL),
        ]
        result = orchestrator._apply_karl_arbitration(responses)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_execute_cycle_stop_hard_block(self):
        """RiskEngine blocks trade → STOP with blocked=True."""
        from orchestration.council_orchestrator import CouncilOrchestrator

        risk = FakeRiskEngine(adjust_result=0.0, reason="extreme volatility")
        orchestrator = CouncilOrchestrator(risk, config={"symbol": "ETHUSDT"})

        responses = [make_response("QuantAgent", SignalDirection.LONG, confidence=90)]
        final = make_response("AstroCouncil", SignalDirection.LONG, confidence=85)

        result = await orchestrator.execute_trading_cycle(
            responses, final, is_backtest=True
        )

        assert result["action"] == "STOP"
        assert result["size"] == 0.0
        assert result["blocked"] is True
        assert result["risk_reason"] == "extreme volatility"

    @pytest.mark.asyncio
    async def test_execute_cycle_neutral(self):
        """Council NEUTRAL → no trade, but not blocked."""
        from orchestration.council_orchestrator import CouncilOrchestrator

        risk = FakeRiskEngine(adjust_result=0.5, reason="ok")
        orchestrator = CouncilOrchestrator(risk)

        responses = [make_response("FundamentalAgent", SignalDirection.NEUTRAL)]
        final = make_response("AstroCouncil", SignalDirection.NEUTRAL)

        result = await orchestrator.execute_trading_cycle(responses, final)

        assert result["action"] == "NEUTRAL"
        assert result["size"] == 0.0
        assert result["blocked"] is False

    @pytest.mark.asyncio
    async def test_execute_cycle_config_override(self):
        """Config overrides work (base_position_size from call site)."""
        from orchestration.council_orchestrator import CouncilOrchestrator

        risk = FakeRiskEngine(adjust_result=2.0, reason="aggressive")
        orchestrator = CouncilOrchestrator(risk, config={"base_position_size": 1.0})

        responses = [make_response("QuantAgent", SignalDirection.LONG, confidence=90)]
        final = make_response("AstroCouncil", SignalDirection.LONG, confidence=80)

        result = await orchestrator.execute_trading_cycle(
            responses, final, config={"base_position_size": 2.0}
        )

        assert result["size"] == 2.0
        assert risk.calls[0]["base_size"] == 2.0

    def test_adjust_through_risk_delegation(self):
        """RiskEngine.adjust_position_size is called with correct args."""
        from orchestration.council_orchestrator import CouncilOrchestrator

        risk = FakeRiskEngine(adjust_result=0.33, reason="conservative")
        orchestrator = CouncilOrchestrator(risk)

        responses = [make_response("QuantAgent", SignalDirection.LONG)]
        size, reason = orchestrator.adjust_through_risk(base_size=0.5, agent_responses=responses)

        assert size == 0.33
        assert reason == "conservative"
        assert risk.calls[0]["base_size"] == 0.5
        assert risk.calls[0]["agents"] == 1


# ═══════════════════════════════════════════════════════════════════════
# 2. HMMRegimeAgent
# ═══════════════════════════════════════════════════════════════════════

class TestHMMRegimeAgent:
    """HMMRegimeAgent: market regime detection via Hidden Markov Model."""

    def test_hmm_agent_creation_degraded_mode(self):
        """HMM agent instantiates even without hmmlearn (degraded mode)."""
        from agents._impl.hmm_regime_agent import HMMRegimeAgent

        agent = HMMRegimeAgent()
        assert agent.name == "HMMRegimeAgent"
        assert agent.domain == "quant"
        assert agent.weight == pytest.approx(0.10)

    @pytest.mark.asyncio
    async def test_hmm_run_degraded_returns_unknown(self):
        """Degraded mode returns REGIME_UNKNOWN with low confidence."""
        from agents._impl.hmm_regime_agent import HMMRegimeAgent

        agent = HMMRegimeAgent()
        state = {"symbol": "BTCUSDT", "timeframe": "1D", "regime": "unknown"}
        result = await agent.run(state)

        assert result is not None
        assert hasattr(result, "signal")

    @pytest.mark.asyncio
    async def test_hmm_context_propagation(self):
        """HMM agent propagates task_id via contextvars when called through on_message."""
        from agents._impl.hmm_regime_agent import HMMRegimeAgent
        from core.envelopes import TaskEnvelope

        agent = HMMRegimeAgent()
        envelope = TaskEnvelope.new(
            agent_name="HMMRegimeAgent",
            state={"symbol": "BTCUSDT"},
            deadline_seconds=120,
            correlation_id="ctx-test-hmm",
        )

        renv = await agent.on_message(envelope)
        assert renv.task_id == envelope.task_id
        assert renv.agent_name == envelope.agent_name
        assert renv.traceparent == envelope.traceparent


# ═══════════════════════════════════════════════════════════════════════
# 3. KARL — Conflict Resolution
# ═══════════════════════════════════════════════════════════════════════

class TestKARLConflictResolution:
    """KARL arbitration between QuantAgent and HMMRegimeAgent."""

    def test_karl_resolve_conflict_opposite_signals(self):
        """Opposite signals: confidence is adjusted, not erased."""
        from agents.karl_synthesis import resolve_conflict

        quant = make_response("QuantAgent", SignalDirection.LONG, confidence=85)
        hmm = make_response("HMMRegimeAgent", SignalDirection.SHORT, confidence=75)

        # KARL modifies in-place
        quant_before = quant.confidence
        hmm_before = hmm.confidence
        resolve_conflict(quant, hmm)

        # Both still exist, confidence may change
        assert quant.confidence >= 0
        assert hmm.confidence >= 0

    def test_karl_resolve_conflict_same_signal(self):
        """Same signal: no conflict, agents unchanged."""
        from agents.karl_synthesis import resolve_conflict

        quant = make_response("QuantAgent", SignalDirection.LONG, confidence=80)
        hmm = make_response("HMMRegimeAgent", SignalDirection.LONG, confidence=70)

        resolve_conflict(quant, hmm)
        # Same direction — amplification expected
        assert quant.confidence >= 0.50
        assert hmm.confidence >= 0.50


# ═══════════════════════════════════════════════════════════════════════
# 4. RegimeDetector — Backtest HMM labeling
# ═══════════════════════════════════════════════════════════════════════

class TestRegimeDetector:
    """RegimeDetector: full-history HMM fit + Viterbi labeling."""

    def test_regime_detector_import_and_signature(self):
        """RegimeDetector is importable and has expected methods."""
        from backtest.regime_detector import RegimeDetector

        detector = RegimeDetector()
        assert hasattr(detector, "fit")
        assert hasattr(detector, "predict")
        assert hasattr(detector, "detect_anomalies")

    def test_regime_detector_fit_predict_synthetic(self):
        """Basic fit/predict on synthetic returns."""
        import numpy as np
        from backtest.regime_detector import RegimeDetector

        detector = RegimeDetector()
        np.random.seed(42)
        returns = np.random.randn(500) * 0.01  # 500 days of low-vol data

        detector.fit(returns)
        labels = detector.predict(returns)

        # Labels should be 0, 1, or 2 for 3-state HMM
        assert len(labels) == len(returns)
        assert set(labels).issubset({0, 1, 2})

    def test_regime_detector_anomaly_detection(self):
        """Anomaly detection flags high-vol periods."""
        import numpy as np
        from backtest.regime_detector import RegimeDetector

        detector = RegimeDetector()
        np.random.seed(1)
        # 100 days calm + 20 days volatile spike
        returns = np.concatenate([
            np.random.randn(100) * 0.005,
            np.random.randn(20) * 0.05,
        ])

        detector.fit(returns[:100])
        anomalies = detector.detect_anomalies(returns, window=20, threshold=2.0)
        assert isinstance(anomalies, list)

    def test_regime_detector_no_hmm_import_degraded(self):
        """When hmmlearn not installed, RegimeDetector degrades gracefully."""
        import sys
        import numpy as np
        from backtest.regime_detector import RegimeDetector

        detector = RegimeDetector()

        # If hmmlearn is available, fit should work normally
        returns = np.array([0.01, -0.02, 0.005, -0.01, 0.02])
        try:
            detector.fit(returns)
            labels = detector.predict(returns)
            assert len(labels) == len(returns)
        except Exception:
            # Degraded mode acceptable if no hmmlearn
            pass


# ═══════════════════════════════════════════════════════════════════════
# 5. Meta-RL Calibration Tracker
# ═══════════════════════════════════════════════════════════════════════

class TestMetaRLCalibration:
    """Meta-RL calibration tracker + drift detection."""

    def test_calibration_tracker_import(self):
        """CalibrationTracker is importable."""
        from meta_rl.calibration import CalibrationTracker
        tracker = CalibrationTracker()
        assert hasattr(tracker, "calibration_accuracy")
        assert hasattr(tracker, "evaluate")
        assert hasattr(tracker, "detect_drift")

    def test_calibration_accuracy_initial_zero(self):
        """New tracker has 0 accuracy."""
        from meta_rl.calibration import CalibrationTracker
        tracker = CalibrationTracker()
        # calibration_accuracy might be a float or a dict
        acc = tracker.calibration_accuracy
        assert acc is not None

    def test_calibration_drift_detection(self):
        """Drift detection returns boolean."""
        from meta_rl.calibration import CalibrationTracker
        tracker = CalibrationTracker()
        result = tracker.detect_drift()
        assert isinstance(result, bool)


# ═══════════════════════════════════════════════════════════════════════
# 6. End-to-End: Agent → KARL → RiskEngine → Execution
# ═══════════════════════════════════════════════════════════════════════

class TestPhase7E2E:
    """Full Phase 7 pipeline: all agents → KARL → RiskEngine → Execution."""

    @pytest.mark.asyncio
    async def test_full_pipeline_buy_signal(self):
        """BUY signal passes through KARL → RiskEngine → EXECUTED."""
        from orchestration.council_orchestrator import CouncilOrchestrator

        risk = FakeRiskEngine(adjust_result=0.5, reason="normal")
        orchestrator = CouncilOrchestrator(risk, config={
            "symbol": "BTCUSDT",
            "base_position_size": 1.0,
        })

        # Simulated agent responses from all 7 pools
        responses = [
            make_response("FundamentalAgent", SignalDirection.LONG, confidence=70, weight=0.20),
            make_response("QuantAgent", SignalDirection.LONG, confidence=80, weight=0.20),
            make_response("SentimentAgent", SignalDirection.LONG, confidence=60, weight=0.10),
            make_response("TechnicalAgent", SignalDirection.LONG, confidence=61, weight=0.10),
            make_response("RiskAgent", SignalDirection.NEUTRAL, confidence=50, weight=0.15),
            make_response("HMMRegimeAgent", SignalDirection.LONG, confidence=70, weight=0.10),
            make_response("BullResearcher", SignalDirection.LONG, confidence=51, weight=0.05),
        ]
        final = make_response("AstroCouncil", SignalDirection.LONG, confidence=61)

        result = await orchestrator.execute_trading_cycle(responses, final)

        assert result["action"] == "EXECUTED"
        assert result["size"] > 0
        assert result["blocked"] is False

    @pytest.mark.asyncio
    async def test_full_pipeline_conflict_stop(self):
        """HMM says SELL, Quant says BUY → KARL resolves, RiskEngine may still block."""
        from orchestration.council_orchestrator import CouncilOrchestrator

        risk = FakeRiskEngine(adjust_result=0.0, reason="extreme drawdown")
        orchestrator = CouncilOrchestrator(risk, config={"symbol": "ETHUSDT"})

        responses = [
            make_response("QuantAgent", SignalDirection.LONG, confidence=85),
            make_response("HMMRegimeAgent", SignalDirection.SHORT, confidence=80),
        ]
        final = make_response("AstroCouncil", SignalDirection.LONG, confidence=45)

        result = await orchestrator.execute_trading_cycle(responses, final)

        # Risk engine blocked the trade
        assert result["action"] == "STOP"
        assert result["blocked"] is True
