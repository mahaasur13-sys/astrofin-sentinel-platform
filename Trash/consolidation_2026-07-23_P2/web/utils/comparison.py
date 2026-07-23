"""web/utils/comparison.py — Multi-strategy comparison utilities (ATOM-META-RL-004)"""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def build_comparison_table(session_records: list[dict]) -> str:
    """Build an HTML comparison table for selected strategies."""
    if not session_records:
        return "<p class='text-muted'>No strategies selected</p>"

    rows = []
    for r in session_records:
        ev = r.get("evaluation", {})
        reward = r.get("reward", 0)
        badge = "bg-success" if reward > 0.7 else "bg-warning" if reward > 0.4 else "bg-secondary"
        rows.append(
            f"<tr><td><code>{r.get('id', '?')[:8]}</code></td>"
            f"<td>{r.get('generation', 0)}</td>"
            f"<td><span class='badge {badge}'>{reward:+.4f}</span></td>"
            f"<td>{ev.get('sharpe', 0):.3f}</td>"
            f"<td>{ev.get('trades', 0)}</td>"
            f"<td>{ev.get('win_rate', 0):.1%}</td>"
            f"<td>{ev.get('max_drawdown', 0):.2%}</td></tr>"
        )

    return f"""<table class="table table-sm table-dark table-hover">
        <thead><tr><th>ID</th><th>Gen</th><th>Reward</th><th>Sharpe</th><th>Trades</th><th>Win%</th><th>MaxDD</th></tr></thead>
        <tbody>{"".join(rows)}</tbody></table>"""


def build_comparison_chart(records_by_session: dict[str, list[dict]]) -> dict:
    """Build a grouped bar chart comparing sessions."""
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Reward by Generation", "Metrics Comparison"),
        horizontal_spacing=0.12,
    )

    colors = ["#00d4ff", "#ffd600", "#00c853", "#ff6d00", "#d500f9"]
    for idx, (sid, records) in enumerate(records_by_session.items()):
        if idx >= 5:
            break
        color = colors[idx % len(colors)]
        label = sid[:16]

        # Left: reward bar
        gens = [r.get("generation", i) for i, r in enumerate(records)]
        rewards = [r.get("reward", 0) for r in records]
        fig.add_trace(
            go.Bar(
                x=gens,
                y=rewards,
                name=f"Reward {label}",
                marker_color=color,
                opacity=0.8,
                legendgroup=label,
            ),
            row=1,
            col=1,
        )

        # Right: metrics radar
        if records:
            best = max(records, key=lambda r: r.get("reward", 0))
            ev = best.get("evaluation", {})
            metrics = [
                ev.get("sharpe", 0) / 5,
                ev.get("win_rate", 0),
                min(ev.get("trades", 1) / 50, 1),
                1 - min(ev.get("max_drawdown", 0), 1),
                (abs(ev.get("risk_adjusted_pnl", 0)) if ev.get("risk_adjusted_pnl", 0) is not None else 0),
            ]
            labels = ["Sharpe", "Win%", "Trades", "Stability", "PnL"]
            fig.add_trace(
                go.Scatterpolar(
                    r=metrics + [metrics[0]],
                    theta=labels + [labels[0]],
                    name=f"Metrics {label}",
                    line_color=color,
                    fill="toself",
                    opacity=0.4,
                    legendgroup=label,
                    showlegend=True,
                ),
                row=1,
                col=2,
            )

    fig.update_layout(
        template="plotly_dark",
        height=300,
        margin={"l": 40, "r": 20, "t": 40, "b": 30},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.25, "xanchor": "center", "x": 0.5},
        barmode="group",
    )
    return fig.to_dict()


def build_convergence_chart(gen_stats: list[dict]) -> dict:
    """Build a convergence line chart (mean + max reward per generation)."""
    if not gen_stats:
        return go.Figure().to_dict()

    gens = [s.get("generation", i) for i, s in enumerate(gen_stats)]
    max_rw = [s.get("max_reward", 0) for s in gen_stats]
    mean_rw = [s.get("mean_reward", 0) for s in gen_stats]
    std_rw = [s.get("std_reward", 0) for s in gen_stats]

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Convergence (Reward)", "Reward Distribution"),
        horizontal_spacing=0.12,
    )

    # Left: convergence lines
    fig.add_trace(
        go.Scatter(
            x=gens,
            y=max_rw,
            mode="lines+markers",
            name="Best",
            line={"color": "#00d4ff", "width": 2},
            marker={"size": 6},
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=gens,
            y=mean_rw,
            mode="lines+markers",
            name="Mean",
            line={"color": "#ffd600", "width": 1.5, "dash": "dot"},
            marker={"size": 5},
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=gens + gens[::-1],
            y=[m + s for m, s in zip(mean_rw, std_rw, strict=False)]
            + [m - s for m, s in zip(mean_rw[::-1], std_rw[::-1], strict=False)],
            fill="toself",
            opacity=0.15,
            fillcolor="#ffd600",
            line={"color": "rgba(0,0,0,0)"},
            name="±1 Std",
            showlegend=True,
        ),
        row=1,
        col=1,
    )

    # Right: reward histogram
    rewards = [s.get("reward", 0) for s in gen_stats]
    fig.add_trace(
        go.Histogram(
            y=rewards,
            name="Rewards",
            marker_color="#00d4ff",
            opacity=0.7,
            nbinsy=15,
            orientation="h",
        ),
        row=1,
        col=2,
    )

    fig.update_layout(
        template="plotly_dark",
        height=250,
        margin={"l": 40, "r": 20, "t": 40, "b": 30},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.2, "xanchor": "center", "x": 0.5},
    )
    return fig.to_dict()
