"""agents/gitagent_registry.py — ATOM-GITAGENT-004/005: Agent Registry + Output Adapter
Registry: централизованный доступ ко всем агентам.
Output Adapter: единый нормализатор после registry.run().
"""

from __future__ import annotations

import asyncio
import builtins
import logging
from typing import Any

from integrations.gitagent.adapters.output_adapter import (
    NormalizedOutput,
    UnifiedOutputAdapter,
    compute_weighted_signal,
)

logger = logging.getLogger("registry")

# ─── Agent Registry ────────────────────────────────────────────────────────────

# All agents with metadata
AGENT_AGENTS: dict[str, dict] = {
    # Astro Domain
    "AstroCouncil": {
        "name": "AstroCouncil",
        "domain": "astro",
        "weight": 0.20,
        "karl": True,
        "ttc": True,
        "selfq": True,
        "path": "agents._impl.astro_council",
        "method": "run_astro_council",
    },
    "BradleyAgent": {
        "name": "BradleyAgent",
        "domain": "astro",
        "weight": 0.03,
        "karl": True,
        "ttc": True,
        "selfq": True,
        "path": "agents._impl.bradley_agent",
        "method": "run_bradley_agent",
    },
    "GannAgent": {
        "name": "GannAgent",
        "domain": "astro",
        "weight": 0.03,
        "karl": True,
        "ttc": True,
        "selfq": True,
        "path": "agents._impl.gann_agent",
        "method": "run_gann_agent",
    },
    "CycleAgent": {
        "name": "CycleAgent",
        "domain": "astro",
        "weight": 0.05,
        "karl": True,
        "ttc": True,
        "selfq": True,
        "path": "agents._impl.cycle_agent",
        "method": "run_cycle_agent",
    },
    "ElectoralAgent": {
        "name": "ElectoralAgent",
        "domain": "astro",
        "weight": 0.03,
        "karl": True,
        "ttc": False,
        "selfq": False,
        "path": "agents._impl.electoral_agent",
        "method": "run_electoral_agent",
    },
    "TimeWindowAgent": {
        "name": "TimeWindowAgent",
        "domain": "astro",
        "weight": 0.02,
        "karl": True,
        "ttc": True,
        "selfq": True,
        "path": "agents._impl.time_window_agent",
        "method": "run_time_window_agent",
    },
    # Hybrid Agents
    "FundamentalAgent": {
        "name": "FundamentalAgent",
        "domain": "fundamental",
        "weight": 0.20,
        "karl": True,
        "ttc": True,
        "selfq": True,
        "path": "agents._impl.fundamental_agent",
        "method": "run_fundamental_agent",
    },
    "MacroAgent": {
        "name": "MacroAgent",
        "domain": "macro",
        "weight": 0.15,
        "karl": True,
        "ttc": True,
        "selfq": True,
        "path": "agents._impl.macro_agent",
        "method": "run_macro_agent",
    },
    "QuantAgent": {
        "name": "QuantAgent",
        "domain": "quant",
        "weight": 0.20,
        "karl": True,
        "ttc": True,
        "selfq": True,
        "path": "agents._impl.quant_agent",
        "method": "run_quant_agent",
    },
    "OptionsFlowAgent": {
        "name": "OptionsFlowAgent",
        "domain": "options",
        "weight": 0.15,
        "karl": True,
        "ttc": True,
        "selfq": True,
        "path": "agents._impl.options_flow_agent",
        "method": "run_options_flow_agent",
    },
    "SentimentAgent": {
        "name": "SentimentAgent",
        "domain": "sentiment",
        "weight": 0.10,
        "karl": True,
        "ttc": True,
        "selfq": True,
        "path": "agents._impl.sentiment_agent",
        "method": "run_sentiment_agent",
    },
    "TechnicalAgent": {
        "name": "TechnicalAgent",
        "domain": "technical",
        "weight": 0.10,
        "karl": True,
        "ttc": True,
        "selfq": True,
        "path": "agents._impl.technical_agent",
        "method": "run_technical_agent",
    },
    "BullResearcher": {
        "name": "BullResearcher",
        "domain": "research",
        "weight": 0.05,
        "karl": True,
        "ttc": True,
        "selfq": True,
        "path": "agents._impl.bull_researcher",
        "method": "run_bull_researcher",
    },
    "BearResearcher": {
        "name": "BearResearcher",
        "domain": "research",
        "weight": 0.05,
        "karl": True,
        "ttc": True,
        "selfq": True,
        "path": "agents._impl.bear_researcher",
        "method": "run_bear_researcher",
    },
    "MLPredictorAgent": {
        "name": "MLPredictorAgent",
        "domain": "quant",
        "weight": 0.08,
        "karl": True,
        "ttc": True,
        "selfq": True,
        "path": "agents._impl.ml_predictor_agent",
        "method": "run_ml_predictor_agent",
    },
    "MarketAnalyst": {
        "name": "MarketAnalyst",
        "domain": "technical",
        "weight": 0.05,
        "karl": True,
        "ttc": True,
        "selfq": True,
        "path": "agents._impl.market_analyst",
        "method": "run_market_analyst",
    },
    "InsiderAgent": {
        "name": "InsiderAgent",
        "domain": "fundamental",
        "weight": 0.05,
        "karl": True,
        "ttc": False,
        "selfq": False,
        "path": "agents._impl.insider_agent",
        "method": "run_insider_agent",
    },
    "ElliotAgent": {
        "name": "ElliotAgent",
        "domain": "technical",
        "weight": 0.05,
        "karl": True,
        "ttc": True,
        "selfq": True,
        "path": "agents._impl.elliot_agent",
        "method": "run_elliot_agent",
    },
    "RiskAgent": {
        "name": "RiskAgent",
        "domain": "risk",
        "weight": 0.00,
        "karl": True,
        "ttc": False,
        "selfq": False,
        "path": "agents._impl.risk_agent",
        "method": "run_risk_agent",
    },
    # Synthesis
    "SynthesisAgent": {
        "name": "SynthesisAgent",
        "domain": "synthesis",
        "weight": 0.00,
        "karl": True,
        "ttc": True,
        "selfq": False,
        "path": "agents._impl.synthesis_agent",
        "method": "run_synthesis_agent",
    },
    "CompromiseAgent": {
        "name": "CompromiseAgent",
        "domain": "synthesis",
        "weight": 0.00,
        "karl": False,
        "ttc": False,
        "selfq": False,
        "path": "agents._impl.compromise_agent",
        "method": "run_compromise_agent",
    },
}

