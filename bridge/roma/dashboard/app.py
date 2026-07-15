#!/usr/bin/env python3
"""ROMA Observable OS — Unified Control Plane Dashboard."""
from dash import Dash, html, dcc, callback, Output, Input
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from datetime import datetime
import time

# ── Projection Engine import ──────────────────────────────────────
import sys
sys.path.insert(0, '/home/workspace/roma-execution-bridge')
from dashboard.projection_engine import ProjectionEngine

# ── Init ──────────────────────────────────────────────────────────
app = Dash(__name__, external_stylesheets=[dbc.themes.DARK])
app.title = "ROMA — Observable OS"
pe = ProjectionEngine()
_pe_refresh = time.time()

# ── Seed simulation data ──────────────────────────────────────────
def seed():
    global _pe_refresh
    now = int(datetime.now().strftime("%s")) * 1000
    for i, ev in enumerate([
        {"type": "JOB_SUBMITTED", "payload": {"job_id": "job-001", "tenant_id": "acme", "plugin": "ml_training"}},
        {"type": "JOB_QUEUED", "payload": {"job_id": "job-001"}},
        {"type": "JOB_SCHEDULED", "payload": {"job_id": "job-001", "gpu_node": "gpu-node-1"}},
        {"type": "JOB_STARTED", "payload": {"job_id": "job-001"}},
        {"type": "JOB_COMPLETED", "payload": {"job_id": "job-001", "cost": 0.0275}},
    ]):
        pe.ingest({**ev, "ts": now + i * 500})
    pe.ingest({"type": "GPU_STATE_SNAPSHOT", "ts": now, "payload": {
        "gpu-node-1": {"utilization_pct": 87, "vram_used_gb": 7.2, "vram_total_gb": 10.5, "active_jobs": 3},
        "gpu-node-2": {"utilization_pct": 45, "vram_used_gb": 3.1, "vram_total_gb": 10.5, "active_jobs": 1},
    }})
    pe.ingest({"type": "RAFT_STATE_SNAPSHOT", "ts": now, "payload": {
        "leader": "node-0", "term": 5, "commit_index": 148,
        "nodes": {"node-0": "leader", "node-1": "follower", "node-2": "follower"}
    }})
    _pe_refresh = time.time()

seed()

# ── Helpers ──────────────────────────────────────────────────────
STATUS_COLOR = {
    "SUBMITTED": "#6c757d", "QUEUED": "#ffc107", "SCHEDULED": "#17a2b8",
    "RUNNING": "#0d6efd", "COMPLETED": "#28a745", "FAILED": "#dc3545"
}

def make_gpu_bar(node: str, state: dict) -> go.Figure:
    used = state["vram_used_gb"]
    total = state["vram_total_gb"]
    free = total - used
    pct = state["utilization_pct"]
    bar = go.Figure(go.Bar(
        y=[node], x=[used], name="Used",
        marker_color="#e74c3c", orientation="h"
    ))
    bar.add_trace(go.Bar(y=[node], x=[free], name="Free",
                          marker_color="#2ecc71", orientation="h"))
    bar.update_layout(
        barmode="stack", height=80,
        title=f"{pct}% | {used:.1f}/{total:.1f} GB",
        yaxis_title="", xaxis_title="VRAM (GB)",
        showlegend=True, legend=dict(orientation="h", y=1.12),
        template="plotly_dark", margin=dict(l=40, r=20, t=40, b=20)
    )
    return bar

def make_cost_gauge() -> go.Figure:
    return go.Figure(go.Indicator(
        mode="gauge+number", value=0.0275,
        number={"prefix": "$", "valueformat": ".4f"},
        gauge={
            "axis": {"range": [0, 1]}, "bar": {"color": "#f39c12"},
            "steps": [
                {"range": [0, 0.3], "color": "#2ecc71"},
                {"range": [0.3, 0.7], "color": "#f39c12"},
                {"range": [0.7, 1], "color": "#e74c3c"}
            ]
        }, title={"text": "Last Job Cost"}, domain={"x": [0, 1], "y": [0, 1]}
    ))

def make_timeline() -> go.Figure:
    jobs = pe.project_execution_timeline()
    if not jobs:
        return go.Figure()
    fig = go.Figure()
    for j in jobs:
        color = STATUS_COLOR.get(j["status"], "#999")
        fig.add_trace(go.Bar(
            x=[(j["end"] or j["start"] + 1000) - j["start"]],
            y=[j["plugin"]], base=j["start"],
            marker_color=color, orientation="h",
            text=j["job_id"], insidetextanchor="start",
            customdata=[j["cost"]],
            hovertemplate=f"{j['job_id']}<br>Status: {j['status']}<br>Cost: $%{{customdata:.4f}}<extra></extra>"
        ))
    fig.update_layout(
        title="Execution Timeline", template="plotly_dark",
        xaxis_title="Time (ms)", height=150,
        showlegend=False, margin=dict(l=100, r=20, t=30, b=30)
    )
    return fig

