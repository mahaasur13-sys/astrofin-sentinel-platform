# Agent Registry - AstroFin Sentinel V5

Status: 16 active agent implementations as of 2026-06-30

## Active Agents (16)

| Agent | File | Weight | Domain | Status |
|-------|------|--------|--------|--------|
| bradley_agent | agents/_impl/bradley_agent.py | 3% (Bradley seasonality) | Astrology/Bradley | Active |
| compromise_agent | agents/_impl/compromise_agent.py | Conflict resolution | Conflict | Active |
| cycle_agent | agents/_impl/cycle_agent.py | 5% (Market cycles) | Astrology/Cycles | Active |
| electoral_agent | agents/_impl/electoral_agent.py | 3% (Muhurta timing) | Astrology/Electoral | Active |
| elliot_agent | agents/_impl/elliot_agent.py | Elliot Wave | Elliot Wave | Active |
| fundamental_agent | agents/_impl/fundamental_agent.py | 20% (12% Fundamental+Macro block) | Fundamental analysis | Active |
| gann_agent | agents/_impl/gann_agent.py | 3% (Gann angles) | Astrology/Gann | Active |
| insider_agent | agents/_impl/insider_agent.py | Insider activity | Insider | Active |
| macro_agent | agents/_impl/macro_agent.py | 15% | Macroeconomics | Active |
| ml_predictor_agent | agents/_impl/ml_predictor_agent.py | ML (20% Quant block) | ML prediction | Active |
| options_flow_agent | agents/_impl/options_flow_agent.py | 15% | Options flow | Active |
| quant_agent | agents/_impl/quant_agent.py | 20% | Quantitative | Active |
| risk_agent | agents/_impl/risk_agent.py | Risk overlay | Risk | Active |
| sentiment_agent | agents/_impl/sentiment_agent.py | 10% | Sentiment | Active |
| technical_agent | agents/_impl/technical_agent.py | 10% | Technical | Active |
| time_window_agent | agents/_impl/time_window_agent.py | 2% (Multi-TF) | Astrology/Timing | Active |

## Archived

- 7 root duplicates archived to agents/_archived/ (2026-03-26)
- 1 stub: agents/astro_council_agent.py (replaced by agents/_impl/astro_council/agent.py)

## R5 Coverage: 100% (16/16 in agents/_impl/ __init__.py)