# Domain weights for hybrid scoring
DOMAIN_WEIGHTS = {
    "fundamental": 0.20,
    "quant": 0.20,
    "macro": 0.15,
    "options": 0.15,
    "sentiment": 0.10,
    "technical": 0.10,
    "astro": 0.10,
    "research": 0.05,
    "risk": 0.00,
}

# TTC agents
TTC_AGENTS = {name for name, info in AGENT_AGENTS.items() if info.get("ttc", False)}

# KARL agents
KARL_AGENTS = {name for name, info in AGENT_AGENTS.items() if info.get("karl", False)}

# ─── Agent Registry Class ──────────────────────────────────────────────────────


class GitAgentRegistry:
    """
    Unified registry for all AstroFin agents.
    Provides run(), run_ttc(), validate() with output adapter normalization.
    """

    def __init__(self):
        self.output_adapter = UnifiedOutputAdapter()
        self._cache = {}

    def list(
        self,
        domain: str | None = None,
        karl_only: bool = False,
        ttc_only: bool = False,
    ) -> list[str]:
        """List agents, optionally filtered."""
        agents = list(AGENT_AGENTS.keys())

        if domain:
            agents = [a for a in agents if AGENT_AGENTS[a]["domain"] == domain]
        if karl_only:
            agents = [a for a in agents if a in KARL_AGENTS]
        if ttc_only:
            agents = [a for a in agents if a in TTC_AGENTS]

        return sorted(agents)

    def get_info(self, agent_name: str) -> dict | None:
        return AGENT_AGENTS.get(agent_name)

    def validate(self, agent_name: str) -> tuple[bool, str]:
        """Validate agent is properly configured."""
        info = AGENT_AGENTS.get(agent_name)
        if not info:
            return False, f"Agent '{agent_name}' not found in registry"
        if not info.get("path"):
            return False, f"No path defined for {agent_name}"
        return True, "OK"

    async def run(self, agent_name: str, input_state: dict[str, Any], use_ttc: bool = False) -> NormalizedOutput:
        """
        Run agent with unified output normalization.
        Automatically handles TTC fallback for non-TTC agents.
        """
        info = self.get_info(agent_name)
        if not info:
            return NormalizedOutput(
                signal="NEUTRAL",
                confidence=50,
                reasoning=f"Agent {agent_name} not found",
                metadata={},
                agent_name=agent_name,
                raw_output={},
            )

        # TTC decision
        supports_ttc = info.get("ttc", False)

        if use_ttc and not supports_ttc:
            # TTC fallback: single-pass execution
            logger.debug(f"[Registry] {agent_name} doesn't support TTC, using single-pass")
            raw_output = await self._single_pass(agent_name, input_state)
        elif use_ttc and supports_ttc:
            # Full TTC execution
            raw_output = await self._ttc_pass(agent_name, input_state)
        else:
            raw_output = await self._single_pass(agent_name, input_state)

        # ALWAYS normalize via output adapter
        return self.output_adapter.adapt(raw_output, agent_name, info)

    async def _single_pass(self, agent_name: str, input_state: dict) -> dict[str, Any]:
        """Single-pass agent execution."""
        try:
            import importlib

            info = self.get_info(agent_name)
            module = importlib.import_module(info["path"])

            method_name = info["method"]
            method = getattr(module, method_name, None)

            if method is None:
                # Try class instantiation
                cls = getattr(module, method_name, None)
                if cls:
                    instance = cls()
                    if hasattr(instance, "run"):
                        result = await instance.run(input_state)
                        return result.to_dict() if hasattr(result, "to_dict") else result
                return {
                    "signal": "NEUTRAL",
                    "confidence": 50,
                    "reasoning": f"Method {method_name} not found",
                    "metadata": {},
                }

            # Direct function call
            if asyncio.iscoroutinefunction(method):
                result = await method(input_state)
            else:
                result = method(input_state)

            return result.to_dict() if hasattr(result, "to_dict") else result

        except ImportError:
            return {
                "signal": "NEUTRAL",
                "confidence": 50,
                "reasoning": f"Module {agent_name} not importable",
                "metadata": {"error": "import"},
            }
        except Exception as e:  # noqa: BLE001
            return {
                "signal": "NEUTRAL",
                "confidence": 50,
                "reasoning": f"Execution error: {e}",
                "metadata": {"error": str(e)},
            }

    async def _ttc_pass(self, agent_name: str, input_state: dict, k: int = 5) -> dict[str, Any]:
        """
        Multi-trajectory TTC execution.
        Returns aggregated result across k trajectories.
        """
        info = self.get_info(agent_name)

        # Generate k trajectories
        trajectories = []
        confidences = []

        for seed in range(k):
            # Add seed to state for deterministic variation
            state = {**input_state, "_ttc_seed": seed, "_ttc_k": k}
            try:
                traj = await self._single_pass(agent_name, state)
                out = self.output_adapter.adapt(traj, agent_name, info)
                trajectories.append(out.to_dict())
                confidences.append(out.confidence)
            except Exception:  # noqa: BLE001
                pass

        if not trajectories:
            return {
                "signal": "NEUTRAL",
                "confidence": 50,
                "reasoning": "TTC failed",
                "metadata": {},
            }

        # Aggregate: mean confidence + majority signal
        avg_conf = sum(confidences) / len(confidences)

        signals = [t["signal"] for t in trajectories]
        from collections import Counter

        most_common = Counter(signals).most_common(1)[0][0]

        return {
            "signal": most_common,
            "confidence": int(round(avg_conf)),
            "reasoning": f"TTC k={len(trajectories)} trajectories aggregated",
            "metadata": {
                "ttc": True,
                "k": k,
                "trajectories": len(trajectories),
                "signals": signals,
                "confidences": confidences,
            },
        }

    async def run_all(
        self,
        input_state: dict[str, Any],
        domain_filter: str | None = None,
        use_ttc: bool = False,
    ) -> builtins.list[NormalizedOutput]:
        """Run all (or filtered) agents and normalize outputs."""
        agents = self.list(domain=domain_filter)
        tasks = [self.run(a, input_state, use_ttc=use_ttc) for a in agents]
        return await asyncio.gather(*tasks)

    def weighted_consensus(self, outputs: builtins.list[NormalizedOutput]) -> dict[str, Any]:
        """Compute domain-weighted consensus signal."""
        weights = [self.get_info(o.agent_name).get("weight", 0.05) for o in outputs]
        return compute_weighted_signal(outputs, weights)


