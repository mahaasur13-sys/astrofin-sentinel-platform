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
