/**
 * AstroFin Sentinel — Agent type definitions and weights.
 * Maps to the 13 agents from orchestration/sentinel_v5.py ENSEMBLE_WEIGHTS.
 */

export const AGENT_TYPES = [
  'fundamental',
  'quant',
  'sentiment',
  'technical',
  'macro',
  'risk',
  'news',
  'options',
  'crypto',
  'astrology',
  'commodity',
  'forex',
  'bond',
] as const;

export type AgentType = (typeof AGENT_TYPES)[number];

export const ENSEMBLE_WEIGHTS: Record<AgentType, number> = {
  fundamental: 0.15,
  quant: 0.12,
  sentiment: 0.10,
  technical: 0.14,
  macro: 0.10,
  risk: 0.13,
  news: 0.08,
  options: 0.06,
  crypto: 0.04,
  astrology: 0.03,
  commodity: 0.03,
  forex: 0.01,
  bond: 0.01,
};

export interface AgentResponse {
  signal: 'BUY' | 'SELL' | 'HOLD' | 'SKIP';
  confidence: number;
  reasoning: string;
  metadata?: Record<string, unknown>;
}

export interface EnsembleResult {
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  reasoning: string;
  agentsSuccess: number;
  agentsFailed: number;
  agentsSkipped: number;
  totalElapsedMs: number;
  traceparent?: string;
  individualResults?: Record<string, AgentResult>;
}

export interface AgentResult {
  agentType: string;
  signal: string;
  confidence: number;
  reasoning: string;
  elapsedMs: number;
  error?: string;
}

export interface AnalysisSession {
  id: string;
  ticker: string;
  timeframe: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'TIMEOUT';
  finalSignal?: string;
  confidence: number;
  reasoning?: string;
  traceparent?: string;
  createdAt: string;
  completedAt?: string;
}

export const SIGNAL_COLORS: Record<string, string> = {
  BUY: 'text-emerald-500',
  SELL: 'text-red-500',
  HOLD: 'text-amber-500',
  SKIP: 'text-gray-500',
};

export const SIGNAL_BG: Record<string, string> = {
  BUY: 'bg-emerald-500/10 border-emerald-500/30',
  SELL: 'bg-red-500/10 border-red-500/30',
  HOLD: 'bg-amber-500/10 border-amber-500/30',
  SKIP: 'bg-gray-500/10 border-gray-500/30',
};

export const AGENT_ICONS: Record<AgentType, string> = {
  fundamental: 'BarChart3',
  quant: 'TrendingUp',
  sentiment: 'MessageSquare',
  technical: 'CandlestickChart',
  macro: 'Globe',
  risk: 'ShieldAlert',
  news: 'Newspaper',
  options: 'Layers',
  crypto: 'Bitcoin',
  astrology: 'Sparkles',
  commodity: 'Gem',
  forex: 'ArrowLeftRight',
  bond: 'Landmark',
};

export const AGENT_DESCRIPTIONS: Record<AgentType, string> = {
  fundamental: 'Financial health, earnings, P/E ratios, revenue growth',
  quant: 'Statistical models, price patterns, mean reversion, momentum',
  sentiment: 'Social media trends, news tone, fear/greed index',
  technical: 'Chart patterns, support/resistance, RSI, MACD',
  macro: 'GDP trends, interest rates, inflation, central bank policy',
  risk: 'Portfolio risk, volatility, drawdown, position sizing',
  news: 'Breaking news impact, regulatory changes, market events',
  options: 'Options flow, implied volatility, put/call ratios',
  crypto: 'Crypto market analysis, blockchain metrics, DeFi',
  astrology: 'Planetary transits, Mercury retrograde, lunar cycles',
  commodity: 'Commodity prices, supply/demand, seasonal patterns',
  forex: 'Currency pairs, FX rates, carry trade, central bank signals',
  bond: 'Yield curves, credit spreads, duration risk, bond ratings',
};
