import type { AgentId, Ticker, Timeframe } from '@/types';

export const AGENT_TYPES = [
  'fundamental',
  'quant',
  'macro',
  'options_flow',
  'sentiment',
  'technical',
  'bull_researcher',
  'bear_researcher',
  'bradley',
  'electoral',
  'time_window',
  'gann',
  'cycle',
] as const;

export const ENSEMBLE_WEIGHTS: Record<AgentId, number> = {
  fundamental: 0.20,
  quant: 0.20,
  macro: 0.15,
  options_flow: 0.15,
  sentiment: 0.10,
  technical: 0.10,
  bull_researcher: 0.05,
  bear_researcher: 0.05,
  bradley: 0.03,
  electoral: 0.03,
  time_window: 0.02,
  gann: 0.03,
  cycle: 0.05,
};

export const WATCHLIST_TICKERS: Ticker[] = [
  'BTC-USD', 'ETH-USD', 'SPX', 'NDX', 'NVDA', 'AAPL', 'GC=F', 'CL=F',
];

export const TIMEFRAMES: Timeframe[] = ['1m', '5m', '15m', '1H', '4H', '1D', '1W'];

export const MODE_TABS = ['LIVE', 'BACKTEST', 'PAPER', 'OPTIMIZE'] as const;

export const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: 'Activity' },
  { id: 'trading',   label: 'Trading',   icon: 'TrendingUp' },
  { id: 'analytics', label: 'Analytics', icon: 'BarChart3' },
  { id: 'agents',    label: 'Agents',    icon: 'Layers' },
  { id: 'backtest',  label: 'Backtest',  icon: 'Route' },
  { id: 'settings',  label: 'Settings',  icon: 'Settings' },
] as const;

export const SSE_RECONNECT_MAX_RETRIES = 5;
export const SSE_RECONNECT_MAX_DELAY_MS = 30_000;

export const FETCH_TIMEOUT_MS = 10_000;
export const FETCH_MAX_RETRIES = 2;
