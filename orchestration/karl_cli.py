"""orchestration/karl_cli.py — ATOM-017: Industrial KARL CLI + Rich UI + Metrics"""

from __future__ import annotations
import asyncio
import sys
import threading
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    RICH = True
except ImportError:
    RICH = False

sys.path.insert(0, str(Path(__file__).parent.parent))
console = Console() if RICH else None


def cprint(msg, style=None):
    if RICH:
        console.print(msg, style=style or "")
    else:
        print(msg)


def print_banner():
    banner = r"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ███████╗██╗   ██╗██████╗ ██████╗  █████╗ ██████╗ ██████╗   ║
║   ██╔════╝██║   ██║██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔══██╗  ║
║   ███████╗██║   ██║██████╔╝██████╔╝███████║██████╔╝██║  ██║  ║
║   ╚════██║██║   ██║██╔═══╝ ██╔══██╗██╔══██║██╔══██╗██║  ██║  ║
║   ███████║╚██████╔╝██║     ██║  ██║██║  ██║██║  ██║██████╔╝  ║
║   ╚══════╝ ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝   ║
║                                                              ║
║   SENTINEL v5 — KARL MODE  ·  ATOM-017  ·  Industrial CLI  ║
╚══════════════════════════════════════════════════════════════╝"""
    cprint(banner, "bold cyan on black")


def print_decision_rich(record, amre, synth):
    if not RICH:
        return print_decision_ascii(record, amre, synth)
    action = record.get("final_action", synth.get("signal", "NEUTRAL"))
    confidence = record.get("confidence_final", synth.get("confidence", 50))
    record.get("regime", "NORMAL")
    record.get("price", 0)
    decision_id = record.get("decision_id", "N/A")
    action_color = {
        "LONG": "green",
        "SHORT": "red",
        "NEUTRAL": "yellow",
        "AVOID": "bold red",
    }.get(action, "white")
    action_icon = {"LONG": "📈", "SHORT": "📉", "NEUTRAL": "⏸", "AVOID": "🚫"}.get(action, "❓")
    main = Text()
    main.append(f"  {action_icon} ACTION  ", style=f"bold {action_color}")
    main.append(f"  CONF={confidence:3}  ", style="bold white")
    main.append(f"  ID={decision_id}", style="dim")
    try:
        console.print(
            Panel(
                main,
                title="[bold]KARL DECISION[/bold]",
                border_style="cyan",
                expand=False,
            )
        )
    except Exception as e:
        print(f"[WARN] {e}")


def print_decision_ascii(record, amre, synth):
    action = record.get("final_action", synth.get("signal", "NEUTRAL"))
    confidence = record.get("confidence_final", synth.get("confidence", 50))
    decision_id = record.get("decision_id", "N/A")
    icon = {
        "LONG": "+LONG",
        "SHORT": "-SHORT",
        "NEUTRAL": "=NEUT",
        "AVOID": "!AVOID",
    }.get(action, " ? ")
    print(f"{icon}  CONF={confidence}  ID={decision_id}")


def save_decision_jsonl(record, filepath="data/karl_decisions.jsonl"):
    if not record:
        return
    from core.safe_json import safe_jsonl_append

    safe_jsonl_append(record, filepath)


def generate_html_report(result, output_path="data/karl_report.html"):
    # (сокращённая версия для краткости, полная доступна в репозитории)
    synth = result.get("final_recommendation", {})
    action = synth.get("signal", "NEUTRAL")
    confidence = synth.get("confidence", 50)
    html = f"""<!DOCTYPE html><html><head><meta charset=utf-8><title>KARL Report</title></head>
<body><h1>Signal: {action}</h1><p>Confidence: {confidence}</p></body></html>"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)
    return output_path


def print_topology_viz(topology_dict=None, session_id=None):
    print("[INFO] Topology visualization placeholder")


async def visualize_current_topology(session_id=None):
    print("[INFO] Topology visualization placeholder")


# ── CLI (Click) ─────────────────────────────────────────────────
import click


@click.group()
def cli():
    """AstroFin Sentinel V5 — KARL CLI"""
    pass


@cli.command()
@click.argument("query", default="Analyze BTC")
@click.option("--symbol", default="BTCUSDT")
@click.option("--timeframe", default="SWING")
@click.option("--with-metrics", is_flag=True, help="Start Prometheus /metrics server on port 9091")
def analyze(query, symbol, timeframe, with_metrics):
    """Run a trading analysis"""
    if with_metrics:
        from tools.metrics_server import run_server

        t = threading.Thread(target=run_server, kwargs={"port": 9091, "host": "0.0.0.0"}, daemon=True)
        t.start()
        click.echo("Metrics server started on 0.0.0.0:9091")

    from orchestration.sentinel_v5 import run_sentinel_v5

    result = asyncio.run(run_sentinel_v5(query, symbol, timeframe))
    record = result.get("decision_record", {})
    amre = result.get("amre_state", {})
    synth = result.get("final_recommendation", {})
    print_decision_rich(record, amre, synth)


@cli.group()
def metrics():
    """Prometheus /metrics server commands."""
    pass


@metrics.command()
@click.option("--port", default=9091, help="Port for /metrics server (default: 9091)")
@click.option("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
def serve(port, host):
    """Start standalone Prometheus /metrics server."""
    from tools.metrics_server import run_server

    click.echo(f"Starting metrics server on {host}:{port}")
    run_server(port=port, host=host)


def main():
    cli()


if __name__ == "__main__":
    main()