# ─── Convenience Functions ──────────────────────────────────────────────────────

_registry: GitAgentRegistry | None = None


def get_registry() -> GitAgentRegistry:
    global _registry
    if _registry is None:
        _registry = GitAgentRegistry()
    return _registry


def list_agents(**kwargs) -> list[str]:
    return get_registry().list(**kwargs)


def get_agent_info(name: str) -> dict | None:
    return AGENT_AGENTS.get(name)


def validate_agent(name: str) -> tuple[bool, str]:
    return get_registry().validate(name)


# ─── CLI ──────────────────────────────────────────────────────────────────────


def main():
    import argparse

    parser = argparse.ArgumentParser(description="GitAgent Registry CLI")
    sub = parser.add_subparsers(dest="cmd")

    list_cmd = sub.add_parser("list", help="List agents")
    list_cmd.add_argument("--domain")
    list_cmd.add_argument("--karl-only", action="store_true")
    list_cmd.add_argument("--ttc-only", action="store_true")

    validate_cmd = sub.add_parser("validate", help="Validate agent")
    validate_cmd.add_argument("name")

    run_cmd = sub.add_parser("run", help="Run agent")
    run_cmd.add_argument("name")
    run_cmd.add_argument("--symbol", default="BTCUSDT")
    run_cmd.add_argument("--price", type=float, default=67000.0)
    run_cmd.add_argument("--ttc", action="store_true")

    args = parser.parse_args()

    if args.cmd == "list":
        agents = list_agents(
            domain=args.domain,
            karl_only=args.karl_only,
            ttc_only=args.ttc_only,
        )
        fmt = "{:<25} {:<12} {:>6} {:>6} {:>6} {:>6}"
        print(fmt.format("Name", "Domain", "Wt%", "KARL", "TTC", "SelfQ"))
        print("-" * 65)
        for name in agents:
            info = get_agent_info(name)
            print(
                fmt.format(
                    name,
                    info["domain"],
                    f"{info['weight'] * 100:.0f}%",
                    "✅" if info.get("karl") else "❌",
                    "✅" if info.get("ttc") else "❌",
                    "✅" if info.get("selfq") else "❌",
                )
            )
        print(f"\nTotal: {len(agents)} agents")

    elif args.cmd == "validate":
        ok, msg = validate_agent(args.name)
        print(f"{'✅' if ok else '❌'} {args.name}: {msg}")

    elif args.cmd == "run":
        import asyncio

        async def do_run():
            reg = get_registry()
            state = {
                "symbol": args.symbol,
                "current_price": args.price,
                "timeframe": "SWING",
                "regime": "NORMAL",
            }
            out = await reg.run(args.name, state, use_ttc=args.ttc)
            print(f"Signal:    {out.signal}")
            print(f"Confidence: {out.confidence}")
            print(f"Reasoning: {out.reasoning[:200]}")
            print(f"Metadata:  {out.metadata}")

        asyncio.run(do_run())

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
