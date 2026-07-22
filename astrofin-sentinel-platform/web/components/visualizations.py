"""Visualizations tab — аналитическая панель с Plotly-графиками.

Показывает:
  - Распределение сигналов агентов (bar)
  - Веса агентов (pie)
  - Уверенность агентов (scatter)
  - История сессий (line)
  - Режимы волатильности (area)
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html
import dash_bootstrap_components as dbc


def _load_sessions():
    """Load session data from history DB JSON export."""
    sessions = []
    db_path = os.path.join(_ROOT, "core", "history.db")
    work_dir = os.path.join(_ROOT, "work")

    for path in [db_path, os.path.join(work_dir, "history.db")]:
        if not os.path.exists(path):
            continue
        import sqlite3
        try:
            conn = sqlite3.connect(path)
            rows = conn.execute(
                "SELECT session_id, ticker, signal, confidence, risk_pct, regime, timestamp, agents_data "
                "FROM sessions ORDER BY timestamp DESC LIMIT 100"
            ).fetchall()
            for r in rows:
                agents_data = {}
                try:
                    agents_data = json.loads(r[7]) if r[7] else {}
                except (json.JSONDecodeError, TypeError):
                    pass
                sessions.append({
                    "session_id": r[0],
                    "ticker": r[1],
                    "signal": r[2],
                    "confidence": float(r[3] or 0),
                    "risk_pct": float(r[4] or 0),
                    "regime": r[5] or "UNKNOWN",
                    "timestamp": r[6],
                    "agents": agents_data,
                })
            conn.close()
        except Exception:
            pass

    return sessions


def _load_agent_weights():
    """Agent weight definitions from AGENTS.md."""
    return [
        ("Fundamental", 20), ("Quant", 20), ("Macro", 15),
        ("Options Flow", 15), ("Sentiment", 10), ("Technical", 10),
        ("Bull", 5), ("Bear", 5),
    ]


def _build_weight_pie():
    """Pie chart: agent weight distribution."""
    weights = _load_agent_weights()
    fig = px.pie(
        names=[w[0] for w in weights],
        values=[w[1] for w in weights],
        title="Agent Weight Distribution",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    fig.update_traces(textinfo="label+percent", textfont_size=11)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e0e0e0",
        margin=dict(t=40, b=0, l=0, r=0),
        height=320,
    )
    return fig


def _build_signal_distribution(sessions):
    """Bar chart: BUY/SELL/NEUTRAL distribution from sessions."""
    if not sessions:
        return _empty_chart("No session data", "Run analysis to populate signal distribution")

    sig_counts = {"BUY": 0, "SELL": 0, "HOLD": 0, "NEUTRAL": 0}
    for s in sessions:
        sig = (s["signal"] or "NEUTRAL").upper()
        if sig in sig_counts:
            sig_counts[sig] += 1
        else:
            sig_counts["NEUTRAL"] += 1

    colors = {"BUY": "#00cc66", "SELL": "#ff4444", "HOLD": "#ffaa00", "NEUTRAL": "#888888"}
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=list(sig_counts.keys()),
        y=list(sig_counts.values()),
        marker_color=[colors.get(k, "#888") for k in sig_counts],
        text=list(sig_counts.values()),
        textposition="outside",
    ))
    fig.update_layout(
        title=f"Signal Distribution ({sum(sig_counts.values())} sessions)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e0e0e0",
        margin=dict(t=40, b=0, l=0, r=0),
        height=320,
        yaxis_title="Count",
    )
    return fig


def _build_confidence_scatter(sessions):
    """Scatter: confidence per session with regime coloring."""
    if not sessions:
        return _empty_chart("No session data", "Run analysis to populate confidence scatter")

    regime_colors = {"LOW": "#00cc66", "NORMAL": "#3399ff", "HIGH": "#ffaa00", "EXTREME": "#ff4444"}
    df_data = []
    for i, s in enumerate(sessions):
        df_data.append({
            "session": i + 1,
            "confidence": s["confidence"],
            "regime": s.get("regime", "UNKNOWN"),
            "signal": s.get("signal", "?"),
        })

    fig = px.scatter(
        df_data,
        x="session",
        y="confidence",
        color="regime",
        hover_data=["signal"],
        title="Agent Confidence by Session",
        color_discrete_map=regime_colors,
    )
    fig.update_traces(marker=dict(size=10, line=dict(width=1, color="#333")))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e0e0e0",
        margin=dict(t=40, b=0, l=0, r=0),
        height=320,
    )
    fig.add_hline(y=0.7, line_dash="dash", line_color="#00cc66", annotation_text="High confidence")
    fig.add_hline(y=0.3, line_dash="dash", line_color="#ff4444", annotation_text="Low confidence")
    return fig


def _build_regime_timeline(sessions):
    """Area chart: regime distribution over time."""
    if not sessions:
        return _empty_chart("No regime data", "Run analysis to populate regime timeline")

    sessions_chronological = list(reversed(sessions))
    regime_map = {"LOW": 1, "NORMAL": 2, "HIGH": 3, "EXTREME": 4}
    ts = [s.get("timestamp", f"Session {i}") for i, s in enumerate(sessions_chronological)]
    vals = [regime_map.get(s.get("regime", "UNKNOWN"), 2) for s in sessions_chronological]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ts, y=vals,
        mode="lines+markers",
        fill="tozeroy",
        line=dict(color="#3399ff", width=2),
        marker=dict(size=6),
        name="Regime",
    ))
    fig.update_yaxes(
        tickvals=[1, 2, 3, 4],
        ticktext=["LOW", "NORMAL", "HIGH", "EXTREME"],
        range=[0.5, 4.5],
    )
    fig.update_layout(
        title="Volatility Regime Timeline",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e0e0e0",
        margin=dict(t=40, b=40, l=0, r=0),
        height=320,
        yaxis_title="",
        xaxis_title="",
    )
    return fig


def _build_risk_pct_line(sessions):
    """Line chart: risk_pct per session."""
    if not sessions:
        return _empty_chart("No data", "Run analysis to populate risk line")

    sessions_rev = list(reversed(sessions))
    ts = [s.get("timestamp", f"Session {i}") for i, s in enumerate(sessions_rev)]
    risk_vals = [s.get("risk_pct", 0) for s in sessions_rev]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ts, y=risk_vals,
        mode="lines+markers",
        line=dict(color="#ffaa00", width=2),
        marker=dict(size=6),
        name="Risk %",
    ))
    fig.update_layout(
        title="Dynamic Risk Allocation (%)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e0e0e0",
        margin=dict(t=40, b=40, l=0, r=0),
        height=320,
        yaxis_title="risk_pct",
    )
    return fig


def _build_summary_cards(sessions):
    """KPI summary cards row."""
    total = len(sessions)
    if total == 0:
        return dbc.Row([dbc.Col(html.P("No session data yet. Run an analysis to populate.", className="text-muted"))])

    buys = sum(1 for s in sessions if (s.get("signal") or "").upper() == "BUY")
    sells = sum(1 for s in sessions if (s.get("signal") or "").upper() == "SELL")
    avg_conf = sum(s.get("confidence", 0) for s in sessions) / total * 100
    high_regime = sum(1 for s in sessions if s.get("regime") in ("HIGH", "EXTREME"))

    cards = [
        ("📊 Sessions", str(total), "text-info"),
        ("📈 BUY", str(buys), "text-success"),
        ("📉 SELL", str(sells), "text-danger"),
        ("🎯 Avg Conf", f"{avg_conf:.1f}%", "text-warning"),
        ("⚠️ High Regime", f"{high_regime}/{total}", "text-warning" if high_regime > total * 0.3 else "text-info"),
    ]

    return dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H6(title, className="text-muted mb-1"),
                    html.H3(value, className=f"{color} mb-0"),
                ]),
                className="bg-dark border-secondary",
            ),
            width="auto",
        )
        for title, value, color in cards
    ], className="g-2 mb-3")


def _empty_chart(title, subtitle):
    fig = go.Figure()
    fig.add_annotation(
        text=subtitle, x=0.5, y=0.5,
        showarrow=False, font=dict(size=14, color="#888"),
    )
    fig.update_layout(
        title=title,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e0e0e0",
        height=320,
    )
    return fig


def visualizations_tab():
    sessions = _load_sessions()

    return html.Div([
        html.H4("📊 Visual Analytics", className="mb-3"),
        _build_summary_cards(sessions),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=_build_weight_pie(), config={"displayModeBar": False}), md=6),
            dbc.Col(dcc.Graph(figure=_build_signal_distribution(sessions), config={"displayModeBar": False}), md=6),
        ], className="mb-3"),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=_build_confidence_scatter(sessions), config={"displayModeBar": False}), md=6),
            dbc.Col(dcc.Graph(figure=_build_regime_timeline(sessions), config={"displayModeBar": False}), md=6),
        ], className="mb-3"),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=_build_risk_pct_line(sessions), config={"displayModeBar": False}), md=6),
        ]),
    ])