# ── Layout ────────────────────────────────────────────────────────
app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("🧠 ROMA — Observable OS", className="text-center my-3"), width=12)),

    dcc.Interval(id="refresh", interval=2000, n_intervals=0),

    # ── Execution Timeline ───────────────────────────────────────
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📊 Execution Timeline"),
                dbc.CardBody(dcc.Graph(id="timeline-chart", figure=make_timeline()))
            ], className="mb-3")
        ], width=8),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("💰 Last Job Cost"),
                dbc.CardBody(dcc.Graph(id="cost-gauge", figure=make_cost_gauge()))
            ], className="mb-3")
        ], width=4),
    ]),

    # ── GPU Heatmap ──────────────────────────────────────────────
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🎮 GPU Utilization Heatmap"),
                dbc.CardBody(dcc.Graph(id="gpu-chart"))
            ], className="mb-3")
        ], width=12)
    ]),

    # ── Raft + Queue ────────────────────────────────────────────
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🗳️ Raft Consensus State"),
                dbc.CardBody(html.Pre(id="raft-state", children="loading...",
                                      style={"font-size": "11px", "color": "#00ff41"}))
            ], className="mb-3")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📋 Job Queue"),
                dbc.CardBody(html.Ul(id="job-list", children=[
                    html.Li(f"{j['job_id']} — {j['status']}") for j in pe.project_execution_timeline()
                ]))
            ], className="mb-3")
        ], width=6),
    ]),

    # ── Audit Log ────────────────────────────────────────────────
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🔍 Immutable Audit Log"),
                dbc.CardBody(html.Pre(id="audit-log", children="", style={"font-size": "10px"}))
            ], className="mb-3")
        ], width=12)
    ]),

    # ── Cost Simulator ──────────────────────────────────────────
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🔮 What-If Cost Simulator"),
                dbc.CardBody([
                    dbc.InputGroup([
                        dbc.InputGroupText("Task"), dbc.Input(id="sim-task", value="train YOLOv8"),
                        dbc.InputGroupText("GPU sec"), dbc.Input(id="sim-gpu", value=60, type="number"),
                    ], className="mb-2"),
                    dbc.InputGroup([
                        dbc.InputGroupText("Batch size"), dbc.Input(id="sim-batch", value=32, type="number"),
                        dbc.InputGroupText("Tier"), dbc.Select(id="sim-tier", options=[
                            {"label": "FREE", "value": "FREE"},
                            {"label": "PRO", "value": "PRO"},
                            {"label": "ENTERPRISE", "value": "ENTERPRISE"},
                        ], value="PRO"),
                    ], className="mb-2"),
                    html.Div(id="sim-result", className="mt-2"),
                ])
            ], className="mb-3")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📈 System Health"),
                dbc.CardBody(html.Div(id="health-summary"))
            ], className="mb-3")
        ], width=6),
    ]),
], fluid=True)

# ── Callbacks ────────────────────────────────────────────────────
@callback(
    Output("timeline-chart", "figure"),
    Output("cost-gauge", "figure"),
    Output("gpu-chart", "figure"),
    Output("raft-state", "children"),
    Output("job-list", "children"),
    Output("audit-log", "children"),
    Input("refresh", "n_intervals"),
)
def refresh(n):
    gpu_state = pe.project_gpu_heatmap()
    gpu_fig = make_timeline()  # placeholder
    for node, state in gpu_state.items():
        gpu_fig = make_gpu_bar(node, state)

    raft = pe.project_raft_cluster()
    raft_txt = f"Leader: {raft.get('leader', '?')} | Term: {raft.get('term', 0)} | CommitIndex: {raft.get('commit_index', 0)}\n"
    for n, role in raft.get("nodes", {}).items():
        raft_txt += f"  {n}: {role}\n"

    jobs = pe.project_execution_timeline()
    job_items = [html.Li(
        html.Span(j["job_id"], style={"color": STATUS_COLOR.get(j["status"], "#fff")}),
        f" | {j['status']} | gpu={j['gpu']} | ${j['cost']:.4f}"
    ) for j in jobs]

    events = [f"[{e['ts']}] {e['type']} → {list(e.get('payload',{}).keys())}" for e in pe.events[-20:]]
    audit_txt = "\n".join(events) if events else "No events yet"

    timeline = make_timeline()
    cost_gauge = make_cost_gauge()

    return timeline, cost_gauge, gpu_fig, raft_txt, job_items, audit_txt

@callback(
    Output("sim-result", "children"),
    Input("sim-task", "value"),
    Input("sim-gpu", "value"),
    Input("sim-batch", "value"),
    Input("sim-tier", "value"),
)
def simulate(task, gpu_sec, batch, tier):
    if not gpu_sec:
        raise PreventUpdate
    rate = {"FREE": 0.0001, "PRO": 0.0002, "ENTERPRISE": 0.0001}.get(tier, 0.0002)
    base_cost = gpu_sec * rate
    if batch and batch > 64:
        base_cost *= 1.5
    return dbc.Alert([
        html.Strong(f"Estimated: ${base_cost:.4f}"),
        html.Br(),
        f"{tier} tier · {gpu_sec}s GPU · batch={batch}"
    ], color="info")

if __name__ == "__main__":
    print("Starting ROMA Dashboard...")
    app.run(host="0.0.0.0", port=8050, debug=False)
