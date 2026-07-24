"""web/components/agents_live.py — Sprint 6: 13 Agents Live + Vedic Calendar.

Tab component displaying:
  - Ensemble vote result + score bar
  - Per-agent signal cards
  - Nakshatra Wheel with risk heatmap
  - Vedic calendar (current panchanga)
"""

from __future__ import annotations

from datetime import datetime
import json

import dash_bootstrap_components as dbc
from dash import dcc, html

NAKSHATRA_COLORS = {
    "Ashwini": "#ff6666", "Bharani": "#cc5555", "Krittika": "#ff4444",
    "Rohini": "#66ff66", "Mrigashira": "#88aa88", "Ardra": "#ff2222",
    "Punarvasu": "#88cc88", "Pushya": "#00ff00", "Ashlesha": "#ff5555",
    "Magha": "#cccc66", "Purva Phalguni": "#ffcc44", "Uttara Phalguni": "#66cc66",
    "Hasta": "#66cc66", "Chitra": "#cc8844", "Swati": "#88cc66",
    "Vishakha": "#ccaa44", "Anuradha": "#66aa66", "Jyeshtha": "#ff3333",
    "Mula": "#ff1111", "Purva Ashadha": "#ffaa44", "Uttara Ashadha": "#77cc66",
    "Shravana": "#66ff66", "Dhanishta": "#ccaa44", "Shatabhisha": "#ff6644",
    "Purva Bhadrapada": "#ff5533", "Uttara Bhadrapada": "#66ff44", "Revati": "#88cc88",
}


def _nak_color(nak_name: str) -> str:
    return NAKSHATRA_COLORS.get(nak_name, "#888888")


def get_current_panchanga() -> dict | None:
    try:
        from core.panchanga import calculate_panchanga
        return calculate_panchanga(datetime.utcnow())
    except Exception:
        return None


def nakshatra_wheel_card(p: dict | None) -> dbc.Card:
    if not p:
        return dbc.Card("Panchanga not available", body=True)

    nak = p.get("nakshatra", {})
    nak_name = nak.get("name", "Unknown") if isinstance(nak, dict) else str(nak)
    color = _nak_color(nak_name)
    tithi = p.get("tithi", {})
    tithi_name = tithi.get("name", "-") if isinstance(tithi, dict) else "-"
    muhurta = p.get("muhurta_score", {})
    score = muhurta.get("score", 50) if isinstance(muhurta, dict) else 50

    bar_color = "#00cc66" if score >= 70 else "#ffaa00" if score >= 50 else "#ff4444"

    return dbc.Card(
        [
            dbc.CardHeader("🌙 Vedic Calendar — Current Nakshatra"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div(
                            nak_name,
                            className="fs-4 fw-bold mb-1",
                            style={"color": color},
                        ),
                        html.Div(f"Pada {nak.get('pada', '?')} · Lord {nak.get('lord', '?')}",
                                 className="text-muted small"),
                        html.Div(f"Tithi: {tithi_name}",
                                 className="text-muted small mt-1"),
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Muhurta Score", className="small"),
                        dbc.Progress(
                            value=score, max=100,
                            color="success" if score >= 70 else "warning" if score >= 50 else "danger",
                            className="mb-1",
                        ),
                        html.Span(f"{score}/100", className="small"),
                        html.Div(muhurta.get("verdict", "-"), className="fw-bold mt-1"),
                    ], width=6),
                ]),
                html.Hr(className="my-2"),
                _choghadiya_strip(p.get("choghadiya", [])),
            ]),
        ],
        className="mb-3",
    )


def _choghadiya_strip(periods: list) -> html.Div:
    if not periods:
        return html.Div()
    items = []
    icon_map = {"auspicious": "✅", "profitable": "💰", "energetic": "⚡",
                "inauspicious": "⛔", "anxious": "🔴", "difficult": "⚠️", "slow": "🐌", "neutral": "❓"}
    for p in periods[:8]:
        icon = icon_map.get(p.get("quality", "neutral"), "❓")
        items.append(
            dbc.Col([
                html.Div(icon, className="fs-5 text-center"),
                html.Div(p.get("start", ""), className="small text-center text-muted"),
            ], width=1),
        )
    return dbc.Row(items, className="g-1")


def agent_vote_card(name: str, signal: str, conf: float, reason: str, weight: float) -> dbc.Card:
    sig_color = {"LONG": "success", "SHORT": "danger", "NEUTRAL": "secondary", "HOLD": "warning"}
    badge = sig_color.get(signal, "light")
    return dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col(html.Strong(name), width=5),
                dbc.Col(dbc.Badge(signal, color=badge, className="me-1"), width=2),
                dbc.Col(f"{conf:.0f}%", width=2),
                dbc.Col(f"×{weight:.2f}" if weight > 0 else "info", width=1, className="text-muted small"),
            ]),
            html.Small(reason[:80], className="text-muted") if reason else None,
        ]),
        className="mb-1 agent-vote-card",
    )


