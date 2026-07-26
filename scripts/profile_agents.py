#!/usr/bin/env python3
"""H-01: Profile Astro agents — top-3 performance bottlenecks.

Usage:
    python scripts/profile_agents.py              # profile all 3 agents
    python scripts/profile_agents.py --agent Gann  # single agent
    python scripts/profile_agents.py --runs 500    # more iterations
"""

from __future__ import annotations

import argparse
import cProfile
import pstats
import os
import sys
import io
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUTPUT_DIR = Path("docs/performance")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_STATE = {
    "symbol": "BTCUSDT",
    "current_price": 64290.0,
    "_price_data": [
        [1745971200000, 63900.0, 64500.0, 63800.0, 64100.0, 12000],
    ] * 90,
}


def profile_agent(name: str, agent_cls, runs: int = 100):
    """Profile a single agent over N analyze() calls."""
    print(f"\n{'='*60}")
    print(f"  PROFILING: {name} ({runs} calls)")
    print(f"{'='*60}")

    agent = agent_cls()
    state = DEFAULT_STATE.copy()

    profiler = cProfile.Profile()
    profiler.enable()
    for _ in range(runs):
        agent.analyze(state)
    profiler.disable()

    out = io.StringIO()
    stats = pstats.Stats(profiler, stream=out).sort_stats("cumtime")
    stats.print_stats(20)

    prof_path = OUTPUT_DIR / f"profile_{name.lower()}.prof"
    stats.dump_stats(str(prof_path))

    print(out.getvalue())
    print(f"  → Profile saved: {prof_path}")
    return prof_path


def main():
    parser = argparse.ArgumentParser(description="Profile AstroFin agents")
    parser.add_argument("--agent", choices=["Gann", "Bradley", "Elliot", "all"], default="all")
    parser.add_argument("--runs", type=int, default=100, help="Number of analyze() calls")
    args = parser.parse_args()

    agents = []
    if args.agent == "all":
        agents = [
            ("Gann", "agents._impl.gann_agent", "GannAgent"),
            ("Bradley", "agents._impl.bradley_agent", "BradleyAgent"),
            ("Elliot", "agents._impl.elliot_agent", "ElliotAgent"),
        ]
    else:
        mapping = {
            "Gann": ("Gann", "agents._impl.gann_agent", "GannAgent"),
            "Bradley": ("Bradley", "agents._impl.bradley_agent", "BradleyAgent"),
            "Elliot": ("Elliot", "agents._impl.elliot_agent", "ElliotAgent"),
        }
        agents = [mapping[args.agent]]

    results = {}
    for name, mod_path, class_name in agents:
        import importlib
        mod = importlib.import_module(mod_path)
        cls = getattr(mod, class_name)
        prof_path = profile_agent(name, cls, runs=args.runs)
        results[name] = prof_path

    print(f"\n{'='*60}")
    print(f"  All profiles saved to {OUTPUT_DIR}/")
    for name, path in results.items():
        print(f"    {name}: {path}")
    print(f"{'='*60}")
    print(f"\nTo analyze: python -m pstats {list(results.values())[0]}")
    print(f"  sort cumtime")
    print(f"  stats 20")


if __name__ == "__main__":
    main()
