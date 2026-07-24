from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from agents._impl.amre import (
    SelfQuestioningEngine,
    build_decision_record,
    check_delisted_fallback,
    get_audit_log,
    get_calibrator,
    get_dd_tracker,
    get_karl_diagnostics,
    get_oap_optimizer,
    get_reward_diagnostics,
    run_backtest_on_bars,
    should_trigger_self_questioning,
    validate_with_grounding,
)
from agents._impl.amre import create_backtest_runner, estimate_uncertainty
from agents._impl.amre.lag_windowing import get_lag_window
from agents._impl.amre.reward import RewardState
from agents._impl.amre.risk_control import apply_position_lag_risk
from agents._impl.amre.trajectory import MarketState, market_state_hash
from agents._impl.synthesis_agent import SynthesisAgent
from agents.base_agent import AgentResponse

# ── P2-04: extracted conflict resolution + weight calibration ───────────────
from agents._impl.amre.conflict_resolver import (
    CONFLICT_THRESHOLD,
    WEIGHT_REDUCTION,
    detect_bull_bear_conflict,
    resolve_bull_bear_conflict,
    resolve_conflict,  # noqa: F401 — backward-compat re-export
)
from agents._impl.amre.weights_calibrator import (
    WARMUP_THRESHOLD,
    apply_lag_smoothing,
    compute_state_hash,
    estimate_karl_reward,
)

logger = logging.getLogger(__name__)
"""agents/karl_synthesis.py — KARL-013: SynthesisAgent + AMRE Integration.
P2-04 refactored: reward/lag → weights_calibrator.py, conflicts → conflict_resolver.py.

Оборачивает SynthesisAgent в AMRE-контур:
  DecisionRecord → OAP update → Backtest sample → Sync audit

Использование:
    from agents.karl_synthesis import KARLSynthesisAgent
    result = await karl_agent.run(state)
"""


# ATOM-019: PostgreSQL integration
try:
    from db import (
        AgentSignalRepository,
        AstroPositionRepository,
        DecisionRecordRepository,
        is_postgres_available,
    )

    PG_AVAILABLE = is_postgres_available()
except Exception:
    PG_AVAILABLE = False
    DecisionRecordRepository = None
    AgentSignalRepository = None
    AstroPositionRepository = None


# ─── KARL Synthesis Agent ────────────────────────────────────────────────────