def ensemble_header_card(result) -> dbc.Card:
    if result is None:
        return dbc.Card(dbc.CardBody("No ensemble data yet. Run 13 agents first."), className="mb-3")

    sig = result.get("signal", "NEUTRAL")
    score = result.get("score", 0)
    conf = result.get("confidence", 0)
    veto = result.get("veto_reason", "")
    nak = result.get("nakshatra", "")

    sig_color_map = {"LONG": "#00cc66", "SHORT": "#ff4444", "NEUTRAL": "#888888", "HOLD": "#ffaa00"}
    color = sig_color_map.get(sig, "#888888")

    score_pct = int(abs(score) * 100)

    return dbc.Card(
        [
            dbc.CardHeader("🏆 Ensemble Vote"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div(sig, className="fs-3 fw-bold", style={"color": color}),
                        html.Div(f"Score: {score:+.3f}  ·  Confidence: {conf:.0f}%",
                                 className="text-muted"),
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Conviction", className="small"),
                        dbc.Progress(value=score_pct, max=100,
                                     color="success" if score > 0 else "danger" if score < 0 else "secondary",
                                     className="mb-1"),
                        html.Span(f"{score_pct}% directional conviction", className="small"),
                        html.Div(f"🌙 {nak}" if nak else "", className="small text-muted mt-1"),
                    ], width=6),
                ]),
                html.Div(veto, className="text-danger fw-bold") if veto else None,
            ]),
        ],
        className="mb-3 border-2",
        style={"borderColor": color},
    )


def agents_live_tab() -> html.Div:
    """Returns the full '13 Agents Live' tab layout (DCC tabs callback-ready)."""
    panchanga = get_current_panchanga()

    return html.Div([
        dbc.Row([
            dbc.Col([
                ensemble_header_card(None),
                nakshatra_wheel_card(panchanga),
            ], width=4),
            dbc.Col([
                html.H5("13 Agents — Real-time Signals", className="mb-2"),
                html.Div("No agent results yet. Run ./tools/run_13_agents.py to populate.",
                         className="text-muted small", id="agents-live-placeholder"),
                html.Div(id="agents-live-cards"),
            ], width=8),
        ]),
        html.Hr(),
        dbc.Row([
            dbc.Col([
                html.H6("📊 Weight Distribution", className="mb-2"),
                dcc.Graph(
                    id="weight-pie-chart",
                    figure={
                        "data": [{
                            "type": "pie",
                            "labels": ["Fundamental", "Quant", "Macro", "OptionsFlow", "Sentiment",
                                       "Technical", "Bull", "Bear", "Bradley", "Cycle", "Electoral", "Gann"],
                            "values": [20, 20, 15, 15, 10, 10, 5, 5, 3, 5, 3, 3],
                            "hole": 0.4,
                            "marker": {"colors": ["#636efa", "#ef553b", "#00cc96", "#ab63fa",
                                                   "#ffa15a", "#19d3f3", "#ff6692", "#b6e880",
                                                   "#ff97ff", "#fecb52", "#b0e4ff", "#ffccaa"]},
                        }],
                        "layout": {
                            "margin": {"t": 10, "b": 10, "l": 10, "r": 10},
                            "paper_bgcolor": "rgba(0,0,0,0)",
                            "plot_bgcolor": "rgba(0,0,0,0)",
                            "font": {"color": "#aaa"},
                        },
                    },
                    config={"displayModeBar": False},
                    style={"height": 300},
                ),
            ], width=4),
            dbc.Col([
                html.H6("🌙 Nakshatra Risk Heatmap", className="mb-2"),
                dcc.Graph(
                    id="nakshatra-heatmap",
                    figure=_nak_heatmap_figure(),
                    config={"displayModeBar": False},
                    style={"height": 300},
                ),
            ], width=8),
        ]),
    ])


def _nak_heatmap_figure():
    from trading.vedic.nakshatra_risk import NAKSHATRA_RISK
    names = list(NAKSHATRA_RISK.keys())
    values = list(NAKSHATRA_RISK.values())
    colors = [_nak_color(n) for n in names]
    return {
        "data": [{
            "type": "bar",
            "x": names,
            "y": values,
            "marker": {
                "color": colors,
                "line": {"width": 0},
            },
            "text": [f"×{v:.2f}" for v in values],
            "textposition": "outside",
            "textfont": {"color": "#888", "size": 8},
        }],
        "layout": {
            "margin": {"t": 10, "b": 60, "l": 30, "r": 10},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#aaa", "size": 9},
            "xaxis": {"tickangle": -45, "dtick": 1},
            "yaxis": {"title": "Risk ×", "range": [0.5, 1.6]},
            "shapes": [
                {"type": "line", "x0": -0.5, "x1": 27, "y0": 1.0, "y1": 1.0,
                 "line": {"color": "#888", "dash": "dot", "width": 1}},
            ],
        },
    }


def nakshatra_risk_badge(nak_name: str) -> html.Span:
    from trading.vedic.nakshatra_risk import get_nakshatra_multiplier, is_favorable_nakshatra, is_dangerous_nakshatra
    mult = get_nakshatra_multiplier(nak_name)
    if is_favorable_nakshatra(nak_name):
        color = "success"
        icon = "✅"
    elif is_dangerous_nakshatra(nak_name):
        color = "danger"
        icon = "⛔"
    else:
        color = "warning"
        icon = "⚪"
    return html.Span(f"{icon} {nak_name} ×{mult:.2f}", className=f"badge bg-{color}")
