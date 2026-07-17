"""HMMRegimeAgent — Hidden Markov Model for market regime detection and anomaly scoring."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from agents.metrics import track_agent_metrics
from core.base_agent import UNKNOWN, AgentResponse, BaseAgent, SignalDirection

logger = logging.getLogger(__name__)

try:
    from hmmlearn import hmm

    HAS_HMM = True
except ImportError:
    HAS_HMM = False
    logger.warning("hmmlearn not installed. HMMRegimeAgent will run in degraded mode.")


class HMMRegimeAgent(BaseAgent[AgentResponse]):
    """
    Определяет рыночный режим (тренд/флэт/волатильность) через HMM.
    Выступает как perception-слой для KARL и Risk Engine.

    Domain: quant
    Weight: 0.10
    """

    def __init__(self):
        super().__init__(
            name="HMMRegimeAgent",
            instructions_path="agents/HMMRegimeAgent_instructions.md",
            domain="quant",
            weight=0.10,
        )
        self._model: Any = None
        self._n_states = 3  # bull, bear, sideways
        self._lookback = 120
        self._anomaly_threshold = -15.0  # log-likelihood below which = anomaly  # Log-likelihood below which market is anomalous

    def _init_model(self):
        if not HAS_HMM:
            return None
        if self._model is None:
            self._model = hmm.GaussianHMM(
                n_components=self._n_states,
                covariance_type="diag",
                n_iter=200, tol=1e-3, random_state=42, init_params="stmc",
            )
        return self._model

    def _extract_features(self, ohlcv: list) -> np.ndarray:
        """Извлечение признаков: returns, volatility, volume ratio."""
        if len(ohlcv) < self._lookback:
            return np.array([])
        closes = np.array([c["close"] for c in ohlcv[-self._lookback:]])
        volumes = np.array([c["volume"] for c in ohlcv[-self._lookback:]])
        returns = np.diff(np.log(closes))
        volatility = np.std(returns) * np.sqrt(252)
        volume_ratio = volumes[-1] / (np.mean(volumes) + 1e-8)
        features = np.column_stack([
            returns,
            np.full_like(returns, volatility),
            np.full_like(returns, volume_ratio),
        ])
        return features

    def _predict_regime(self, features: np.ndarray) -> tuple[int, np.ndarray, float, bool]:
        """Возвращает (режим, вероятности, log_likelihood, is_anomaly)."""
        model = self._init_model()
        if model is None or len(features) == 0:
            return 1, np.array([0.33, 0.34, 0.33]), 0.0, False
        try:
            model.fit(features)
            state = model.predict(features)[-1]
            probs = model.predict_proba(features)[-1]
            log_likelihood = float(model.score(features))
            is_anomaly = log_likelihood < self._anomaly_threshold
            return int(state), probs, log_likelihood, is_anomaly
        except Exception as e:
            logger.error(f"HMM prediction failed: {e}")
            return 1, np.array([0.33, 0.34, 0.33]), 0.0, False

    async def analyze(self, state: dict) -> AgentResponse:
        symbol = state.get("symbol", "BTCUSDT")
        ohlcv = state.get("ohlcv", [])

        if not ohlcv or len(ohlcv) < self._lookback:
            return AgentResponse(
                agent_name=self.name,
                signal=SignalDirection.NEUTRAL,
                confidence=50,
                reasoning="Insufficient data for HMM regime detection.",
                sources=[],
                metadata={"data_quality": 0.0, "n_samples": len(ohlcv)},
            )

        features = self._extract_features(ohlcv)
        regime, probs, log_likelihood, is_anomaly = self._predict_regime(features)

        regime_map = {0: SignalDirection.LONG, 1: SignalDirection.NEUTRAL, 2: SignalDirection.SHORT}
        base_signal = regime_map.get(regime, SignalDirection.NEUTRAL)

        if is_anomaly:
            signal = SignalDirection.AVOID
            confidence = 90
            reasoning = (
                f"HMM anomaly detected (log_likelihood={log_likelihood:.2f} < {self._anomaly_threshold}). "
                "Market behaviour deviates from learned model — AVOID trading."
            )
        else:
            signal = base_signal
            confidence = int(max(probs) * 100) if len(probs) > 0 else 50
            reasoning = (
                f"HMM regime: state={regime} (probs={[round(p, 2) for p in probs.tolist()]}), "
                f"log_likelihood={log_likelihood:.2f}"
            )

        return AgentResponse(
            agent_name=self.name,
            signal=signal,
            confidence=min(confidence, 100),
            reasoning=reasoning,
            sources=[],
            metadata={
                "regime": regime,
                "regime_probabilities": probs.tolist() if len(probs) > 0 else [],
                "log_likelihood": log_likelihood,
                "is_anomaly": is_anomaly,
                "data_quality": 1.0,
                "n_samples": len(ohlcv),
            },
        )

    @track_agent_metrics
    async def run(self, state: dict) -> AgentResponse:
        """
        Точка входа агента. Выполняет анализ рыночного режима через HMM,
        оборачивает логику в трекинг метрик и обрабатывает исключения.

        Args:
            state: Текущее состояние среды платформы, содержит 'symbol' и 'ohlcv'.

        Returns:
            AgentResponse: Сигнал (LONG/SHORT/NEUTRAL/AVOID) с метаданными режима.
        """
        try:
            return await self.analyze(state)
        except Exception as e:
            logger.exception("hmm_regime_agent_unhandled")
            return self._degraded(UNKNOWN, repr(e))


async def run_hmm_regime_agent(state: dict) -> AgentResponse:
    """Convenience runner used by agents/gitagent_registry.py."""
    return await HMMRegimeAgent().run(state)


__all__ = ["HMMRegimeAgent", "run_hmm_regime_agent"]
