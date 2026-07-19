"""
AstroFin Sentinel API — FastAPI backend for React frontend.

Endpoints:
    GET  /api/v1/dashboard        — full dashboard state (agents, regime, ensemble)
    POST /api/v1/agent/run        — run an agent with LLM routing
    WS   /ws/agent/{agent_id}     — WebSocket real-time agent streaming
    GET  /health                  — health check
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from core.base_agent import BaseAgent
from core.llm_router import route

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


class _ApiAgent(BaseAgent):
    async def run(self, state: dict) -> dict:
        return {"result": "ok"}


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.4.0"}


@app.get("/api/v1/dashboard", response_model=DashboardResponse)
def get_dashboard():
    agents = [DashboardAgent(**a) for a in AGENT_DEFS]

    buy_count = sum(1 for a in AGENT_DEFS if a["id"] in ("1", "3", "5", "7", "9", "11", "13"))
    sell_count = sum(1 for a in AGENT_DEFS if a["id"] in ("4", "8"))
    hold_count = 13 - buy_count - sell_count

    net_signal = "BUY" if buy_count > sell_count else "SELL" if sell_count > buy_count else "HOLD"

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
    )


@app.post("/api/v1/agent/run", response_model=AgentResponse)
def run_agent(req: AgentRequest):
    agent = _ApiAgent(
        name=req.agentId,
        instructions_path=None,
        domain=None,
        weight=0.0,
    )
    result = agent.generate(prompt=req.prompt, session_id=req.agentId)
    return {"result": result}


@app.websocket("/ws/agent/{agent_id}")
async def agent_websocket(websocket: WebSocket, agent_id: str):
    await websocket.accept()
    try:
        agent = _ApiAgent(name=agent_id, instructions_path=None, domain=None, weight=0.0)
        await websocket.send_text(f"Agent {agent_id} connected")
        while True:
            data = await websocket.receive_text()
            result = await agent.run({"query": data})
            await websocket.send_json(result)
    except WebSocketDisconnect:
        pass
