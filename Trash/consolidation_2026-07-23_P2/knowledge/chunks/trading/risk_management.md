# Risk Management Framework

## Core Rules

1. **Never risk more than 1-2% of capital on a single trade**
2. **Always use stop losses** — no exceptions
3. **Diversify across uncorrelated assets**
4. **Keep a cash reserve** — minimum 20% not deployed

## Dynamic Risk Scaling

Adjust position size based on:
- Account equity curve (reduce when drawdown > 5%)
- Current volatility (smaller positions in high VIX periods)
- Confidence score from AstroFin signals

| Signal Confidence | Position Size Multiplier |
|-------------------|-------------------------|
| 90-100% | 1.5× base |
| 70-89% | 1.0× base |
| 50-69% | 0.5× base |
| < 50% | Skip trade |

## Drawdown Rules

- Drawdown > 5%: reduce risk by 50%
- Drawdown > 10%: halt trading, review system
- Drawdown > 20%: trading account is suspended
