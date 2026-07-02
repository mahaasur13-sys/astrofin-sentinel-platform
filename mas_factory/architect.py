"""mas_factory/architect.py - MASFactoryArchitect: builds topology from intention"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from mas_factory.registry import get_registry
from mas_factory.topology import (
    Adapter,
    Connection,
    Role,
    SwitchNode,
    SwitchStrategy,
    Topology,
)

# Intent keywords → required capabilities
INTENT_PATTERNS = {
    "fundamental": ["fundamental_analysis", "valuation", "financial_metrics"],
    "technical": ["price_action", "chart_patterns", "indicators"],
    "macro": ["economic_indicators", "fed_policy", "geopolitics"],
    "options": ["options_flow", "gamma_exposure", "unusual_activity"],
    "sentiment": ["social_sentiment", "news_analysis", "fear_greed"],
    "astro": ["planetary_positions", "aspects", "nakshatra", "choghadiya"],
    "quant": ["ml_predictions", "backtesting", "volatility_model"],
    "electional": ["muhurta_timing", "entry_windows"],
}

SYMBOL_CONTEXT = {
    "crypto": ["BTC", "ETH", "SOL"],
    "defi": ["UNI", "AAVE", "MKR"],
    "tech": ["AAPL", "GOOGL", "MSFT"],
}

REGIME_TEMPLATES = {
    "INTRADAY": {"max_depth": 3, "timeout_ms": 10000},
    "SWING": {"max_depth": 5, "timeout_ms": 30000},
    "POSITIONAL": {"max_depth": 8, "timeout_ms": 60000},
}


@dataclass
class Intention:
    """Parsed user intention"""

    raw: str
    intent_type: str  # "analyze" | "compare" | "predict" | "backtest"
    symbol: str
    timeframe: str
    keywords: list[str]
    complexity: str  # "simple" | "moderate" | "complex"
    required_capabilities: set[str]
    constraints: dict[str, Any]
    confidence_floor: int = 65
    max_agents: int = 8

    def compute_hash(self) -> str:
        data = json.dumps(
            {
                "raw": self.raw,
                "symbol": self.symbol,
                "timeframe": self.timeframe,
                "keywords": sorted(self.required_capabilities),
            },
            sort_keys=True,
        )
        return hashlib.sha256(data.encode()).hexdigest()[:12]


class MASFactoryArchitect:
    """
    MASFactory Architect - generates declarative topology.json from high-level intention.

    This is the CORE of the transition from SkillMD to MAS Factory.
    Instead of hard-coded if/else in sentinel_v5.py, we now:
        1. Parse intention → extract capabilities
        2. Select roles by capability matching
        3. Build connections based on data flow
        4. Insert switch nodes for conditional routing
        5. Return Topology blueprint

    The TopologyExecutor then runs agents dynamically from this blueprint.
    """

    def __init__(self):
        self.registry = get_registry()
        self._topology_cache: dict[str, Topology] = {}

    def build(
        self,
        intention: str,
        symbol: str = "BTCUSDT",
        timeframe: str = "SWING",
        **kwargs,
    ) -> Topology:
        """
        Main entry point. Build declarative topology from intention.

        Args:
            intention: Natural language query (e.g., "Analyze BTC for swing trade")
            symbol: Trading symbol
            timeframe: INTRADAY | SWING | POSITIONAL
            **kwargs: Additional constraints (confidence_floor, max_agents, etc.)

        Returns:
            Topology: Declarative blueprint with roles, connections, switch nodes
        """
        # Step 1: Parse intention
        parsed = self._parse_intention(intention, symbol, timeframe, **kwargs)

        # Step 2: Check cache
        cache_key = f"{parsed.compute_hash()}_{timeframe}"
        if cache_key in self._topology_cache:
            cached = self._topology_cache[cache_key]
            # Extend metadata with new timestamp
            cached.metadata["cached"] = False
            cached.metadata["reused_at"] = datetime.now().isoformat()
            return cached

        # Step 3: Select roles by capability matching
        roles = self._select_roles(parsed)

        # Step 4: Build connections based on data flow
        connections = self._build_connections(roles, parsed)

        # Step 5: Insert switch nodes
        switch_nodes = self._build_switch_nodes(roles, parsed)

        # Step 6: Create topology
        topology = Topology(
            intention=intention,
            symbol=symbol,
            timeframe=timeframe,
            version="1.0",
            roles=roles,
            connections=connections,
            switch_nodes=switch_nodes,
            entry_point="router",
            exit_point="synthesis",
            metadata={
                "parsed_intention": parsed.raw,
                "complexity": parsed.complexity,
                "required_capabilities": list(parsed.required_capabilities),
                "confidence_floor": parsed.confidence_floor,
                "created_at": datetime.now().isoformat(),
            },
        )

        # Step 7: Validate
        errors = topology.validate()
        if errors:
            raise ValueError(f"Topology validation failed: {errors}")

        # Cache it
        self._topology_cache[cache_key] = topology

        return topology

    def _parse_intention(self, intention: str, symbol: str, timeframe: str, **kwargs) -> Intention:
        """Parse natural language into structured Intention"""
        lower = intention.lower()
        keywords = []
        required_capabilities: set[str] = set()

        # Detect intent type
        if any(w in lower for w in ["analyze", "analysis", "look at"]):
            intent_type = "analyze"
        elif any(w in lower for w in ["compare", "vs", "versus"]):
            intent_type = "compare"
        elif any(w in lower for w in ["predict", "forecast", "will"]):
            intent_type = "predict"
        elif any(w in lower for w in ["backtest", "test", "historical"]):
            intent_type = "backtest"
        else:
            intent_type = "analyze"

        # Detect keywords and map to capabilities
        for keyword, caps in INTENT_PATTERNS.items():
            if keyword in lower:
                keywords.append(keyword)
                required_capabilities.update(caps)

        # If no keywords detected, add defaults based on timeframe
        if not keywords:
            if timeframe == "INTRADAY":
                required_capabilities.update(["technical_analysis", "price_action"])
            elif timeframe == "SWING":
                required_capabilities.update(["fundamental_analysis", "technical_analysis", "astro_timing"])
            else:
                required_capabilities.update(["fundamental_analysis", "macro_analysis", "sentiment"])

        # Determine complexity
        complexity = (
            "simple"
            if len(required_capabilities) <= 3
            else "moderate"
            if len(required_capabilities) <= 5
            else "complex"
        )

        # Constraints
        constraints = {
            "confidence_floor": kwargs.get("confidence_floor", 65),
            "max_agents": kwargs.get("max_agents", 8),
            "allow_astro": "astro" not in kwargs.get("exclude", []),
            "allow_electional": kwargs.get("include_electional", False),
        }

        return Intention(
            raw=intention,
            intent_type=intent_type,
            symbol=symbol,
            timeframe=timeframe,
            keywords=keywords,
            complexity=complexity,
            required_capabilities=required_capabilities,
            constraints=constraints,
            confidence_floor=constraints["confidence_floor"],
            max_agents=constraints["max_agents"],
        )

    def _select_roles(self, intention: Intention) -> list[Role]:
        """Select roles based on required capabilities"""
        all_roles = self.registry.get_all_roles()
        selected = []

        for role in all_roles:
            # Check if role capabilities match required
            role_caps = set(role.capabilities)
            match_score = len(intention.required_capabilities & role_caps)

            if match_score > 0:
                # Adjust weight based on match
                adjusted_weight = role.weight * (match_score / max(len(role_caps), 1))
                role.weight = max(0.05, adjusted_weight)
                selected.append(role)

        # Sort by weight descending and limit
        selected.sort(key=lambda r: r.weight, reverse=True)
        selected = selected[: intention.max_agents]

        # Ensure we have at least a synthesis role
        role_names = {r.name for r in selected}
        if "synthesis" not in role_names:
            selected.append(
                Role(
                    name="synthesis",
                    agent_type="SynthesisAgent",
                    weight=0.0,  # Coordinator, no vote
                    capabilities=["synthesis", "final_recommendation"],
                    inputs=["signals"],
                    outputs=["final_signal"],
                )
            )

        return selected

    def _build_connections(self, roles: list[Role], intention: Intention) -> list[Connection]:
        """Build data flow connections between roles"""
        connections = []

        # Input → Router
        connections.append(
            Connection(
                from_node="input",
                to_node="router",
                adapter=Adapter("input", "router", "passthrough"),
            )
        )

        # Router → First tier (capability-matched agents)
        capability_order = list(intention.required_capabilities)[:4]

        prev = "router"
        for i, cap in enumerate(capability_order):
            # Find matching role
            role = next((r for r in roles if cap in r.capabilities), None)
            if role:
                connections.append(
                    Connection(
                        from_node=prev,
                        to_node=role.name,
                        adapter=Adapter(prev, role.name, "passthrough"),
                    )
                )
                prev = role.name

        # Last agent → Synthesis
        connections.append(
            Connection(
                from_node=prev,
                to_node="synthesis",
                adapter=Adapter(prev, "synthesis", "extract_signal"),
            )
        )

        # Synthesis → End
        connections.append(
            Connection(
                from_node="synthesis",
                to_node="end",
                adapter=Adapter("synthesis", "end", "passthrough"),
            )
        )

        return connections

    def _build_switch_nodes(self, roles: list[Role], intention: Intention) -> list[SwitchNode]:
        """Build conditional routing nodes"""
        switch_nodes = []

        # Thompson router
        switch_nodes.append(
            SwitchNode(
                id="router",
                strategy=SwitchStrategy.THOMPSON,
                candidates=[r.name for r in roles if r.name != "synthesis"],
                k=min(4, len(roles) - 1),
                weights={r.name: r.weight for r in roles if r.name != "synthesis"},
            )
        )

        return switch_nodes

    def get_cached_topology(self, intention_hash: str) -> Topology | None:
        """Retrieve cached topology by hash"""
        for cached in self._topology_cache.values():
            if cached.compute_hash() == intention_hash:
                return cached
        return None

    def clear_cache(self):
        """Clear topology cache"""
        self._topology_cache.clear()


# Singleton
_ARCHITECT: MASFactoryArchitect | None = None


def get_architect() -> MASFactoryArchitect:
    global _ARCHITECT
    if _ARCHITECT is None:
        _ARCHITECT = MASFactoryArchitect()
    return _ARCHITECT
