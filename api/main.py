"""
AstroFin Sentinel API — FastAPI backend for React frontend.

Endpoints:
    GET  /api/v1/dashboard        — full dashboard state (agents, regime, ensemble)
    GET  /api/v1/astro/aspects    — current astrological aspects from ephemeris
    POST /api/v1/agent/run        — run an agent with LLM routing
    GET  /health                  — health check
import re
"""

from datetime import datetime, timezone
import re
import logging
import inspect, asyncio
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from core.auth import require_api_key
from core.base_agent import BaseAgent

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="AstroFin Sentinel API", version="0.5.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Prometheus metrics endpoint (scraped by astrofin-prometheus) ─────────
from fastapi.responses import Response
from prometheus_client import REGISTRY, generate_latest

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint — scraped on localhost:8000."""
    return Response(content=generate_latest(REGISTRY), media_type="text/plain; charset=utf-8")

from api.routes.sessions import router as sessions_router

app.include_router(sessions_router, prefix="/api/v1")

@app.on_event("startup")
def _init_db_on_startup() -> None:
    """Create the tables the API reads (PostgreSQL, or SQLite when unset)."""
    from db.init import init_db_if_needed

    result = init_db_if_needed()
    logging.getLogger("api.main").info("db_init_on_startup: %s", result)


FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_methods=["*"],
    allow_headers=["*"],
)


AGENT_DEFS = [
    {
        "id": "1",
        "name": "FundamentalAgent",
        "weight": 0.20,
        "domain": "fundamental",
        "signal": "idle",
        "confidence": 0.0,
    },
    {"id": "2", "name": "QuantAgent", "weight": 0.20, "domain": "quant", "signal": "idle", "confidence": 0.0},
    {"id": "3", "name": "MacroAgent", "weight": 0.15, "domain": "macro", "signal": "idle", "confidence": 0.0},
    {"id": "4", "name": "OptionsFlowAgent", "weight": 0.15, "domain": "options", "signal": "idle", "confidence": 0.0},
    {"id": "5", "name": "SentimentAgent", "weight": 0.10, "domain": "sentiment", "signal": "idle", "confidence": 0.0},
    {"id": "6", "name": "TechnicalAgent", "weight": 0.10, "domain": "technical", "signal": "idle", "confidence": 0.0},
    {"id": "7", "name": "BullResearcher", "weight": 0.05, "domain": "research", "signal": "idle", "confidence": 0.0},
    {"id": "8", "name": "BearResearcher", "weight": 0.05, "domain": "research", "signal": "idle", "confidence": 0.0},
    {"id": "9", "name": "BradleyAgent", "weight": 0.03, "domain": "astro", "signal": "idle", "confidence": 0.0},
    {"id": "10", "name": "ElectoralAgent", "weight": 0.03, "domain": "astro", "signal": "idle", "confidence": 0.0},
    {"id": "11", "name": "GannAgent", "weight": 0.03, "domain": "astro", "signal": "idle", "confidence": 0.0},
    {"id": "12", "name": "CycleAgent", "weight": 0.05, "domain": "astro", "signal": "idle", "confidence": 0.0},
    {"id": "13", "name": "TimeWindowAgent", "weight": 0.02, "domain": "astro", "signal": "idle", "confidence": 0.0},
]


class AgentRequest(BaseModel):
    agentId: str
    prompt: str


class AgentResponse(BaseModel):
    result: str


class DashboardAgent(BaseModel):
    id: str
    name: str
    weight: float
    domain: str
    signal: str = "idle"
    confidence: float = 0
    status: str = "idle"


class RegimeProbs(BaseModel):
    bull: float = 0.48
    bear: float = 0.12
    sideways: float = 0.25
    high_vol: float = 0.10
    anomaly: float = 0.05


class EnsembleSignal(BaseModel):
    signal: str
    confidence: float
    buy_count: int
    sell_count: int
    hold_count: int


class DashboardResponse(BaseModel):
    agents: list[DashboardAgent]
    regime: RegimeProbs
    ensemble: EnsembleSignal
    safety_gate: str = "SAFE"
    pnl: float = 0.0
    mode: str = "Live"
    agent_analysis: dict = {}
    price_source: str = "unavailable"
    price: float | None = None
    agents_source: str = "static_placeholder"
    regime_source: str = "static_placeholder"


class _ApiAgent(BaseAgent):
    async def run(self, state: dict) -> dict:
        return {"result": "ok"}


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.4.0"}


@app.get("/api/v1/astro/aspects")
@require_api_key
def get_astro_aspects(request: Request):
    """Current astrological aspects from Swiss Ephemeris — source of truth."""
    from core.aspects import AspectsEngine
    from core.ephemeris import get_planetary_positions

    now = datetime.now(timezone.utc)
    positions = get_planetary_positions(now)
    engine = AspectsEngine()
    report = engine.compute(positions)

    return {
        "timestamp": now.isoformat(),
        "aspects": [
            {
                "planet1": a.planet1,
                "planet2": a.planet2,
                "type": a.aspect_type.value if hasattr(a.aspect_type, "value") else str(a.aspect_type),
                "orb": round(a.orb, 2),
                "signature": a.signature,
            }
            for a in report.aspects
        ],
        "source": "swiss_ephemeris",
    }


@app.get("/api/v1/dashboard", response_model=DashboardResponse)
@require_api_key
def get_dashboard(request: Request):
    agents = [DashboardAgent(**a) for a in AGENT_DEFS]

    buy_count = sum(1 for a in agents if a.signal == "LONG")
    sell_count = sum(1 for a in agents if a.signal == "SHORT")
    hold_count = 13 - buy_count - sell_count

    net_signal = (
        "HOLD"
        if buy_count + sell_count == 0
        else ("BUY" if buy_count > sell_count else "SELL" if sell_count > buy_count else "HOLD")
    )

    # Gann/Bradley/Elliot need a real 90-bar series — never run them on generated data
    import importlib.util

    agent_results: dict = {}
    price_source = "unavailable"
    price: float | None = None
    prices: list | None = None
    try:
        import httpx

        r = httpx.get(
            "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
            params={"vs_currency": "usd", "days": 90},
            timeout=10,
        )
        if r.status_code == 200:
            raw = r.json().get("prices", [])
            if len(raw) >= 90:
                prices = [[int(p[0]), p[1] * 0.99, p[1] * 1.01, p[1] * 0.99, p[1], 5000] for p in raw[-90:]]
                price = prices[-1][4]
                price_source = "coingecko"
    except Exception as exc:
        logging.getLogger("api.main").warning("dashboard_price_fetch_failed: %s", exc)

    if prices:
        for agent_key, fname, clsname in [
            ("gann", "gann_agent.py", "GannAgent"),
            ("bradley", "bradley_agent.py", "BradleyAgent"),
            ("elliot", "elliot_agent.py", "ElliotAgent"),
        ]:
            try:
                spec = importlib.util.spec_from_file_location(agent_key, f"agents/_impl/{fname}")
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    state = {"symbol": "BTCUSDT", "current_price": price, "_price_data": prices}
                    result = asyncio.run(getattr(mod, clsname)().analyze(state))
                    agent_results[agent_key] = {
                        "signal": result.signal.value if hasattr(result.signal, "value") else str(result.signal),
                        "confidence": result.confidence,
                        "reasoning": result.reasoning,
                        "sources": result.sources,
                        "metadata": dict(result.metadata) if hasattr(result.metadata, "items") else {},
                    }
            except Exception as e:
                agent_results[agent_key] = {"signal": "ERROR", "confidence": 0, "reasoning": str(e), "sources": []}

    return DashboardResponse(
        agents=agents,
        regime=RegimeProbs(),
        ensemble=EnsembleSignal(
            signal=net_signal,
            confidence=round(buy_count / 13, 2) if net_signal == "BUY" else 0.5,
            buy_count=buy_count,
            sell_count=sell_count,
            hold_count=hold_count,
        ),
        agent_analysis=agent_results,
        price_source=price_source,
        price=price,
    )


@app.post("/api/v1/agent/run")
@require_api_key

def run_agent(req: AgentRequest, request: Request):
    """Return decisions from agents with real ephemeris, aspects, and honest ensemble."""
    logger = logging.getLogger("api.main")
    import importlib
    import time
    from datetime import datetime, timezone

    start = time.time()

    # ── 1. Real ephemeris & aspects ──
    try:
        from core.aspects import AspectsEngine
        from core.ephemeris import get_planetary_positions

        dt = datetime.now(timezone.utc)
        positions = get_planetary_positions(dt)
        engine = AspectsEngine()
        report = engine.compute(positions)
        aspects = (
            [
                {
                    "planet1": a.planet1,
                    "planet2": a.planet2,
                    "type": str(a.aspect_type.name).lower()
                    if hasattr(a.aspect_type, "name")
                    else str(a.aspect_type).lower(),
                    "orb": round(a.orb, 2),
                    "applies": a.applies,  # Aspect has no .score — orb/applies are the real fields
                }
                for a in report.aspects
            ]
            if hasattr(report, "aspects")
            else []
        )
        aspects_source = "swiss_ephemeris"
        muhurta_score = None  # not computed on this path — null beats a fake 100/100
    except Exception:
        aspects = []
        aspects_source = "unavailable"
        muhurta_score = None

    # ── 2. CoinGecko real price ──
    price_source = "unavailable"
    try:
        import json
        import urllib.request

        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        req_url = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_url, timeout=5) as resp:  # nosec B310
            data = json.loads(resp.read())
        real_price = float(data["bitcoin"]["usd"])
        price_source = "coingecko"
    except Exception as exc:
        logger.warning("agent_run_price_fetch_failed: %s", exc)
        real_price = None
    price = float(req.price) if hasattr(req, "price") and req.price else real_price

    # ── 3. Run agents — only on a real price series ──
    if price_source != "coingecko" or price is None:
        return {
            "result": {
                "agents": [],
                "ensemble": None,
                "aspects_source": aspects_source,
                "muhurta_placeholder": True,
                "price": None,
                "price_source": price_source,
                "processing_time_ms": round((time.time() - start) * 1000, 1),
                "note": "no real price series — agents skipped",
            }
        }

    AGENT_SPECS = [
        ("1", "FundamentalAgent", "fundamental"),
        ("2", "QuantAgent", "quant"),
        ("3", "MacroAgent", "macro"),
        ("4", "OptionsFlowAgent", "options"),
        ("5", "SentimentAgent", "sentiment"),
        ("6", "TechnicalAgent", "technical"),
        ("7", "BullResearcher", "research"),
        ("8", "BearResearcher", "research"),
        ("9", "ElectoralAgent", "astro"),
        ("10", "BradleyAgent", "astro"),
        ("11", "TimeWindowAgent", "astro"),
        ("12", "GannAgent", "astro"),
        ("13", "CycleAgent", "astro"),
    ]
    def _snake(agent_name: str) -> str:
        return re.sub(r"(?<=[a-z])([A-Z])", r"_\1", agent_name).lower()

    agent_decisions = []
    for aid, name, domain in AGENT_SPECS:
        try:
            fname = "agents/_impl/ml_predictor_agent.py" if name == "MLPredictorAgent" else f"agents/_impl/{_snake(name)}.py"
            spec = importlib.util.spec_from_file_location(name.lower(), fname)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                agent_cls = getattr(mod, name, None) or getattr(mod, name + "Agent", None)
                if agent_cls:
                    state = {"symbol": "BTCUSDT", "current_price": price}
                    # RAG context injection (P1 — RAG-First architecture)
                    try:
                        from knowledge.rag_index import retrieve_context
                        rag_ctx = retrieve_context(req.prompt, top_k=3)
                        if rag_ctx:
                            state["rag_context"] = rag_ctx
                    except Exception:
                        pass
                    result = asyncio.run(agent_cls().analyze(state))
                    if result is None:
                        raise RuntimeError("async agent not supported")
                    signal = getattr(
                        getattr(result, "signal", None), "value", str(getattr(result, "signal", "NEUTRAL"))
                    )
                    confidence = getattr(result, "confidence", 50)
                    reasoning = getattr(result, "reasoning", "")[:200]
                    agent_decisions.append(
                        {
                            "id": aid,
                            "name": name,
                            "signal": str(signal).upper(),
                            "confidence": int(confidence),
                            "reasoning": reasoning,
                        }
                    )
                    continue
            raise RuntimeError("import failed")
        except Exception as exc:
            import traceback; print(f"agent_import_failed agent={name} error={exc} traceback={traceback.format_exc()}")
            # Fallback: neutral based on domain
            confidence = 50
            signal = "NEUTRAL"
            reasoning = f"No real data — agent {name} unavailable"
            agent_decisions.append(
                {"id": aid, "name": name, "signal": signal, "confidence": confidence, "reasoning": reasoning}
            )

    # ── 4. Honest ensemble (no bias) ──
    buy_count = sum(1 for a in agent_decisions if a["signal"] == "LONG")
    sell_count = sum(1 for a in agent_decisions if a["signal"] == "SHORT")
    neutral_count = 13 - buy_count - sell_count

    if buy_count > sell_count and buy_count >= 7:
        ensemble_action = "BUY"
    elif sell_count > buy_count and sell_count >= 7:
        ensemble_action = "SELL"
    else:
        ensemble_action = "HOLD"

    if buy_count + sell_count > 0:
        ensemble_conf = round(
            sum(a["confidence"] for a in agent_decisions if a["signal"] in ("LONG", "SHORT")) / (buy_count + sell_count)
        )
    else:
        ensemble_conf = 50

    price_label = f"${price:,.0f}" if price is not None else "недоступна"

    return {
        "result": {
            "agents": agent_decisions,
            "ensemble": {
                "action": ensemble_action,
                "confidence": ensemble_conf,
                "buy_count": buy_count,
                "sell_count": sell_count,
                "neutral_count": neutral_count,
                "recommendation": f"Цена: {price_label} | "
                + (
                    "Открыть LONG с SL −3%"
                    if ensemble_action == "BUY"
                    else "Открыть SHORT с SL +3%"
                    if ensemble_action == "SELL"
                    else "Ждать пробоя диапазона"
                ),
                "risk_factors": [
                    "Muhurta score: unavailable (placeholder — not computed)",
                    f"Aspects found: {len(aspects)}",
                    f"Price source: {price_source}",
                ],
                "astro_factors": [
                    f"Aspects: {len(aspects)} planetary angles ({aspects_source})",
                    "Muhurta: not computed (placeholder, not from Swiss Ephemeris)",
                ][:2],
            },
            "price": price,
            "price_source": price_source,
            "aspects_source": aspects_source,
            "muhurta_placeholder": muhurta_score is None,
            "processing_time_ms": round((time.time() - start) * 1000, 1),
        }
    }


@app.get("/api/v1/astro/interpretation")
@require_api_key
def get_interpretation(request: Request):
    """Vedic + astro interpretation for traders: verdict, Muhurta, Choghadiya, Nakshatra."""
    from datetime import datetime, timezone

    from core.aspects import AspectsEngine
    from core.ephemeris import get_planetary_positions

    try:
        dt = datetime.now(timezone.utc)
        positions = get_planetary_positions(dt)
        engine = AspectsEngine()
        report = engine.compute(positions)
        aspects = report.aspects
        aspects_source = "swiss_ephemeris"
    except Exception:
        aspects = []
        aspects_source = "unavailable"

    # Score each aspect (Aspect objects → dict records)
    aspect_records = []
    for a in aspects:
        a_type = str(a.aspect_type.name).lower() if hasattr(a.aspect_type, "name") else str(a.aspect_type).lower()
        orb = abs(a.orb)
        if a_type in ("trine", "sextile"):
            score = max(0, 5.0 - orb / 2)
            label = "favourable" if orb <= 3 else "slightly_favourable"
            icon = "✅" if orb <= 3 else "↗️"
        elif a_type in ("square", "opposition"):
            score = -max(0, 5.0 - orb / 2)
            label = "unfavourable" if orb <= 3 else "slightly_unfavourable"
            icon = "⚠️" if orb <= 3 else "↘️"
        else:
            score = 5.0 - abs(abs(orb) - 2) if abs(orb) <= 5 else 0
            label = "neutral"
            icon = "➖"
        score = round(score, 2)
        aspect_records.append(
            {
                "planet1": a.planet1,
                "planet2": a.planet2,
                "type": a_type,
                "orb": round(orb, 2),
                "icon": icon,
                "label": label,
                "score": score,
            }
        )

    fav_scores = [a["score"] for a in aspect_records if "favourable" in a["label"]]
    unfav_scores = [a["score"] for a in aspect_records if "unfavourable" in a["label"]]
    aspect_avg = (sum(fav_scores) + sum(unfav_scores)) / max(len(fav_scores) + len(unfav_scores), 1)

    # Simple Muhurta from Nakshatra
    panchanga_source = "unavailable"
    try:
        from core.panchanga import calculate_panchanga, get_choghadiya

        panchanga = calculate_panchanga(dt)
        n = panchanga.get("nakshatra", {}) if isinstance(panchanga, dict) else {}
        n_name = n.get("name") if isinstance(n, dict) else None
        n_good = n.get("good") if isinstance(n, dict) else None
        n_grade = None if n_good is None else ("good" if n_good else "mixed")
        n_mult = None if n_good is None else (0.8 if n_good else 0.5)
        muhurta_score = None if n_good is None else (90 if n_good else 50)
        slots = get_choghadiya(dt) if callable(get_choghadiya) else []
        current = slots[0] if slots else None
        panchanga_source = "swiss_ephemeris"
    except Exception:
        n_name = None
        n_grade = None
        n_mult = None
        muhurta_score = None
        slots = []
        current = None

    composite = (
        round(max(0, min(100, 50 + aspect_avg * 5 + muhurta_score * 0.3)), 1)
        if muhurta_score is not None
        else None
    )

    if muhurta_score is None:
        verdict, v_icon, v_text = "unavailable", "⚪", "Панчанга недоступна — Muhurta не рассчитана"
    elif muhurta_score >= 80 and len(fav_scores) > len(unfav_scores):
        verdict, v_icon, v_text = "favourable", "🟢", "Благоприятное время для входа"
    elif muhurta_score >= 50 or len(fav_scores) >= len(unfav_scores):
        verdict, v_icon, v_text = "caution", "🟡", "Нейтрально — входить осторожно, с уменьшенным размером"
    else:
        verdict, v_icon, v_text = "avoid", "🔴", "Неблагоприятно — лучше воздержаться от входа"

    return {
        "verdict": verdict,
        "verdict_icon": v_icon,
        "verdict_text": v_text,
        "composite_score": composite,
        "muhurta_score": muhurta_score,
        "nakshatra": n_name,
        "nakshatra_grade": n_grade,
        "nakshatra_multiplier": n_mult,
        "choghadiya_current": (
            {
                "name": current.get("name", "?") if isinstance(current, dict) else None,
                "icon": current.get("icon") if isinstance(current, dict) else None,
                "quality": current.get("quality") if isinstance(current, dict) else None,
                "recommended": current.get("recommended") if isinstance(current, dict) else None,
            }
            if isinstance(current, dict)
            else None
        ),
        "choghadiya_slots": [
            {
                "period": i,
                "name": s.get("name", "?"),
                "start": s.get("start", "--"),
                "end": s.get("end", "--"),
                "icon": s.get("icon", "QUESTION"),
                "quality": s.get("quality", "--"),
            }
            for i, s in enumerate(slots[:8])
            if isinstance(s, dict)
        ],
        "top_favourable": [
            {
                "planet1": a["planet1"],
                "planet2": a["planet2"],
                "type": a["type"],
                "icon": a["icon"],
                "orb": a["orb"],
                "score": a["score"],
            }
            for a in sorted([a for a in aspect_records if "favourable" in a["label"]], key=lambda x: -x["score"])[:5]
        ],
        "top_unfavourable": [
            {
                "planet1": a["planet1"],
                "planet2": a["planet2"],
                "type": a["type"],
                "icon": a["icon"],
                "orb": a["orb"],
                "score": a["score"],
            }
            for a in sorted([a for a in aspect_records if "unfavourable" in a["label"]], key=lambda x: x["score"])[:5]
        ],
        "aspects_source": aspects_source,
        "panchanga_source": panchanga_source,
        "placeholder": muhurta_score is None,
    }






# ── Serve React production build (after all API routes) ──
import os

react_dist = os.path.join(os.path.dirname(__file__), "..", "web-react", "dist")
if os.path.isdir(react_dist):
    app.mount("/", StaticFiles(directory=react_dist, html=True), name="react")
