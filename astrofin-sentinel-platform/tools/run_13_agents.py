#!/usr/bin/env python3
"""Sprint 6: Concurrent 13-Agent Execution + Ensemble Voting Engine.

Usage:
    cd /home/workspace/astrofin-sentinel-platform
    source venv/bin/activate
    python tools/run_13_agents.py                            # BTCUSDT @ $105k
    python tools/run_13_agents.py BTCUSDT 105000 LOW         # with regime
    python tools/run_13_agents.py ETHUSDT 3200 HIGH Pushya   # with nakshatra
"""

import asyncio
import importlib
import sys
from core.message_broker import InProcessBroker
from core.ensemble_voting import EnsembleVotingEngine, ensemble_from_13_agents

AGENTS = {
    'fundamental':     ('agents._impl.fundamental_agent', 'run_fundamental_agent'),
    'macro':           ('agents._impl.macro_agent', 'run_macro_agent'),
    'quant':           ('agents._impl.quant_agent', 'run_quant_agent'),
    'sentiment':       ('agents._impl.sentiment_agent', 'run_sentiment_agent'),
    'options_flow':    ('agents._impl.options_flow_agent', 'run_options_flow_agent'),
    'bull':            ('agents._impl.bull_researcher', 'run_bull_researcher'),
    'bear':            ('agents._impl.bear_researcher', 'run_bear_researcher'),
    'market_analyst':  ('agents._impl.market_analyst', 'run_market_analyst'),
    'technical':       ('agents._impl.technical_agent', 'run_technical_agent'),
    'electoral':       ('agents._impl.electoral_agent', 'run_electoral_agent'),
    'bradley':         ('agents._impl.bradley_agent', 'run_bradley_agent'),
    'gann':            ('agents._impl.gann_agent', 'run_gann_agent'),
    'cycle':           ('agents._impl.cycle_agent', 'run_cycle_agent'),
}


def extract_signal(result):
    if not isinstance(result, dict):
        return 'N/A', -1, str(result)[:80]
    for v in result.values():
        if isinstance(v, dict):
            return v.get('signal', 'N/A'), v.get('confidence', -1), v.get('reasoning', '')[:80]
    return 'N/A', -1, str(result)[:80]


async def main(symbol='BTCUSDT', price=105000.0, regime='NORMAL', nakshatra=''):
    state = {'symbol': symbol, 'current_price': price, 'timeframe': '1d'}
    broker = InProcessBroker()
    await broker.start()
    header = f'{symbol} @ ${price:,.0f}'
    if nakshatra:
        header += f' | Nakshatra: {nakshatra}'
    print(f'✅ Broker started — {header}\n')

    tasks = []
    for name, (mod_path, fn_name) in AGENTS.items():
        try:
            mod = importlib.import_module(mod_path)
            fn = getattr(mod, fn_name)
            tasks.append((name, asyncio.create_task(fn(state))))
        except Exception as e:
            print(f'  ❌ {name:20s} — import error: {e}')

    print(f'🔄 {len(tasks)} agents running concurrently...\n')
    results_list = await asyncio.gather(*[t for _, t in tasks], return_exceptions=True)
    await broker.close()

    LINE = '━' * 85
    print(f'{LINE}\n  {"AGENT":22s} {"SIGNAL":>9s} {"CONF%":>6s}  REASONING\n{LINE}')

    agent_results: dict[str, dict] = {}
    for (name, _), r in zip(tasks, results_list):
        if isinstance(r, Exception):
            print(f'  ❌ {name:20s} │ {type(r).__name__}: {str(r)[:70]}')
            agent_results[name] = {}
        else:
            sig, conf, reason = extract_signal(r)
            agent_results[name] = r
            print(f'  ✅ {name:20s} │ {sig:>8s} │ {conf:4.0f}% │ {reason}')
    print(LINE)

    ok = sum(1 for r in results_list if not isinstance(r, Exception))
    print(f'\n  {ok}/{len(results_list)} agents completed')

    # ── Ensemble Vote ──
    print()
    ens = ensemble_from_13_agents(agent_results, regime, nakshatra)
    print(ens.summary())

    if ok == len(results_list):
        print('\n  🟢 All agents OK — Sprint 6 ensemble complete')


if __name__ == '__main__':
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'BTCUSDT'
    price = float(sys.argv[2]) if len(sys.argv) > 2 else 105000.0
    regime = sys.argv[3] if len(sys.argv) > 3 else 'NORMAL'
    nakshatra = sys.argv[4] if len(sys.argv) > 4 else ''
    asyncio.run(main(symbol, price, regime, nakshatra))
