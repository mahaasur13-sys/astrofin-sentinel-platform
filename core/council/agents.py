"""core/council/agents.py — AstroCouncil agents"""
from __future__ import annotations

from .types import AGENT_WEIGHTS, CouncilMember, Signal


def fundamental_agent(price: float, fair_value: float, **kwargs) -> CouncilMember:
    ratio = fair_value / price
    if ratio > 1.01:
        conf = int(50 + (ratio - 1.01) * 3000)
        return CouncilMember(
            name="FundamentalAgent",
            domain="fundamental",
            vote=Signal.LONG,
            confidence=min(conf, 90),
            reasoning=f"FV {ratio:.3f}>1.01",
            weight=AGENT_WEIGHTS["fundamental"],
            aligned=False,
        )
    elif ratio < 0.99:
        conf = int(50 + (0.99 - ratio) * 3000)
        return CouncilMember(
            name="FundamentalAgent",
            domain="fundamental",
            vote=Signal.SHORT,
            confidence=min(conf, 90),
            reasoning=f"FV {ratio:.3f}<0.99",
            weight=AGENT_WEIGHTS["fundamental"],
            aligned=False,
        )
    return CouncilMember(
        name="FundamentalAgent",
        domain="fundamental",
        vote=Signal.NEUTRAL,
        confidence=55,
        reasoning=f"FV ratio={ratio:.3f}",
        weight=AGENT_WEIGHTS["fundamental"],
        aligned=False,
    )


def quant_agent(predicted_return: float, uncertainty: float, **kwargs) -> CouncilMember:
    snr = predicted_return / uncertainty if uncertainty > 0 else 0
    if snr > 0.3:
        return CouncilMember(
            name="QuantAgent",
            domain="quant",
            vote=Signal.LONG,
            confidence=min(int(40 + snr * 200), 95),
            reasoning=f"LONG snr={snr:.2f}",
            weight=AGENT_WEIGHTS["quant"],
            aligned=False,
        )
    elif snr < -0.3:
        return CouncilMember(
            name="QuantAgent",
            domain="quant",
            vote=Signal.SHORT,
            confidence=min(int(40 + abs(snr) * 200), 95),
            reasoning=f"SHORT snr={snr:.2f}",
            weight=AGENT_WEIGHTS["quant"],
            aligned=False,
        )
    return CouncilMember(
        name="QuantAgent",
        domain="quant",
        vote=Signal.NEUTRAL,
        confidence=60,
        reasoning=f"NEUTRAL snr={snr:.2f}",
        weight=AGENT_WEIGHTS["quant"],
        aligned=False,
    )


def macro_agent(vix: float, dxy: float, geopolitical: float = 0.1, **kwargs) -> CouncilMember:
    risk = (vix - 15) / 10 + (dxy - 100) / 20 + geopolitical
    if risk < 0.2:
        return CouncilMember(
            name="MacroAgent",
            domain="macro",
            vote=Signal.LONG,
            confidence=60,
            reasoning=f"low risk={risk:.2f}",
            weight=AGENT_WEIGHTS["macro"],
            aligned=False,
        )
    elif risk > 1.0:
        return CouncilMember(
            name="MacroAgent",
            domain="macro",
            vote=Signal.SHORT,
            confidence=60,
            reasoning=f"high risk={risk:.2f}",
            weight=AGENT_WEIGHTS["macro"],
            aligned=False,
        )
    return CouncilMember(
        name="MacroAgent",
        domain="macro",
        vote=Signal.NEUTRAL,
        confidence=55,
        reasoning=f"mod risk={risk:.2f}",
        weight=AGENT_WEIGHTS["macro"],
        aligned=False,
    )


