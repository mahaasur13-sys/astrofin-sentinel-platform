"""Production Strategy — XAUUSD 4H Improved + Multi-TF WFA Gate."""

import logging

from trading_engine.signals.xauusd_4h_improved import XAUUSD4HSignal

logger = logging.getLogger("trading_engine.signals.production_strategy")


class ProductionStrategy:
    """Hybrid production strategy: 70% XAUUSD 4H + 30% WFA Gate."""

    def __init__(self, xau_weight: float = 0.70, wfa_weight: float = 0.30):
        self.xau_weight = xau_weight
        self.wfa_weight = wfa_weight
        self._xau = XAUUSD4HSignal(entry_threshold=0.08)

    def compute(self) -> dict:
        """Generate trading signal from the hybrid strategy.

        Only the XAUUSD leg is live; the WFA gate is still a placeholder, so the
        weights are reported instead of applied. On any failure the signal is
        flagged ``price_source="unavailable"`` so callers can refuse to persist it.
        """
        try:
            xau = self._xau.generate()
        except Exception as exc:
            logger.error("ProductionStrategy: XAU leg unavailable: %s", exc)
            return {
                "direction": "UNAVAILABLE",
                "confidence": None,
                "price": None,
                "regime": None,
                "price_source": "unavailable",
                "error": str(exc),
                "timestamp": None,
            }

        signal = {
            "direction": xau.signal,
            "confidence": round(xau.confidence * 100.0, 1),
            "price": xau.price,
            "regime": xau.regime.upper(),
            "net_score": xau.net_score,
            "atr_pct": round(xau.atr_pct, 3),
            "trend": xau.trend,
            "agent_signals": xau.agent_signals,
            "price_source": "xauusd_4h_improved",
            "wfa_placeholder": True,
            "timestamp": None,
        }
        logger.info(
            "ProductionStrategy.compute() → %s (conf=%.1f, regime=%s, net=%+.3f)",
            signal["direction"], signal["confidence"], signal["regime"], signal["net_score"],
        )
        return signal
