from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from agents._impl.amre import (
    SelfQuestioningEngine,
    # Audit
    build_decision_record,
    check_delisted_fallback,
    # Reward
    compute_trajectory_reward,
    create_backtest_runner,
    # Uncertainty + Grounding
    estimate_uncertainty,
    get_audit_log,
    get_calibrator,
    get_dd_tracker,
    get_karl_diagnostics,
    # OAP
    get_oap_optimizer,
    get_reward_diagnostics,
    # AMRE output
    run_backtest_on_bars,
    should_trigger_self_questioning,
    validate_with_grounding,
)
from agents._impl.amre.lag_windowing import get_lag_window
from agents._impl.amre.reward import (
    RewardState,
    update_reward_ema,
)
from agents._impl.amre.risk_control import apply_position_lag_risk
from agents._impl.amre.trajectory import MarketState, market_state_hash
from agents._impl.synthesis_agent import SynthesisAgent
from agents.base_agent import AgentResponse

logger = logging.getLogger(__name__)
"""agents/karl_synthesis.py — KARL-013: SynthesisAgent + AMRE Integration
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
# ATOM-KARL-015 Phase 5: Lag Windowing

# ─── KARL Synthesis Agent ────────────────────────────────────────────────────────


class KARLSynthesisAgent:
    """
    SynthesisAgent + Full AMRE/KARL Control Loop.

    Adds to SynthesisAgent:
    - DecisionRecord на каждое решение
    - OAPOptimizer.update_from_decision() после синтеза
    - ContinuousBacktest sample
    - Self-questioning engine (optional)
    - Periodic sync_with_audit()
    """

    def __init__(
        self,
        sync_interval: int = 10,
        enable_self_question: bool = False,
        enable_backtest: bool = True,
        backtest_horizon: int = 5,
    ):
        self.base_agent = SynthesisAgent()
        self.sync_interval = sync_interval  # Recalibrate every N decisions
        self.enable_self_question = enable_self_question
        self.enable_backtest = enable_backtest

        # Sub-systems
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
        # ATOM-KARL-015 Phase 3: EMA reward state
        self.reward_state = RewardState()
        # ATOM-KARL-015 Phase 5: Lag Windowing
        self.lag_window = get_lag_window()
        self.lag_enabled = True  # enabled by default; set to False to disable

    async def run(self, state: dict) -> dict[str, Any]:
        """
        Run synthesis + AMRE post-processing.

        Returns dict with:
          - synthesis_result: AgentResponse.to_dict()
          - amre_output: AMREOutput dataclass
          - decision_record: DecisionRecord.to_dict()
          - karl_diagnostics: get_karl_diagnostics()
        """
        # ── Step 1: Pre-AMRE checks ────────────────────────────────────────────
        symbol = state.get("symbol", "BTCUSDT")

        # Delisted ticker fallback
        delist_fb = check_delisted_fallback(symbol)
        if delist_fb:
            state = {**state, "symbol": delist_fb.fallback_symbol}

        # Build market state for audit
        price = state.get("current_price", 50000)
        regime = state.get("regime", "NORMAL")
        ms = MarketState(
            symbol=symbol,
            price=price,
            timeframe=state.get("timeframe_requested", "SWING"),
            n_signals=len(state.get("all_signals", [])),
            session_id=state.get("session_id", str(uuid.uuid4())[:8]),
            timestamp=datetime.now(timezone.utc).isoformat(),
            regime=regime,
        )
        market_state_hash(ms)

        # ── Step 2: Run base synthesis ─────────────────────────────────────────
        synthesis_result = await self.base_agent.run(state)

        # Convert to dict for consistent handling
        if isinstance(synthesis_result, AgentResponse):
            synth_dict = synthesis_result.to_dict()
        else:
            synth_dict = synthesis_result

        signal = synth_dict.get("signal", "NEUTRAL")
        confidence = synth_dict.get("confidence", 50)
        all_signals = state.get("all_signals", [])

        # ── Step 3: Self-questioning — Triple Trigger gate (Phase 4) ──────────
        # SelfQ запускается ТОЛЬКО при одном из трёх условий:
        #   1. Strong Disagreement: >35% LONG и >35% SHORT
        #   2. Extreme Regime: HIGH или EXTREME
        #   3. Overconfidence: confidence > 85%
        sq_result = None
        sq_reason = "not_enabled"
        if self.self_questioner:
            need_sq, sq_reason = should_trigger_self_questioning(
                signals=all_signals,
                regime=regime,
                final_confidence=confidence / 100.0,  # normalize to 0..1
            )
            if need_sq:
                # Логируем причину (можно заменить на logger.debug)
                log.info(f"[SelfQ Trigger] {sq_reason} — running self-questioning")
                sq_result = self.self_questioner.ask(all_signals, state)
                if sq_result.confidence_adjustment != 0:
                    confidence = max(
                        30, min(92, confidence + sq_result.confidence_adjustment)
                    )
                    synth_dict["reasoning"] = (
                        f"[SelfQ] {sq_result.question} → {sq_result.answer}. {synth_dict.get('reasoning', '')}"
                    )
            else:
                # Логируем пропуск не чаще чем раз в 5 вызовов
                if self.decision_counter % 5 == 0:
                    log.info(f"[SelfQ Skip] reason={sq_reason}")

        # ── Step 4: Uncertainty + Grounding ──────────────────────────────────
        uncertainty = estimate_uncertainty(all_signals)

        # ── Step 4.5: Phase 5 — Grounding Soft Degrade ───────────────────────
        # Apply grounding BEFORE lag windowing so EMA gets a clean base signal.
        # New grounding returns a delta (negative = degrade) and grounding_factor.
        grounding = validate_with_grounding(
            state, all_signals, current_confidence=confidence
        )

        grounding_factor = grounding.get("grounding_factor", 1.0)
        if grounding_factor < 1.0:
            # Multiplicative soft degrade: max(30, round(confidence * factor))
            degraded = max(30, round(confidence * grounding_factor))
            confidence = degraded
            log.info(
                f"[Grounding] factor={grounding_factor:.3f} → conf {confidence} (degraded)"
            )

        # ── Step 4.6: Phase 5 — Lag Windowing smoothing ───────────────────────
        position_pct = synth_dict.get("metadata", {}).get("position_size", 0.02)

        confidence, position_pct, lag_meta = self._apply_lag_smoothing(
            confidence, position_pct
        )

        # Risk control via position_lag (only when window is mature)
        risk_adjusted = False
        if lag_meta.get("window_mature", False):
            new_pos = apply_position_lag_risk(
                position_pct, lag_meta.get("position_lag", 0.0)
            )
            if new_pos != position_pct:
                position_pct = new_pos
                risk_adjusted = True
                log.info(
                    f"[RiskControl] position adjusted: lag={lag_meta.get('position_lag', 0.0):+.3f} → {position_pct:.4f}"
                )

        # Store lag metrics in synth_dict for observability
        synth_dict["lag_metrics"] = lag_meta
        if risk_adjusted:
            synth_dict["metadata"] = {
                **(synth_dict.get("metadata", {})),
                "position_risk_adjusted": True,
            }

        # ── Step 5: Reward estimation ─────────────────────────────────────────
        reward = self._estimate_reward(state, all_signals, confidence, signal)

        # ── Step 6: Build state hash for record ──────────────────────────────
        state_hash = self._compute_state_hash(state, signal, confidence, regime)

        # ── Step 7: Build DecisionRecord ─────────────────────────────────────
        # Ensemble for record (s can be AgentResponse or dict)
        def _sig_get(s, key, default=None):
            if hasattr(s, key):
                return getattr(s, key)
            if isinstance(s, dict):
                return s.get(key, default)
            return default

        # Collect ensemble info from signals
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

        # Trajectories (simplified — just current decision)
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

        # KPI snapshot from OAP
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
            confidence_adjustments.append(
                f"grounding:{grounding['confidence_adjustment']}"
            )
        # Use cached sq_result from Step 3 — NEVER call ask() again here (would double-invoke and drain question bank)
        if sq_result is not None and sq_result.confidence_adjustment != 0:
            confidence_adjustments.append(f"self_q:{sq_result.confidence_adjustment}")

        # ATOM-META-RL-005: risk_adjusted_pnl from Meta-RL backtest (0.0 in live path)
        # Meta-RL will override this when calling with backtest results
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
            },
            risk_adjusted_pnl=0.0,  # ATOM-META-RL-005: set by Meta-RL backtest path
        )
        if record.risk_adjusted_pnl != 0.0:
            logger.debug(
                f"[META-RL-KARL-BIDIR] DecisionRecord {record.decision_id}: risk_adj_pnl={record.risk_adjusted_pnl:+.4f}"
            )

        # ── Step 8: Record to audit log ──────────────────────────────────────
        audit_log = get_audit_log()
        audit_log.record(record)

        # ATOM-019: Save to PostgreSQL if available
        if PG_AVAILABLE and DecisionRecordRepository:
            try:
                DecisionRecordRepository.save(record.to_dict())
                # Save individual agent signals
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
                log.info(f"[KARL] PostgreSQL save failed: {e}")

        # ── Step 8: Update OAP optimizer ─────────────────────────────────────────
        self.oap.sync_with_audit()

        # ── Step 10: Update calibrator + drawdown tracker ─────────────────────
        self.calibrator.add_sample(confidence, reward)
        self.dd_tracker.add_trade(reward)

        # ── Step 11: Backtest sample (if enabled) ──────────────────────────────
        if self.backtest and self.enable_backtest:
            try:
                self.backtest.add_sample(
                    state=ms,
                    decision=record,
                    reward=reward,
                    signals=all_signals,
                )
            except Exception:
                pass  # Non-fatal

        # ── Step 12: Periodic recalibration ───────────────────────────────────
        self.decision_counter += 1
        if self.decision_counter % self.sync_interval == 0:
            self._sync_and_recalibrate()

        # ── Step 13: Return enriched result ───────────────────────────────────
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

    def _estimate_reward(
        self, state: dict, signals: list, confidence: int, signal: str
    ) -> float:
        """
        Phase 3: EMA-smoothed reward with astro enrichment.
        - 70% market reward + 30% astro reward
        - EMA smoothing (α=0.3) for temporal stability
        - Falls back gracefully if astro data unavailable
        """
        # Build MarketState
        ms = MarketState(
            symbol=state.get("symbol", "BTC"),
            price=state.get("current_price", 50000),
            timeframe=state.get("timeframe_requested", "SWING"),
            n_signals=len(signals),
            session_id=state.get("session_id", ""),
            timestamp=datetime.now(timezone.utc).isoformat(),
            regime=state.get("regime", "NORMAL"),
            confidence=confidence,
        )

        # Base market reward (existing trajectory-based reward)
        market_reward = compute_trajectory_reward(ms, signals)

        # Astro enrichment (ATOM-021)
        try:
            from agents._impl.amre.astro_reward import compute_astro_reward

            moon_long = state.get("moon_longitude", 0.0)
            aspects = state.get("planetary_aspects", [])
            nak_long = state.get("nakshatra_longitude", 0.0)
            astro_dict = compute_astro_reward(
                state=ms,
                moon_longitude=moon_long,
                aspects=aspects,
                nakshatra_longitude=nak_long,
                base_reward=market_reward,
            )
            astro_reward = astro_dict.get("final_reward", 0.0)
        except Exception:
            astro_reward = 0.0  # Fallback: no astro data

        # Combined raw reward: 70% market + 30% astro
        raw_reward = 0.7 * market_reward + 0.3 * astro_reward

        # EMA smoothing — α=0.3 balances responsiveness with noise reduction
        previous_ema = self.reward_state.ema_reward
        smoothed = update_reward_ema(previous_ema, raw_reward)
        self.reward_state.ema_reward = smoothed
        self.reward_state.raw_reward = raw_reward
        self.reward_state.count += 1

        # Log for observability
        if self.reward_state.count % 10 == 0:
            log.info(
                f"[REWARD EMA] count={self.reward_state.count} market={market_reward:.3f} astro={astro_reward:.3f} raw={raw_reward:.3f} ema={smoothed:.3f}"
            )

        return smoothed

    def _compute_state_hash(
        self, state: dict, signal: str, confidence: int, regime: str
    ) -> str:
        """Compute reproducible state hash."""
        data = f"{state.get('symbol', '')}:{state.get('current_price', 0)}:{state.get('timeframe_requested', 'SWING')}:{len(state.get('all_signals', []))}:{regime}:{signal}:{confidence}"
        return hashlib.sha256(data.encode()).hexdigest()[
            :12
        ]  # nosec B324 — content hash for synthesis key, not security

    # ── Phase 5: Lag Windowing ─────────────────────────────────────────────────

    def _apply_lag_smoothing(
        self, confidence: int, position_pct: float
    ) -> tuple[int, float, dict]:
        """
        Apply LagWindow smoothing to confidence and compute position_lag metrics.

        Parameters
        ----------
        confidence : int
            Current raw confidence (0–100).
        position_pct : float
            Current position size (0.0–1.0+).

        Returns
        -------
        tuple
            (adjusted_confidence, adjusted_position_pct, lag_metrics_dict)

        Notes
        -----
        - Returns unchanged values when ``self.lag_enabled`` is False.
        - Maturity threshold: ``count >= WARMUP_THRESHOLD`` (20 decisions).
        - position_pct is NOT yet risk-adjusted here; risk control is applied
          separately after this call in ``run()``.
        """
        if not self.lag_enabled:
            return confidence, position_pct, {}

        # LagWindow.add() returns a dict with keys:
        # final_confidence, raw_confidence, ema, lag_adj,
        # position_lag, window_size, alpha, blend, count
        metrics = self.lag_window.add(
            confidence=confidence,
            position_pct=position_pct,
        )

        adjusted_conf = metrics["final_confidence"]
        window_mature = metrics["count"] >= 20  # WARMUP_THRESHOLD == 20

        lag_meta = {
            "raw_confidence": metrics["raw_confidence"],
            "ema_confidence": metrics["ema"],
            "lag_adjustment": metrics["lag_adj"],
            "position_lag": metrics["position_lag"],
            "window_mature": window_mature,
            "window_size": metrics["window_size"],
            "blend": metrics["blend"],
        }

        # Log when lag adjustment is non-zero
        if metrics["lag_adj"] != 0:
            log.info(
                f"[LagWindow] conf {confidence} → {adjusted_conf} (adj={metrics['lag_adj']:+.3f}, pos_lag={metrics['position_lag']:+.3f})"
            )

        return adjusted_conf, position_pct, lag_meta

    def _sync_and_recalibrate(self):
        """Periodic self-assessment — calls sync_with_audit to update KPIs."""
        self.oap.sync_with_audit()

    def sync_with_audit(self) -> dict[str, Any]:
        """
        Manual trigger: sync_with_audit().
        Periodic self-assessment — analyze drift, adjust KPIs.
        """
        audit_log = get_audit_log()
        drift = audit_log.analyze_drift()
        karl_diag = get_karl_diagnostics()

        # Force recalibration if drifting
        if drift.get("status") == "degrading":
            self._sync_and_recalibrate()

        return {
            "drift_analysis": drift,
            "karl_diagnostics": karl_diag,
            "calibrator_diagnostics": get_reward_diagnostics(),
            "decision_count": self.decision_counter,
        }

    def run_backtest_on_historical(
        self, bars: list, symbol: str = "BTCUSDT"
    ) -> dict[str, Any]:
        """
        Run continuous backtest on historical bars.
        Returns backtest results.
        """
        if not self.backtest:
            return {"error": "backtest not enabled"}

        results = run_backtest_on_bars(
            agent_run_fn=lambda state: self.run(state),
            bars=bars,
            symbol=symbol,
        )
        return results

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


# ── Sprint 6: conflict resolution stub ─────────────────────────────────────

def resolve_conflict(agent_a, agent_b):
    """Resolve conflict between two agents by reducing both weights by 10%."""
    agent_a.metadata["weight"] = max(0.0, agent_a.metadata.get("weight", 0.10) - 0.10)
    agent_b.metadata["weight"] = max(0.0, agent_b.metadata.get("weight", 0.10) - 0.10)
