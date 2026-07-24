export const AGENT_IDS = [
  'fundamental', 'quant', 'macro', 'options_flow', 'sentiment',
  'technical', 'bull_researcher', 'bear_researcher',
  'bradley', 'electoral', 'time_window', 'gann', 'cycle',
] as const;

export type AgentId = (typeof AGENT_IDS)[number];

export type AgentSignal = 'BUY' | 'SELL' | 'HOLD' | 'SKIP';
export type AgentRunStatus = 'idle' | 'running' | 'success' | 'error';
export type AgentLiveStatus = 'pending' | 'running' | 'complete' | 'error';

export interface AgentDefinition {
  id: AgentId;
  name: string;
  weight: number;
  category: string;
}

export interface AgentEntry {
  id: string;
  name: string;
  weight: number;
  signal: AgentSignal;
  confidence: number;
}

export interface AgentResult {
  agentType: string;
  signal: AgentSignal;
  confidence: number;
  elapsedMs: number;
}

export const AGENT_DISPLAY_NAMES: Record<AgentId, string> = {
  fundamental: 'Fundamental',
  quant: 'Quant',
  macro: 'Macro',
  options_flow: 'Options Flow',
  sentiment: 'Sentiment',
  technical: 'Technical',
  bull_researcher: 'Bull Researcher',
  bear_researcher: 'Bear Researcher',
  bradley: 'Bradley',
  electoral: 'Electoral',
  time_window: 'Time Window',
  gann: 'Gann',
  cycle: 'Cycle',
};

export const AGENT_DOMAINS: Record<AgentId, string> = {
  fundamental: 'Fundamental analysis: P/E, MVRV, revenue growth, valuation models',
  quant: 'ML models, backtesting, volatility prediction, statistical arbitrage',
  macro: 'Macro economics: VIX, DXY, Fed rates, geopolitics',
  options_flow: 'Options flow analysis, unusual activity, gamma exposure',
  sentiment: 'News analysis, Reddit, X, StockTwits, Fear & Greed',
  technical: 'Technical analysis: RSI, MACD, Bollinger Bands',
  bull_researcher: 'Bull narrative + strong astrological factors',
  bear_researcher: 'Bear narrative + risk factors',
  bradley: 'Bradley seasonality model for S&P 500 + planetary aspects',
  electoral: 'Muhurta timing: Choghadiya/Nakshatra entry windows',
  time_window: 'Multi-TF windows (4H/1D/1W) + astro timing',
  gann: 'Gann angles (1×1, 1×2), price/time squares, time clusters',
  cycle: 'Dominant cycles (20/40/80 days), phases, turning points + astro-cycles',
};

// ── Live dashboard types ──

export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'error';

export interface AgentLive {
  id: string;
  name: string;
  weight: number;
  status: AgentRunStatus;
  signal: AgentSignal;
  confidence: number;
  lastResponse: string | null;
  lastError: string | null;
  lastUpdate: string;
}

export interface AgentDetail extends AgentLive {
  history: AgentResult[];
}

export interface DashboardSnapshot {
  agents: Record<string, AgentLive>;
  safety: import('./safety').SafetyGate;
  equity: import('./market').EquityPoint[];
  watchlist: import('./market').WatchlistItem[];
  ensemble: import('./ensemble').EnsembleResult;
  regime: import('./regime').Regime;
  timestamp: string;
}

// ── Typed SSE event (discriminated union) ──

export type SSEEvent =
  | { type: 'snapshot';   payload: DashboardSnapshot; timestamp: string }
  | { type: 'agents_live'; payload: AgentLive[];       timestamp: string }
  | { type: 'ensemble';   payload: import('./ensemble').EnsembleResult; timestamp: string }
  | { type: 'safety';     payload: import('./safety').SafetyGate; timestamp: string }
  | { type: 'regime';     payload: import('./regime').Regime; timestamp: string }
  | { type: 'equity';     payload: import('./market').EquityPoint[]; timestamp: string }
  | { type: 'watchlist';  payload: import('./market').WatchlistItem[]; timestamp: string }
  | { type: 'heartbeat';  payload: { latencyMs: number; uptime: string }; timestamp: string };

// ── API response types ──

export interface SessionPayload {
  sessionId: string;
  ticker: string;
  timeframe: string;
  createdAt: string;
}

export type SessionResponseItem = SessionPayload;

export interface AstroResponse {
  compositeScore: number;
  signal: string;
  interpretation: string;
}
