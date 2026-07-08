"""core/council/runner.py — AstroCouncil Runner"""

from __future__ import annotations

import logging
from datetime import datetime

from core.council.agents import AGENT_FACTORIES
from core.council.council import AstroCouncil
from core.council.types import CouncilResult

logger = logging.getLogger(__name__)


def run_council(
    symbol: str,
    price: float = 100.0,
    fair_value: float = 110.0,
    catalyst: str = "",
    predicted_return: float = 0.02,
    uncertainty: float = 0.05,
    vix: float = 18.0,
    dxy: float = 104.0,
    geopolitical: float = 0.1,
    rsi: float = 45.0,
    macd_bullish: bool = True,
    trend: str = "up",
    fear_greed: float = 65.0,
    news_score: float = 0.1,
    ul_trailing: float = 500000.0,
    gamma_exp: float = 0.0,
    unusual: bool = False,
    moon_long: float = 120.0,
    jupiter_long: float = 200.0,
    saturn_long: float = 300.0,
    nakshatra: int = 14,
    choghadiya: str = "Shubh",
    retrograde: list | None = None,
) -> CouncilResult:
    council = AstroCouncil()
    members = [
        AGENT_FACTORIES["fundamental"](price=price, fair_value=fair_value, catalyst=catalyst),
        AGENT_FACTORIES["quant"](predicted_return=predicted_return, uncertainty=uncertainty),
        AGENT_FACTORIES["macro"](vix=vix, dxy=dxy, geopolitical=geopolitical),
        AGENT_FACTORIES["technical"](rsi=rsi, macd_bullish=macd_bullish, price=price),
        AGENT_FACTORIES["sentiment"](vix=vix, fear_greed=fear_greed, news_score=news_score),
        AGENT_FACTORIES["optionsflow"](
            predicted_return=predicted_return,
            ul_trailing=ul_trailing,
            gamma_exp=gamma_exp,
            unusual=unusual,
        ),
        AGENT_FACTORIES["astro"](
            price=price,
            predicted_return=predicted_return,
            moon_long=moon_long,
            jupiter_long=jupiter_long,
            saturn_long=saturn_long,
            nakshatra=nakshatra,
            choghadiya=choghadiya,
            retrograde=retrograde or [],
        ),
    ]
    for m in members:
        council.add_member(m)
    deliberation = f"Council voting on {symbol} at {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}: "
    result = council.vote(symbol, deliberation)
    result.deliberation += "; " + council.summary(result)
    return result


if __name__ == "__main__":
    result = run_council("BTCUSDT")
    logger.info(result.deliberation)
    logger.info(
        "SUMMARY: %s confidence=%.3f consensus=%.3f", result.final_signal.value, result.confidence, result.consensus
    )
