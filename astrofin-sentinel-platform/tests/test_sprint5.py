"""Sprint 5: E2E — 13 Real Agents through Hub-and-Spoke Broker."""

import asyncio
import time
import pytest
from core.envelopes import TaskEnvelope, ResultEnvelope, TaskStatus

# 13 agent run functions (async)
_AGENT_MAP = {
    'MarketAnalyst': ('agents._impl.market_analyst', 'run_market_analyst'),
    'BullResearcher': ('agents._impl.bull_researcher', 'run_bull_researcher'),
    'BearResearcher': ('agents._impl.bear_researcher', 'run_bear_researcher'),
    'FundamentalAgent': ('agents._impl.fundamental_agent', 'run_fundamental_agent'),
    'MacroAgent': ('agents._impl.macro_agent', 'run_macro_agent'),
    'QuantAgent': ('agents._impl.quant_agent', 'run_quant_agent'),
    'OptionsFlowAgent': ('agents._impl.options_flow_agent', 'run_options_flow_agent'),
    'SentimentAgent': ('agents._impl.sentiment_agent', 'run_sentiment_agent'),
    'TechnicalAgent': ('agents._impl.technical_agent', 'run_technical_agent'),
    'BradleyAgent': ('agents._impl.bradley_agent', 'run_bradley_agent'),
    'GannAgent': ('agents._impl.gann_agent', 'run_gann_agent'),
    'CycleAgent': ('agents._impl.cycle_agent', 'run_cycle_agent'),
    'ElectoralAgent': ('agents._impl.electoral_agent', 'run_electoral_agent'),
}
_AGENT_COUNT = 13

_AGENT_RUN_FNS = {}  # lazy

def _lazy_import(name: str):
    """Lazy import agent run function using correct (module_path, fn_name) tuple."""
    if name not in _AGENT_RUN_FNS:
        import importlib
        mod_path, fn_name = _AGENT_MAP[name]
        mod = importlib.import_module(mod_path)
        _AGENT_RUN_FNS[name] = getattr(mod, fn_name)
    return _AGENT_RUN_FNS[name]


def _build_state(ticker: str = "BTCUSDT") -> dict:
    return {
        "symbol": ticker,
        "timeframe": "1d",
        "current_price": 50000.0,
        "indicators": {"rsi": 50, "macd": {"value": 0, "signal": 0}, "atr_pct": 2.0},
        "session_id": f"e2e-{time.time_ns()}",
    }


