import re

# --- 1. HMMRegimeAgent: add set_pretrained_model method ---
with open("/home/workspace/agents/_impl/hmm_regime_agent.py") as f:
    content = f.read()

# Add set_pretrained_model before _init_model
if "set_pretrained_model" not in content:
    insertion = (
        "\n    def set_pretrained_model(self, regime_detector):\n"
        '        """Inject a pre-trained RegimeDetector for backtest/production inference-only mode."""\n'
        "        self._external_detector = regime_detector\n"
    )
    content = content.replace("\n    def _init_model(self):", insertion + "\n    def _init_model(self):")

# Modify analyze() to use pretrained detector
if "self._external_detector" not in content:
    old = "        features = self._extract_features(ohlcv)\n        regime, probs, log_likelihood, is_anomaly = self._predict_regime(features)"
    new = (
        "        # Use pretrained external detector if available (backtest/production mode)\n"
        "        if hasattr(self, '_external_detector') and self._external_detector:\n"
        "            regime, probs, log_likelihood, is_anomaly = self._external_detector.predict(ohlcv)\n"
        "        else:\n"
        "            features = self._extract_features(ohlcv)\n"
        "            regime, probs, log_likelihood, is_anomaly = self._predict_regime(features)"
    )
    content = content.replace(old, new)

with open("/home/workspace/agents/_impl/hmm_regime_agent.py", "w") as f:
    f.write(content)
print("✅ 1. HMMRegimeAgent patched")

# --- 2. BacktestRunner: wire real HMM agent into run() ---
with open("/home/workspace/backtest/backtest_runner.py") as f:
    content = f.read()

# Add import
if "from agents._impl.hmm_regime_agent import" not in content:
    old = "from core.base_agent import AgentResponse, SignalDirection"
    new = "from core.base_agent import AgentResponse, SignalDirection\nfrom agents._impl.hmm_regime_agent import HMMRegimeAgent"
    content = content.replace(old, new)

# Replace run() method to use real HMM agent
if "_build_responses" in content:
    # Replace the entire run method (from "async def run" to "return self.stats")
    old_run_start = "    async def run(self, ohlcv: list, symbol: str = \"BTCUSDT\") -> BacktestStats:"
    new_run = """    async def run(self, ohlcv: list, symbol: str = "BTCUSDT") -> BacktestStats:
        \"\"\"Run backtest using production pipeline: HMMRegimeAgent → CouncilOrchestrator.\"\"\"
        lookback = getattr(self, '_lookback', 60)
        self.stats.equity_curve = [self.initial_capital]

        # Create HMM agent once (with pretrained detector if available)
        hmm_agent = HMMRegimeAgent()
        if hasattr(self, '_regime_detector') and self._regime_detector:
            hmm_agent.set_pretrained_model(self._regime_detector)

        for i in range(lookback, len(ohlcv)):
            window = ohlcv[max(0, i - lookback) : i + 1]
            current_price = ohlcv[i]["close"] if isinstance(ohlcv[i], dict) else ohlcv[i].get("close", 0)

            from core.base_agent import AgentResponse, SignalDirection

            state = {"symbol": symbol, "ohlcv": window, "current_price": current_price}

            # Run real HMM agent
            hmm_response = await hmm_agent.run(state)

            # Build council responses (Quant + HMM)
            quant_response = AgentResponse(
                agent_name="QuantAgent",
                signal=SignalDirection.LONG,
                confidence=80,
                reasoning="Backtest simulated Quant response",
                sources=[],
                metadata={},
            )

            agent_responses = [hmm_response, quant_response]
            final_signal = SignalDirection.LONG if quant_response.confidence >= 50 else SignalDirection.NEUTRAL

            if final_signal == SignalDirection.NEUTRAL:
                current_equity = self.capital + (self.position * current_price)
                self.stats.equity_curve.append(current_equity)
                continue

            action = await self.orch.execute_trading_cycle(
                agent_responses=agent_responses,
                final_signal=final_signal,
                config={"symbol": symbol, "base_position_size": 1.0},
                is_backtest=True,
            )

            self._simulate_trade(action, current_price)

            current_equity = self.capital + (self.position * current_price)
            self.stats.equity_curve.append(current_equity)

            if current_equity > self.stats.peak_equity:
                self.stats.peak_equity = current_equity
            drawdown = (self.stats.peak_equity - current_equity) / self.stats.peak_equity if self.stats.peak_equity > 0 else 0
            if drawdown > self.stats.max_drawdown:
                self.stats.max_drawdown = drawdown

        self.stats.final_equity = self.stats.equity_curve[-1] if self.stats.equity_curve else self.initial_capital
        return self.stats"""

    # Replace old run() with new one
    import re
    pattern = re.compile(r'    async def run\(self, ohlcv: list.*?\n(?=    def _simulate_trade)', re.DOTALL)
    content = pattern.sub(new_run + '\n\n', content)

with open("/home/workspace/backtest/backtest_runner.py", "w") as f:
    f.write(content)
print("✅ 2. BacktestRunner patched")

# --- 3. analyze_backtest.py: use RegimeDetector and pass cached real data ---
with open("/home/workspace/scripts/analyze_backtest.py") as f:
    content = f.read()

if "from backtest.regime_detector import RegimeDetector" not in content:
    old = "from backtest.backtest_runner import BacktestRunner, generate_random_ohlcv"
    new = "from backtest.backtest_runner import BacktestRunner, generate_random_ohlcv\nfrom backtest.regime_detector import RegimeDetector"
    content = content.replace(old, new)
    
    # Replace the ohlcv loading in the main block to use cached real data
    old_load = '    ohlcv = generate_random_ohlcv(n_bars=500, seed=42)'
    new_load = """    # Try cached BTC data first, fallback to random
    import json
    cache_path = os.path.join(os.path.dirname(__file__), "..", "backtest/data_cache/btc_coingecko_365d.jsonl")
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            ohlcv = [json.loads(line) for line in f if line.strip()]
        print(f"  Using cached BTC data: {len(ohlcv)} bars")
    else:
        ohlcv = generate_random_ohlcv(n_bars=500, seed=42)
        print(f"  Using synthetic data: {len(ohlcv)} bars")"""
    content = content.replace(old_load, new_load)

with open("/home/workspace/scripts/analyze_backtest.py", "w") as f:
    f.write(content)
print("✅ 3. analyze_backtest.py patched")
