"""
AstroFin Sentinel API — FastAPI backend for React frontend.

Endpoints:
    POST /api/v1/agent/run — run an agent with LLM routing
    WS   /ws/agent/{agent_id} — WebSocket real-time agent streaming
    GET  /health — health check
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.base_agent import BaseAgent
from core.llm_router import route

app = FastAPI(title="AstroFin Sentinel API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentRequest(BaseModel):
    agentId: str
    prompt: str


class AgentResponse(BaseModel):
    result: str


class _ApiAgent(BaseAgent):
    """Concrete agent for API endpoint — delegates to LLM router."""
    async def run(self, state: dict) -> dict:
        return {"result": "ok"}


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.3.0"}


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