class KARLSynthesisAgent:
    """SynthesisAgent + Full AMRE/KARL Control Loop.

    Adds to SynthesisAgent:
    - DecisionRecord на каждое решение
    - OAPOptimizer.update_from_decision() после синтеза
    - ContinuousBacktest sample
    - Self-questioning engine (optional)
    - Periodic sync_with_audit()

    P2-04: reward/lag/conflict logic extracted to weights_calibrator + conflict_resolver.
    """

    def __init__(
        self,
        sync_interval: int = 10,
        enable_self_question: bool = False,
        enable_backtest: bool = True,
        backtest_horizon: int = 5,
    ):
        self.base_agent = SynthesisAgent()
        self.sync_interval = sync_interval
        self.enable_self_question = enable_self_question
        self.enable_backtest = enable_backtest

        self.decision_counter = 0
        self.self_questioner = SelfQuestioningEngine() if enable_self_question else None
        self.backtest = (
            create_backtest_runner(horizon=backtest_horizon)
            if enable_backtest
            else None
        )
        self.oap = get_oap_optimizer()
        self.calibrator = get_calibrator()
        self.dd_tracker = get_dd_tracker()
        self.reward_state = RewardState()
        self.lag_window = get_lag_window()
        self.lag_enabled = True

    async def run(self, state: dict) -> dict[str, Any]:
        """Run synthesis + AMRE post-processing.

        Returns dict with:
          - synthesis_result: AgentResponse.to_dict()
          - amre_output: AMREOutput dataclass
          - decision_record: DecisionRecord.to_dict()
          - karl_diagnostics: get_karl_diagnostics()
        """
        symbol = state.get("symbol", "BTCUSDT")
        regime = state.get("regime", "NORMAL")
        all_signals = state.get("all_signals", [])

        # Delisted ticker fallback
        delist_fb = check_delisted_fallback(symbol)
        if delist_fb:
            state = {**state, "symbol": delist_fb.fallback_symbol}

        # ── Step 1: Market state ──────────────────────────────────────────
        price = state.get("current_price", 50000)
        ms = MarketState(
            symbol=symbol,
            price=price,
            timeframe=state.get("timeframe_requested", "SWING"),
            n_signals=len(all_signals),
            session_id=state.get("session_id", str(uuid.uuid4())[:8]),
            timestamp=datetime.now(timezone.utc).isoformat(),
            regime=regime,
        )
        market_state_hash(ms)

        # ── Step 2: Base synthesis ─────────────────────────────────────────
        synthesis_result = await self.base_agent.run(state)
        if isinstance(synthesis_result, AgentResponse):
            synth_dict = synthesis_result.to_dict()
        else:
            synth_dict = synthesis_result

        signal = synth_dict.get("signal", "NEUTRAL")
        confidence = synth_dict.get("confidence", 50)

        # ── Step 3: Self-questioning ──────────────────────────────────────
        sq_result = None
        sq_reason = "not_enabled"
        if self.self_questioner:
            need_sq, sq_reason = should_trigger_self_questioning(
                signals=all_signals,
                regime=regime,
                final_confidence=confidence / 100.0,
            )
            if need_sq:
                logger.info(f"[SelfQ Trigger] {sq_reason} — running self-questioning")
                sq_result = self.self_questioner.ask(all_signals, state)
                if sq_result.confidence_adjustment != 0:
                    confidence = max(30, min(92, confidence + sq_result.confidence_adjustment))
                    synth_dict["reasoning"] = (
                        f"[SelfQ] {sq_result.question} → {sq_result.answer}. "
                        f"{synth_dict.get('reasoning', '')}"
                    )
            elif self.decision_counter % 5 == 0:
                logger.info(f"[SelfQ Skip] reason={sq_reason}")

        # ── Step 4: Uncertainty + Grounding ──────────────────────────────
        uncertainty = estimate_uncertainty(all_signals)
        grounding = validate_with_grounding(
            state, all_signals, current_confidence=confidence
        )
        grounding_factor = grounding.get("grounding_factor", 1.0)
        if grounding_factor < 1.0:
            confidence = max(30, round(confidence * grounding_factor))
            logger.info(
                f"[Grounding] factor={grounding_factor:.3f} → conf {confidence} (degraded)"
            )

        # ── Step 5: Lag Windowing (P2-04 → weights_calibrator) ───────────
        position_pct = synth_dict.get("metadata", {}).get("position_size", 0.02)
        confidence, position_pct, lag_meta = apply_lag_smoothing(
            self.lag_window, confidence, position_pct, self.lag_enabled
        )

        # Risk control
        risk_adjusted = False
        if lag_meta.get("window_mature", False):
            new_pos = apply_position_lag_risk(
                position_pct, lag_meta.get("position_lag", 0.0)
            )
            if new_pos != position_pct:
                position_pct = new_pos
                risk_adjusted = True
                logger.info(
                    f"[RiskControl] position adjusted: "
                    f"lag={lag_meta.get('position_lag', 0.0):+.3f} → {position_pct:.4f}"
                )

        synth_dict["lag_metrics"] = lag_meta
        if risk_adjusted:
            synth_dict["metadata"] = {
                **(synth_dict.get("metadata", {})),
                "position_risk_adjusted": True,
            }

        # ── Step 6: Reward estimation (P2-04 → weights_calibrator) ──────
        from agents._impl.amre.trajectory import MarketState as MS

        reward = estimate_karl_reward(
            state=state,
            signals=all_signals,
            confidence=confidence,
            signal=signal,
            reward_state=self.reward_state,
            market_state_cls=MS,
        )

        # ── Step 7: State hash (P2-04 → weights_calibrator) ─────────────
        state_hash = compute_state_hash(state, signal, confidence, regime)

        # ── Step 7.5: Bull/Bear conflict resolution (P2-04 → conflict_resolver) ──
        conflict = resolve_bull_bear_conflict(all_signals)
        if conflict["has_conflict"]:
            confidence = max(30, confidence - conflict["confidence_penalty"])

        # ── Step 8: DecisionRecord ────────────────────────────────────────
        def _sig_get(s, key, default=None):
            if hasattr(s, key):
                return getattr(s, key)
            if isinstance(s, dict):
                return s.get(key, default)
            return default

        selected_ensemble = [
            {
                "name": _sig_get(s, "agent_name", "unknown"),
                "signal": _sig_get(s, "signal", "NEUTRAL"),
                "confidence": _sig_get(s, "confidence", 50),
                "weight": 0.0,
                "q_value": 0.0,
            }
            for s in all_signals
        ]

        top_trajectories = [
            {
                "id": f"traj_{self.decision_counter}",
                "depth": 0,
                "action": signal,
                "q_value": reward,
                "advantage": reward - 0.5,
                "uncertainty": uncertainty.get("total", 0.5),
                "confidence": confidence,
                "policy": "karl_synthesis",
            }
        ]

        oap_state = self.oap.kpi_state
        kpi_snapshot = {
            "oos_fail_rate": oap_state.oos_fail_rate,
            "entropy": oap_state.entropy_avg,
            "uncertainty": uncertainty.get("total", 0.5),
            "avg_confidence": confidence,
            "sharpe_ratio": 0.0,
            "win_rate": 0.0,
            "regime_stability": 1.0,
            "exploration_rate": oap_state.current_exploration_rate,
            "ttc_depth": oap_state.current_ttc_depth,
            "grounding_strength": oap_state.current_grounding_strength,
        }

        confidence_adjustments = []
        if grounding.get("confidence_adjustment", 0) != 0:
            confidence_adjustments.append(f"grounding:{grounding['confidence_adjustment']}")
        if sq_result is not None and sq_result.confidence_adjustment != 0:
            confidence_adjustments.append(f"self_q:{sq_result.confidence_adjustment}")
        if conflict["has_conflict"]:
            confidence_adjustments.append(f"conflict:-{conflict['confidence_penalty']}")

        record = build_decision_record(
            decision_id=f"KARL_{self.decision_counter:04d}_{symbol}",
            session_id=state.get("session_id", "unknown"),
            symbol=symbol,
            price=price,
            timeframe=state.get("timeframe_requested", "SWING"),
            regime=regime,
            state_hash=state_hash,
            top_trajectories=top_trajectories,
            selected_ensemble=selected_ensemble,
            q_values=[reward],
            q_star=reward,
            uncertainty=uncertainty,
            confidence_raw=synth_dict.get("confidence", 50),
            confidence_final=confidence,
            confidence_adjustments=confidence_adjustments,
            final_action=signal,
            position_pct=synth_dict.get("metadata", {}).get("position_size", 0.02),
            kpi_snapshot=kpi_snapshot,
            metadata={
                "delist_fallback": delist_fb.reason if delist_fb else None,
                "uncertainty_aleatoric": uncertainty.get("aleatoric", 0.0),
                "uncertainty_epistemic": uncertainty.get("epistemic", 0.0),
                "grounding_passed": grounding.get("passed", True),
                "grounding_issues": grounding.get("issues", [])[:3],
                "grounding_factor": grounding.get("grounding_factor", 1.0),
                "conflict_divergence": conflict.get("divergence", 0.0),
            },
            risk_adjusted_pnl=0.0,
        )

        # ── Step 9: Record to audit log ──────────────────────────────────
        audit_log = get_audit_log()
        audit_log.record(record)

        if PG_AVAILABLE and DecisionRecordRepository:
            try:
                DecisionRecordRepository.save(record.to_dict())
                for s in all_signals:
                    if AgentSignalRepository:
                        AgentSignalRepository.save(
                            session_id=state.get("session_id", "unknown"),
                            agent_name=_sig_get(s, "agent_name", "unknown"),
                            signal=_sig_get(s, "signal", "NEUTRAL"),
                            confidence=_sig_get(s, "confidence", 50),
                            reasoning=_sig_get(s, "reasoning", "")[:500],
                            metadata=_sig_get(s, "metadata", {}),
                        )
            except Exception as e:
                logger.info(f"[KARL] PostgreSQL save failed: {e}")

        # ── Step 10: OAP + Calibrator + DD + Backtest ────────────────────
        self.oap.sync_with_audit()
        self.calibrator.add_sample(confidence, reward)
        self.dd_tracker.add_trade(reward)

        if self.backtest and self.enable_backtest:
            try:
                self.backtest.add_sample(
                    state=ms, decision=record, reward=reward, signals=all_signals
                )
            except Exception:
                pass

        # ── Step 11: Periodic recalibration ──────────────────────────────
        self.decision_counter += 1
        if self.decision_counter % self.sync_interval == 0:
            self._sync_and_recalibrate()

        # ── Step 12: Return enriched result ──────────────────────────────
        synth_dict["confidence"] = confidence
        synth_dict["metadata"] = {
            **(synth_dict.get("metadata", {})),
            "karl_enabled": True,
            "decision_id": record.decision_id,
            "uncertainty": uncertainty,
            "grounding": grounding,
            "amre_passed": grounding.get("passed", True),
            "delist_fallback": delist_fb.reason if delist_fb else None,
            "kpi_snapshot": kpi_snapshot,
            "conflict_resolved": conflict["has_conflict"],
        }

        return {
            "synthesis_result": synth_dict,
            "amre_output": {
                "reward_estimate": round(reward, 4),
                "uncertainty": uncertainty,
                "grounding_passed": grounding.get("passed", True),
                "confidence_final": confidence,
            },
            "decision_record": record.to_dict(),
            "karl_diagnostics": get_karl_diagnostics(),
        }

    def _sync_and_recalibrate(self):
        """Periodic self-assessment — calls sync_with_audit to update KPIs."""
        self.oap.sync_with_audit()

    def sync_with_audit(self) -> dict[str, Any]:
        """Manual trigger: sync_with_audit()."""
        audit_log = get_audit_log()
        drift = audit_log.analyze_drift()
        karl_diag = get_karl_diagnostics()
        if drift.get("status") == "degrading":
            self._sync_and_recalibrate()
        return {
            "drift_analysis": drift,
            "karl_diagnostics": karl_diag,
            "calibrator_diagnostics": get_reward_diagnostics(),
            "decision_count": self.decision_counter,
        }

    # ── P2-04 backward-compatible wrappers (delegate to standalone functions) ──

    def _estimate_reward(
        self, state: dict, signals: list, confidence: int, signal: str
    ) -> float:
        """Thin wrapper → weights_calibrator.estimate_karl_reward()."""
        from agents._impl.amre.weights_calibrator import estimate_karl_reward

        return estimate_karl_reward(
            state, signals, confidence, signal,
            self.reward_state, MarketState,
        )

    def _apply_lag_smoothing(
        self, confidence: int, position_pct: float
    ) -> tuple[int, float, dict]:
        """Thin wrapper → weights_calibrator.apply_lag_smoothing()."""
        from agents._impl.amre.weights_calibrator import apply_lag_smoothing

        return apply_lag_smoothing(
            self.lag_window, confidence, position_pct, self.lag_enabled,
        )

    def run_backtest_on_historical(
        self, bars: list, symbol: str = "BTCUSDT"
    ) -> dict[str, Any]:
        """Run continuous backtest on historical bars."""
        if not self.backtest:
            return {"error": "backtest not enabled"}
        return run_backtest_on_bars(
            agent_run_fn=lambda state: self.run(state),
            bars=bars,
            symbol=symbol,
        )

    def get_status(self) -> dict[str, Any]:
        """Get KARL system status."""
        return {
            "decision_counter": self.decision_counter,
            "sync_interval": self.sync_interval,
            "self_question_enabled": self.enable_self_question,
            "backtest_enabled": self.enable_backtest,
            "karl_diagnostics": get_karl_diagnostics(),
            "drift_status": get_audit_log().analyze_drift(),
        }


# ─── Global singleton ─────────────────────────────────────────────────────────

_KARL_AGENT: Optional["KARLSynthesisAgent"] = None


def get_karl_agent() -> KARLSynthesisAgent:
    global _KARL_AGENT
    if _KARL_AGENT is None:
        _KARL_AGENT = KARLSynthesisAgent()
    return _KARL_AGENT