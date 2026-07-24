"""
AstroFin Sentinel v5 — Router Agent
Routes user queries to appropriate specialist flows.
"""

from __future__ import annotations
from enum import Enum

from pydantic import BaseModel, Field


class QueryType(Enum):
    """Типы запросов, которые роутер должен распознавать."""

    TECHNICAL_ONLY = "technical_only"  # Только тех.анализ
    ASTRO_ONLY = "astro_only"  # Только астрология
    ELECTIONAL_ONLY = "electional_only"  # Только электоральная
    FULL_ANALYSIS = "full_analysis"  # Полный анализ (все потоки)
    SINGLE_SYMBOL = "single_symbol"  # Анализ одного символа
    MULTI_SYMBOL = "multi_symbol"  # Сравнение нескольких
    MARKET_SCAN = "market_scan"  # Сканирование рынка
    MUHURTA_QUERY = "muhurta_query"  # Поиск благоприятного момента


class RouterOutput(BaseModel):
    query_type: QueryType
    symbols: list[str] = Field(default_factory=list)
    timeframe: str | None = None
    include_technical: bool = True
    include_astro: bool = True
    include_electional: bool = False
    birth_data: dict | None = None
    confidence_threshold: float = 0.5


def route_query(user_query: str, context: dict | None = None) -> RouterOutput:
    """
    Роутит пользовательский запрос в нужный тип.

    Правила:
    - Если спрашивают "когда лучше начать" / "мухурта" / "элекция" → ELECTIONAL_ONLY
    - Если спрашивают "BTC" без астрологии → TECHNICAL_ONLY
    - Если спрашивают "BTC + астрология" / "прогноз" → FULL_ANALYSIS
    - Если спрашивают "сканировать рынок" / "что купить" → MARKET_SCAN
    """
    query_lower = user_query.lower()
    context = context or {}

    # Определяем тип запроса
    electional_keywords = [
        "когда начать",
        "мухурта",
        "элекция",
        "благоприятн",
        "лучшее время",
        "начать бизнес",
        "запустить",
        "when",
        "election",
        "muhurta",
        "choghadiya",
    ]

    technical_keywords = [
        "анализ",
        "прогноз",
        "технич",
        "rsi",
        "macd",
        "bollinger",
        "волны",
        "эллиотт",
        "gann",
        "signal",
        "buy",
        "sell",
        "short",
        "long",
    ]

    # Symbol extraction (common crypto/ stock patterns)
    symbols = []
    if "btc" in query_lower or "bitcoin" in query_lower:
        symbols.append("BTCUSDT")
    if "eth" in query_lower or "ethereum" in query_lower:
        symbols.append("ETHUSDT")
    if "sol" in query_lower or "solana" in query_lower:
        symbols.append("SOLUSDT")
    if "bnb" in query_lower:
        symbols.append("BNBUSDT")
    if "s&p" in query_lower or "sp500" in query_lower:
        symbols.append("SPY")
    if "nasdaq" in query_lower or "qqq" in query_lower:
        symbols.append("QQQ")

    # Determine query type
    has_electional = any(kw in query_lower for kw in electional_keywords)
    has_technical = any(kw in query_lower for kw in technical_keywords)
    len(symbols) > 1
    is_market_scan = "сканиров" in query_lower or "scan" in query_lower

    # Determine timeframe BEFORE branching to avoid UnboundLocalError
    # (the early return in `elif has_electional:` uses `timeframe`)
    timeframe = "SWING"
    if "интрадей" in query_lower or "intraday" in query_lower:
        timeframe = "INTRADAY"
    elif "позиционн" in query_lower:
        timeframe = "POSITIONAL"
    elif "месяц" in query_lower or "monthly" in query_lower:
        timeframe = "MONTHLY"

    if is_market_scan:
        query_type = QueryType.MARKET_SCAN
        include_technical = True
        include_astro = True
        include_electional = False
    elif has_electional and has_technical:
        query_type = QueryType.FULL_ANALYSIS
        include_technical = True
        include_astro = True
        include_electional = True
    elif has_electional:
        query_type = QueryType.ELECTIONAL_ONLY
        include_technical = False
        include_astro = False
        include_electional = True
        return RouterOutput(
            query_type=query_type,
            symbols=symbols if symbols else ["BTCUSDT"],
            timeframe=timeframe,
            include_technical=include_technical,
            include_astro=include_astro,
            include_electional=include_electional,
            birth_data=context.get("birth_data"),
            confidence_threshold=context.get("confidence_threshold", 0.5),
        )
    elif has_technical or symbols:
        query_type = (
            QueryType.SINGLE_SYMBOL if len(symbols) == 1 else QueryType.MULTI_SYMBOL
        )
        include_technical = True
        include_astro = context.get("include_astro", True)
        include_electional = False
    else:
        query_type = QueryType.FULL_ANALYSIS
        include_technical = True
        include_astro = True
        include_electional = context.get("include_electional", False)

    return RouterOutput(
        query_type=query_type,
        symbols=symbols if symbols else ["BTCUSDT"],
        timeframe=timeframe,
        include_technical=include_technical,
        include_astro=include_astro,
        include_electional=include_electional,
        birth_data=context.get("birth_data"),
        confidence_threshold=context.get("confidence_threshold", 0.5),
    )