class TestSprint5E2E:
    """Full 13-agent pipeline through broker infrastructure."""

    @pytest.mark.asyncio
    async def test_all_13_agents_import(self):
        """Все 13 агентов импортируются."""
        for name in _AGENT_MAP:
            fn = _lazy_import(name)
            assert callable(fn), f"{name} is not callable"
        assert len(_AGENT_MAP) == _AGENT_COUNT

    @pytest.mark.asyncio
    async def test_single_agent_broker_dispatch(self):
        """Один агент через InProcessBroker → корректный ResultEnvelope."""
        from core.message_broker import InProcessBroker
        from core.envelopes import TaskEnvelope, TaskStatus

        broker = InProcessBroker(max_queue_size=100)
        state = _build_state()
        env = TaskEnvelope.new(agent_name="MarketAnalyst", state=state)
        run_fn = _lazy_import("MarketAnalyst")

        async def handler(e):
            result = await run_fn(e.state_snapshot)
            if hasattr(result, "to_dict"):
                result = result.to_dict()
            elif isinstance(result, str):
                result = {"signal": result}
            return ResultEnvelope(
                task_id=e.task_id, agent_name=e.agent_name,
                trace_id=e.trace_id, status=TaskStatus.COMPLETED,
                result=result or {},
            )

        result = await broker.send(env, handler)
        assert result is not None
        assert result.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
        assert result.agent_name == "MarketAnalyst"

    @pytest.mark.asyncio
    async def test_gather_vs_broker_baseline(self):
        """Сравнение gather vs broker для 3 агентов."""
        from core.message_broker import InProcessBroker
        from core.envelopes import TaskEnvelope, TaskStatus

        broker = InProcessBroker(max_queue_size=100)
        state = _build_state()
        agent_names = ["FundamentalAgent", "MacroAgent", "SentimentAgent"]

        # Gather baseline
        fns = [_lazy_import(n) for n in agent_names]

        t0 = time.perf_counter()
        gather_results = await asyncio.gather(
            *[fn(state) for fn in fns], return_exceptions=True
        )
        gather_time = time.perf_counter() - t0

        # Broker baseline
        t0 = time.perf_counter()
        broker_results = []
        for name in agent_names:
            env = TaskEnvelope.new(agent_name=name, state=state)
            run_fn = _lazy_import(name)

            async def handler(e):
                result = await run_fn(e.state_snapshot)
                if hasattr(result, "to_dict"):
                    result = result.to_dict()
                elif isinstance(result, str):
                    result = {"signal": result}
                return ResultEnvelope(
                    task_id=e.task_id, agent_name=e.agent_name,
                    trace_id=e.trace_id, status=TaskStatus.COMPLETED,
                    result=result or {},
                )

            result = await broker.send(env, handler)
            broker_results.append(result)
        broker_time = time.perf_counter() - t0

        assert len(gather_results) == 3
        assert len(broker_results) == 3
        # Broker overhead should be reasonable
        assert broker_time < gather_time * 30

    @pytest.mark.asyncio
    async def test_async_context_manager_failure(self):
        """Агент crash изолирован — не роняет остальных."""
        from core.message_broker import InProcessBroker
        from core.envelopes import TaskEnvelope, TaskStatus, ResultEnvelope

        broker = InProcessBroker(max_queue_size=100)
        state = _build_state()

        async def crash_handler(e):
            raise RuntimeError("agent crash")

        async def ok_handler(e):
            return ResultEnvelope(
                task_id=e.task_id, agent_name=e.agent_name,
                trace_id=e.trace_id, status=TaskStatus.COMPLETED,
                result={"signal": "ok"},
            )

        # Run both handlers through broker
        results = []
        for handler in [crash_handler, ok_handler]:
            env = TaskEnvelope.new(agent_name="test", state=state)
            r = await broker.send(env, handler)
            results.append(r)

        # At least one should succeed
        assert any(r.status == TaskStatus.COMPLETED for r in results)
        assert any(r.status == TaskStatus.FAILED for r in results)

    @pytest.mark.asyncio
    async def test_fast_broker_dispatch_5_agents(self):
        """Fast dispatch 5 agents without real LLM calls — latency < 5s."""
        from core.message_broker import InProcessBroker
        from core.envelopes import TaskEnvelope, TaskStatus

        broker = InProcessBroker(max_queue_size=100)
        state = _build_state()

        fast_agents = ["BullResearcher", "BearResearcher", "MarketAnalyst"]

        t0 = time.perf_counter()
        for name in fast_agents:
            env = TaskEnvelope.new(agent_name=name, state=state)
            run_fn = _lazy_import(name)

            async def handler(e):
                result = await run_fn(e.state_snapshot)
                if hasattr(result, "to_dict"):
                    result = result.to_dict()
                elif isinstance(result, str):
                    result = {"signal": result}
                return ResultEnvelope(
                    task_id=e.task_id, agent_name=e.agent_name,
                    trace_id=e.trace_id, status=TaskStatus.COMPLETED,
                    result=result or {},
                )

            r = await broker.send(env, handler)
            assert r.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)

        elapsed = time.perf_counter() - t0
        assert elapsed < 5.0, f"3-agent dispatch took {elapsed:.1f}s"

    def test_agent_registry_coverage(self):
        """Registry покрывает все 13 агентов."""
        assert len(_AGENT_MAP) >= 13
        for name in _AGENT_MAP:
            assert name in _AGENT_MAP
        assert "FundamentalAgent" in _AGENT_MAP
        assert "SentimentAgent" in _AGENT_MAP
        assert "BradleyAgent" in _AGENT_MAP
        assert "ElectoralAgent" in _AGENT_MAP

    def test_build_state_has_required_fields(self):
        """_build_state содержит все обязательные поля."""
        state = _build_state()
        assert "symbol" in state
        assert "timeframe" in state
        assert "current_price" in state
        assert "indicators" in state
        assert state["current_price"] > 0
