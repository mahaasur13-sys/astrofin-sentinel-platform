"""
MacroAgent — macroeconomic & geopolitical risk analysis.

Indicators:
- VIX (fear index): >25 → bearish bias
- DXY (dollar index): directional signal
- Geopolitical risk: via RAG retrieval
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from agents._impl.ephemeris_decorator import EphemerisUnavailableError, require_ephemeris
from agents.metrics import track_agent_metrics
from core.base_agent import EPHEMERIS_UNAVAILABLE, UNKNOWN, AgentResponse, BaseAgent, SignalDirection
from knowledge.rag_retriever import RAGRetriever

logger = logging.getLogger(__name__)

# Пороговые значения
VIX_FEAR_THRESHOLD = 25.0  # VIX выше этого → страх, медвежий сигнал
VIX_COMPLACENCY_THRESHOLD = 15.0  # VIX ниже этого → самоуспокоенность, бычий
DXY_STRONG_THRESHOLD = 105.0  # сильный доллар → давление на рисковые активы
DXY_WEAK_THRESHOLD = 95.0  # слабый доллар → поддержка рисковых активов


class MacroAgent(BaseAgent[AgentResponse]):
    """
    MacroAgent — фундаментальный макроэкономический анализ.

    Responsibilities:
    1. VIX analysis (fear index)
    2. DXY (dollar index) directional signal
    3. Geopolitical risk scoring via RAG
    4. Weighted macro signal aggregation

    Weight: 15% (part of 20% Fundamental+Macro block)
    """

    def __init__(self):
        super().__init__(name="MacroAgent", domain="macro", weight=0.15)
        self.rag: Optional[RAGRetriever] = None

    async def _get_rag(self) -> RAGRetriever:
        """Lazy init RAG retriever."""
        if self.rag is None:
            try:
                self.rag = RAGRetriever()  # index_name removed in P2-02 RAGClient (G12)
            except Exception as e:
                logger.warning("Failed to init RAG for MacroAgent: %s", e)
        return self.rag

    @track_agent_metrics
    async def run(self, state: dict) -> AgentResponse:
        """Public entry point. Delegates to analyze() with defensive error handling."""
        try:
            return await self.analyze(state)
        except EphemerisUnavailableError as e:
            return self._degraded(EPHEMERIS_UNAVAILABLE, str(e))
        except Exception as e:  # noqa: BLE001 — last-resort guard
            logger.exception("macro_agent_run_unhandled", extra={"agent": self.name})
            return self._degraded(UNKNOWN, repr(e))

    @require_ephemeris
    async def analyze(self, state: dict) -> AgentResponse:
        """
        Main analysis method.

        Args:
            state: Market state dict with optional keys:
                - vix: float (VIX index value)
                - dxy: float (DXY index value)
                - news_headlines: list[str] (optional news for geopolitical context)

        Returns:
            AgentResponse with signal and confidence.
        """
        reasons = []
        scores = []

        # 1. VIX analysis
        vix = state.get("vix")
        if vix is not None:
            vix_signal, vix_conf, vix_reason = self._analyze_vix(vix)
            scores.append((vix_signal, vix_conf))
            reasons.append(vix_reason)

        # 2. DXY analysis
        dxy = state.get("dxy")
        if dxy is not None:
            dxy_signal, dxy_conf, dxy_reason = self._analyze_dxy(dxy)
            scores.append((dxy_signal, dxy_conf))
            reasons.append(dxy_reason)

        # 3. Geopolitical risk via RAG
        geo_signal, geo_conf, geo_reason = await self._analyze_geopolitical(state)
        if geo_signal is not None:
            scores.append((geo_signal, geo_conf))
            reasons.append(geo_reason)

        # 4. Aggregate signals
        if not scores:
            # No data available
            return AgentResponse(
                agent_name="MacroAgent",
                signal=SignalDirection.NEUTRAL,
                confidence=30,
                reasoning="No macro data available (VIX, DXY, or geopolitical context missing)",
            )

        signal, confidence = self._weighted_aggregate(scores)

        # Формируем итоговое объяснение
        reasoning = " | ".join(reasons)
        reasoning = f"[Macro] {reasoning} → {signal.name} ({confidence:.0f}%)"

        return AgentResponse(
            agent_name="MacroAgent",
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
        )

    def _analyze_vix(self, vix: float) -> tuple[SignalDirection, float, str]:
        """Analyze VIX fear index."""
        if vix > VIX_FEAR_THRESHOLD:
            return (
                SignalDirection.SHORT,
                min(90.0, 50 + (vix - VIX_FEAR_THRESHOLD) * 2),
                f"VIX={vix:.1f} (fear > {VIX_FEAR_THRESHOLD})",
            )
        elif vix < VIX_COMPLACENCY_THRESHOLD:
            return (
                SignalDirection.LONG,
                min(80.0, 50 + (VIX_COMPLACENCY_THRESHOLD - vix) * 3),
                f"VIX={vix:.1f} (complacency < {VIX_COMPLACENCY_THRESHOLD})",
            )
        else:
            return (
                SignalDirection.NEUTRAL,
                40.0,
                f"VIX={vix:.1f} (normal range)",
            )

    def _analyze_dxy(self, dxy: float) -> tuple[SignalDirection, float, str]:
        """Analyze DXY (dollar index). Strong dollar → pressure on risk assets."""
        if dxy > DXY_STRONG_THRESHOLD:
            return (
                SignalDirection.SHORT,
                min(75.0, 50 + (dxy - DXY_STRONG_THRESHOLD) * 1.5),
                f"DXY={dxy:.1f} (strong USD > {DXY_STRONG_THRESHOLD})",
            )
        elif dxy < DXY_WEAK_THRESHOLD:
            return (
                SignalDirection.LONG,
                min(75.0, 50 + (DXY_WEAK_THRESHOLD - dxy) * 1.5),
                f"DXY={dxy:.1f} (weak USD < {DXY_WEAK_THRESHOLD})",
            )
        else:
            return (
                SignalDirection.NEUTRAL,
                40.0,
                f"DXY={dxy:.1f} (normal range)",
            )

    async def _analyze_geopolitical(self, state: dict) -> tuple[Optional[SignalDirection], float, str]:
        """
        Analyze geopolitical risk via RAG.

        Searches for recent geopolitical events and scores their impact.
        Falls back gracefully if RAG is unavailable.
        """
        headlines = state.get("news_headlines", [])
        query = "geopolitical risk financial markets impact"
        if headlines:
            query = " ".join(headlines[:3]) + " " + query

        try:
            rag = await self._get_rag()
            if rag is None:
                return None, 0, "RAG unavailable for geopolitical analysis"

            results = await rag.search(query, top_k=3)
            if not results:
                return None, 0, "No geopolitical signals found in knowledge base"

            # Простейший анализ: считаем негативные ключевые слова
            negative_keywords = [
                "war",
                "conflict",
                "sanction",
                "crisis",
                "tension",
                "attack",
                "invasion",
                "embargo",
                "turmoil",
                "instability",
            ]
            positive_keywords = [
                "peace",
                "ceasefire",
                "agreement",
                "stability",
                "cooperation",
                "trade deal",
                "resolution",
                "summit",
            ]

            neg_count = 0
            pos_count = 0
            for doc in results:
                text = doc.page_content.lower() if hasattr(doc, "page_content") else str(doc).lower()
                neg_count += sum(text.count(kw) for kw in negative_keywords)
                pos_count += sum(text.count(kw) for kw in positive_keywords)

            if neg_count > pos_count:
                return (
                    SignalDirection.SHORT,
                    min(80.0, 50 + (neg_count - pos_count) * 10),
                    f"Geo risk: {neg_count} negative vs {pos_count} positive signals",
                )
            elif pos_count > neg_count:
                return (
                    SignalDirection.LONG,
                    min(70.0, 50 + (pos_count - neg_count) * 10),
                    f"Geo risk: {pos_count} positive vs {neg_count} negative signals",
                )
            else:
                return None, 0, "Geopolitical signals balanced"

        except Exception as e:
            logger.warning("Geopolitical analysis failed: %s", e)
            return None, 0, f"Geopolitical analysis error: {str(e)}"

    def _weighted_aggregate(self, scores: list[tuple[SignalDirection, float]]) -> tuple[SignalDirection, float]:
        """
        Aggregate multiple macro signals into a single direction.

        Weights: VIX=0.4, DXY=0.3, Geopolitical=0.3
        """
        weights = [0.4, 0.3, 0.3][: len(scores)]
        # Normalize weights
        total_w = sum(weights)
        if total_w == 0:
            return SignalDirection.NEUTRAL, 0.0

        weights = [w / total_w for w in weights]

        # Weighted score: -1 (bearish) to +1 (bullish)
        direction_map = {
            SignalDirection.LONG: 1.0,
            SignalDirection.SHORT: -1.0,
            SignalDirection.NEUTRAL: 0.0,
        }

        weighted_score = 0.0
        total_confidence = 0.0
        for (sig, conf), w in zip(scores, weights):
            weighted_score += direction_map[sig] * w
            total_confidence += conf * w

        if weighted_score > 0.2:
            return SignalDirection.LONG, min(90.0, total_confidence)
        elif weighted_score < -0.2:
            return SignalDirection.SHORT, min(90.0, total_confidence)
        else:
            return SignalDirection.NEUTRAL, total_confidence * 0.5


async def run_macro_agent(state: dict) -> dict:
    """Convenience function for orchestration."""
    agent = MacroAgent()
    resp = await agent.analyze(state)
    return {"macro_agent_signal": resp.to_dict()}
