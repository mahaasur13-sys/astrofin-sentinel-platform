"""
AstroFin Sentinel API — FastAPI backend for React frontend.

Endpoints:
    POST /api/v1/agent/run — run an agent with LLM routing
    GET  /health            — health check
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.base_agent import BaseAgent
from core.llm_router import route

app = FastAPI(title="AstroFin Sentinel API", version="0.2.0")

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


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.2.0"}


@app.post("/api/v1/agent/run", response_model=AgentResponse)
def run_agent(req: AgentRequest):
    agent = BaseAgent(
        name=req.agentId,
        instructions_path=None,
        domain=None,
        weight=0.0,
    )
    result = agent.generate(prompt=req.prompt, session_id=req.agentId)
    return {"result": result}
