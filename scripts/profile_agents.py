"""Profile Gann, Bradley, Elliot agents to find top-3 bottlenecks (H-01)."""
import cProfile
import pstats
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

AGENTS = ["GannAgent", "BradleyAgent", "ElliotAgent"]
MODULES = {
    "GannAgent": "agents._impl.gann_agent",
    "BradleyAgent": "agents._impl.bradley_agent",
    "ElliotAgent": "agents._impl.elliot_agent",
}

STATE = {"symbol": "BTCUSDT", "current_price": 64290.0, "_price_data": [64200, 64350, 64180]}

def profile_agent(name, module_path, state, runs=100):
    print(f"Profiling {name} ({runs} runs)...")
    mod = __import__(module_path, fromlist=[name])
    cls = getattr(mod, name)

    profiler = cProfile.Profile()
    profiler.enable()
    for _ in range(runs):
        try:
            cls().analyze(state)
        except Exception:
            pass
    profiler.disable()

    out_path = f"docs/performance/profile_{name.lower()}.prof"
    stats = pstats.Stats(profiler).sort_stats("cumtime")
    stats.dump_stats(out_path)
    stats.print_stats(20)
    print(f"  Saved to {out_path}")

if __name__ == "__main__":
    for name in AGENTS:
        profile_agent(name, MODULES[name], STATE)