def technical_agent(rsi: float, macd_bullish: bool, price: float, **kwargs) -> CouncilMember:
    score = 0
    if rsi < 35:
        score += 2
    elif rsi < 45:
        score += 1
    elif rsi > 65:
        score -= 2
    elif rsi > 55:
        score -= 1
    score += 1 if macd_bullish else -1
    if score >= 2:
        return CouncilMember(
            name="TechnicalAgent",
            domain="technical",
            vote=Signal.LONG,
            confidence=70,
            reasoning=f"bullish score={score}",
            weight=AGENT_WEIGHTS["technical"],
            aligned=False,
        )
    elif score <= -2:
        return CouncilMember(
            name="TechnicalAgent",
            domain="technical",
            vote=Signal.SHORT,
            confidence=70,
            reasoning=f"bearish score={score}",
            weight=AGENT_WEIGHTS["technical"],
            aligned=False,
        )
    return CouncilMember(
        name="TechnicalAgent",
        domain="technical",
        vote=Signal.NEUTRAL,
        confidence=55,
        reasoning=f"neutral score={score}",
        weight=AGENT_WEIGHTS["technical"],
        aligned=False,
    )


def sentiment_agent(vix: float = 18.0, **kwargs) -> CouncilMember:
    if vix < 15:
        return CouncilMember(
            name="SentimentAgent",
            domain="sentiment",
            vote=Signal.LONG,
            confidence=65,
            reasoning=f"low VIX={vix:.1f}",
            weight=AGENT_WEIGHTS["sentiment"],
            aligned=False,
        )
    elif vix > 25:
        return CouncilMember(
            name="SentimentAgent",
            domain="sentiment",
            vote=Signal.SHORT,
            confidence=65,
            reasoning=f"high VIX={vix:.1f}",
            weight=AGENT_WEIGHTS["sentiment"],
            aligned=False,
        )
    return CouncilMember(
        name="SentimentAgent",
        domain="sentiment",
        vote=Signal.NEUTRAL,
        confidence=55,
        reasoning=f"VIX={vix:.1f}",
        weight=AGENT_WEIGHTS["sentiment"],
        aligned=False,
    )


def optionsflow_agent(predicted_return: float = 0.0, **kwargs) -> CouncilMember:
    if predicted_return > 0.01:
        return CouncilMember(
            name="OptionsFlowAgent",
            domain="optionsflow",
            vote=Signal.LONG,
            confidence=65,
            reasoning="positive flow",
            weight=AGENT_WEIGHTS["optionsflow"],
            aligned=False,
        )
    elif predicted_return < -0.01:
        return CouncilMember(
            name="OptionsFlowAgent",
            domain="optionsflow",
            vote=Signal.SHORT,
            confidence=65,
            reasoning="negative flow",
            weight=AGENT_WEIGHTS["optionsflow"],
            aligned=False,
        )
    return CouncilMember(
        name="OptionsFlowAgent",
        domain="optionsflow",
        vote=Signal.NEUTRAL,
        confidence=55,
        reasoning="neutral flow",
        weight=AGENT_WEIGHTS["optionsflow"],
        aligned=False,
    )


def astro_agent(price: float, predicted_return: float, **kwargs) -> CouncilMember:
    if predicted_return > 0.01:
        return CouncilMember(
            name="AstroAgent",
            domain="astro",
            vote=Signal.LONG,
            confidence=60,
            reasoning="bullish astro",
            weight=AGENT_WEIGHTS["astro"],
            aligned=True,
        )
    elif predicted_return < -0.01:
        return CouncilMember(
            name="AstroAgent",
            domain="astro",
            vote=Signal.SHORT,
            confidence=60,
            reasoning="bearish astro",
            weight=AGENT_WEIGHTS["astro"],
            aligned=True,
        )
    return CouncilMember(
        name="AstroAgent",
        domain="astro",
        vote=Signal.NEUTRAL,
        confidence=55,
        reasoning="neutral astro",
        weight=AGENT_WEIGHTS["astro"],
        aligned=True,
    )


AGENT_FACTORIES = {
    "fundamental": fundamental_agent,
    "quant": quant_agent,
    "macro": macro_agent,
    "technical": technical_agent,
    "sentiment": sentiment_agent,
    "optionsflow": optionsflow_agent,
    "astro": astro_agent,
}
