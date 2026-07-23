# Technical Indicators — RSI, MACD, Bollinger

## RSI (Relative Strength Index)

RSI = 100 - (100 / (1 + RS)), where RS = avg gain / avg loss over 14 periods.

| RSI Value | Interpretation |
|-----------|---------------|
| > 70 | Overbought — potential reversal or continuation |
| < 30 | Oversold — potential reversal or continuation |
| 50 | Neutral balance |

**Trading rules:**
- RSI > 70 + price divergence → bearish reversal signal
- RSI < 30 + price divergence → bullish reversal signal
- RSI crossing 50 from below → short-term bullish
- RSI crossing 50 from above → short-term bearish

## MACD (Moving Average Convergence Divergence)

MACD Line = EMA(12) - EMA(26)
Signal Line = EMA(9) of MACD Line
Histogram = MACD Line - Signal Line

**Signals:**
- MACD crosses above Signal → bullish
- MACD crosses below Signal → bearish
- MACD above zero → short-term uptrend
- MACD below zero → short-term downtrend

## Bollinger Bands

Middle = 20-period SMA
Upper = Middle + 2× standard deviation
Lower = Middle - 2× standard deviation

**Rules:**
- Price touching upper band → overbought
- Price touching lower band → oversold
- Squeeze (bands narrow) → breakout coming
- Bands expanding → volatility increasing
