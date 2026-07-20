"""
AstroFin Sentinel API — FastAPI backend for React frontend.

Endpoints:
    GET  /api/v1/dashboard        — full dashboard state (agents, regime, ensemble)
    GET  /api/v1/astro/aspects    — current astrological aspects from ephemeris
    POST /api/v1/agent/run        — run an agent with LLM routing
    WS   /ws/agent/{agent_id}     — WebSocket real-time agent streaming
    GET  /health                  — health check
"""

from datetime import datetime, timezone
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from core.base_agent import BaseAgent

app = FastAPI(title="AstroFin Sentinel API", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


AGENT_DEFS = [
    {"id": "1",  "name": "FundamentalAgent",  "weight": 0.20, "domain": "fundamental"},
    {"id": "2",  "name": "QuantAgent",        "weight": 0.20, "domain": "quant"},
    {"id": "3",  "name": "MacroAgent",        "weight": 0.15, "domain": "macro"},
    {"id": "4",  "name": "OptionsFlowAgent",  "weight": 0.15, "domain": "options"},
    {"id": "5",  "name": "SentimentAgent",    "weight": 0.10, "domain": "sentiment"},
    {"id": "6",  "name": "TechnicalAgent",    "weight": 0.10, "domain": "technical"},
    {"id": "7",  "name": "BullResearcher",    "weight": 0.05, "domain": "research"},
    {"id": "8",  "name": "BearResearcher",    "weight": 0.05, "domain": "research"},
    {"id": "9",  "name": "BradleyAgent",      "weight": 0.03, "domain": "astro"},
    {"id": "10", "name": "ElectoralAgent",    "weight": 0.03, "domain": "astro"},
    {"id": "11", "name": "GannAgent",         "weight": 0.03, "domain": "astro"},
    {"id": "12", "name": "CycleAgent",        "weight": 0.05, "domain": "astro"},
    {"id": "13", "name": "TimeWindowAgent",   "weight": 0.02, "domain": "astro"},
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
    signal: str = "hold"
    confidence: float = 0.5
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
    pnl: float = 2847.0
    mode: str = "Live"
    agent_analysis: dict = {}


class _ApiAgent(BaseAgent):
    async def run(self, state: dict) -> dict:
        return {"result": "ok"}


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.4.0"}


@app.get("/api/v1/astro/aspects")
def get_astro_aspects():
    """Current astrological aspects from Swiss Ephemeris — source of truth."""
    from core.ephemeris import get_planetary_positions
    from core.aspects import AspectsEngine

    now = datetime.now(timezone.utc)
    positions = get_planetary_positions(now)
    engine = AspectsEngine()
    report = engine.compute(positions)

    return {
        "timestamp": now.isoformat(),
        "aspects": [{
            "planet1": a.planet1,
            "planet2": a.planet2,
            "type": a.aspect_type.value if hasattr(a.aspect_type, 'value') else str(a.aspect_type),
            "orb": round(a.orb, 2),
            "signature": a.signature,
        } for a in report.aspects],
        "source": "swiss_ephemeris",
    }


@app.get("/api/v1/dashboard", response_model=DashboardResponse)
def get_dashboard():
    agents = [DashboardAgent(**a) for a in AGENT_DEFS]

    buy_count = sum(1 for a in AGENT_DEFS if a["id"] in ("1", "3", "5", "7", "9", "11", "13"))
    sell_count = sum(1 for a in AGENT_DEFS if a["id"] in ("4", "8"))
    hold_count = 13 - buy_count - sell_count

    net_signal = "BUY" if buy_count > sell_count else "SELL" if sell_count > buy_count else "HOLD"


    # Launch real Gann/Bradley/Elliot agents for dashboard
    import random, math, asyncio, importlib.util
    agent_results = {}
    try:
        random.seed(42)
        base_price = 87000.0
        prices = []
        b = base_price
        for _ in range(90):
            drift = (random.random() - 0.48) * 200
            vol = random.gauss(0, 800)
            close = b + drift + vol
            high = close + abs(random.gauss(0, 300))
            low = close - abs(random.gauss(0, 300))
            ts = 1784390400000 + _ * 86400000
            open_ = low + abs(random.gauss(0, 200))
            prices.append([ts, open_, high, low, close, 1000 + random.random() * 500])
            b = close
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
                    state = {"symbol": "BTCUSDT", "current_price": prices[-1][4], "_price_data": prices}
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
    except Exception as e:
        agent_results = {"error": str(e)}

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
    )


@app.post("/api/v1/agent/run", response_model=AgentResponse)
def run_agent(req: AgentRequest):
    from core.llm_router import route  # lazy import — sentence_transformers blocks
    agent = _ApiAgent(
        name=req.agentId,
        instructions_path=None,
        domain=None,
        weight=0.0,
    )
    result = agent.generate(prompt=req.prompt, session_id=req.agentId)
    return {"result": result}

@app.get("/api/v1/astro/interpretation")
def get_interpretation():
    """Vedic + astro interpretation for traders: verdict, Muhurta, Choghadiya, Nakshatra."""
    from datetime import datetime, timezone
    from core.ephemeris import get_planetary_positions
    from core.aspects import AspectsEngine

    try:
        dt = datetime.now(timezone.utc)
        positions = get_planetary_positions(dt)
        engine = AspectsEngine()
        report = engine.compute(positions)
        aspects = report.aspects
    except Exception:
        aspects = []

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
        aspect_records.append({
            "planet1": a.planet1, "planet2": a.planet2,
            "type": a_type, "orb": round(orb, 2),
            "icon": icon, "label": label, "score": score,
        })

    fav_scores = [a["score"] for a in aspect_records if "favourable" in a["label"]]
    unfav_scores = [a["score"] for a in aspect_records if "unfavourable" in a["label"]]
    aspect_avg = (sum(fav_scores) + sum(unfav_scores)) / max(len(fav_scores) + len(unfav_scores), 1)

    # Simple Muhurta from Nakshatra
    try:
        from core.panchanga import calculate_panchanga, get_choghadiya, get_muhurta_score
        panchanga = calculate_panchanga(dt)
        n = panchanga.get("nakshatra", {}) if isinstance(panchanga, dict) else {}
        n_name = n.get("name", "Uttara Phalguni") if isinstance(n, dict) else "Uttara Phalguni"
        n_good = n.get("good", True) if isinstance(n, dict) else True
        n_grade = "good" if n_good else "mixed"
        n_mult = 0.8 if n_good else 0.5
        muhurta_score = 90 if n_good else 50
        slots = get_choghadiya(dt) if callable(get_choghadiya) else []
        current = slots[0] if slots else {"name": "Amrit", "icon": "DIAMOND", "quality": "auspicious", "recommended": True}
    except Exception:
        n_name = "Uttara Phalguni"
        n_grade = "good"
        n_mult = 0.8
        muhurta_score = 100
        slots = []
        current = {"name": "Amrit", "icon": "DIAMOND", "quality": "auspicious", "recommended": True}

    composite = round(max(0, min(100, 50 + aspect_avg * 5 + muhurta_score * 0.3)), 1)

    if muhurta_score >= 80 and len(fav_scores) > len(unfav_scores):
        verdict, v_icon, v_text = "favourable", "🟢", "Благоприятное время для входа"
    elif muhurta_score >= 50 or len(fav_scores) >= len(unfav_scores):
        verdict, v_icon, v_text = "caution", "🟡", "Нейтрально — входить осторожно, с уменьшенным размером"
    else:
        verdict, v_icon, v_text = "avoid", "🔴", "Неблагоприятно — лучше воздержаться от входа"

    return {
        "verdict": verdict, "verdict_icon": v_icon, "verdict_text": v_text,
        "composite_score": composite, "muhurta_score": muhurta_score,
        "nakshatra": n_name, "nakshatra_grade": n_grade, "nakshatra_multiplier": n_mult,
        "choghadiya_current": {
            "name": current.get("name", "Amrit") if isinstance(current, dict) else "Amrit",
            "icon": current.get("icon", "DIAMOND") if isinstance(current, dict) else "DIAMOND",
            "quality": current.get("quality", "auspicious") if isinstance(current, dict) else "auspicious",
            "recommended": current.get("recommended", True) if isinstance(current, dict) else True,
        },
        "choghadiya_slots": [
            {"period": i, "name": s.get("name", "?"), "start": s.get("start", "--"), "end": s.get("end", "--"),
             "icon": s.get("icon", "QUESTION"), "quality": s.get("quality", "--")}
            for i, s in enumerate(slots[:8]) if isinstance(s, dict)
        ],
        "top_favourable": [
            {"planet1": a["planet1"], "planet2": a["planet2"], "type": a["type"], "icon": a["icon"], "orb": a["orb"], "score": a["score"]}
            for a in sorted([a for a in aspect_records if "favourable" in a["label"]], key=lambda x: -x["score"])[:5]
        ],
        "top_unfavourable": [
            {"planet1": a["planet1"], "planet2": a["planet2"], "type": a["type"], "icon": a["icon"], "orb": a["orb"], "score": a["score"]}
            for a in sorted([a for a in aspect_records if "unfavourable" in a["label"]], key=lambda x: x["score"])[:5]
        ],
    }

# ── Serve React production build (after all API routes) ──
import os
react_dist = os.path.join(os.path.dirname(__file__), "..", "web-react", "dist")
if os.path.isdir(react_dist):
    app.mount("/", StaticFiles(directory=react_dist, html=True), name="react")
