import { z } from 'zod';

export const RegimeSchema = z.enum(['bull', 'bear', 'sideways', 'high_vol', 'anomaly']);

export const SignalDirectionSchema = z.enum(['BUY', 'SELL', 'HOLD', 'SKIP']);

export const AgentLiveStatusSchema = z.enum(['pending', 'running', 'complete', 'error']);

export const AgentRunStatusSchema = z.enum(['idle', 'running', 'success', 'error']);

export const AgentStatusSchema = z.object({
  id: z.string(),
  name: z.string(),
  status: z.enum(['running', 'idle', 'error', 'offline']),
  weight: z.number(),
  lastSignal: SignalDirectionSchema.nullable(),
  lastUpdate: z.string(),
});

export const WatchlistItemSchema = z.object({
  ticker: z.string(),
  changePercent: z.number(),
});

export const SafetyGateSchema = z.object({
  status: z.enum(['safe', 'warning', 'danger', 'stopped']),
  riskPct: z.number(),
  maxDrawdown: z.number(),
  var95: z.number(),
  leverage: z.number(),
  triggers: z.array(z.object({ time: z.string(), reason: z.string() })),
});

export const EquityPointSchema = z.object({
  date: z.string(),
  equity: z.number(),
  regime: RegimeSchema,
});

export const AgentLiveSchema = z.object({
  id: z.string(),
  name: z.string(),
  weight: z.number(),
  status: AgentRunStatusSchema,
  signal: SignalDirectionSchema,
  confidence: z.number(),
  lastResponse: z.string().nullable(),
  lastError: z.string().nullable(),
  lastUpdate: z.string(),
});

export const AgentResultSchema = z.object({
  agentType: z.string(),
  signal: SignalDirectionSchema,
  confidence: z.number(),
  reasoning: z.string(),
  elapsedMs: z.number(),
  error: z.string().optional(),
});

export const DashboardSnapshotSchema = z.object({
  agents: z.record(z.string(), AgentLiveSchema),
  safety: SafetyGateSchema,
  equity: z.array(EquityPointSchema),
  watchlist: z.array(WatchlistItemSchema),
  ensemble: z.object({
    signal: SignalDirectionSchema,
    confidence: z.number(),
  }),
  regime: RegimeSchema,
  timestamp: z.string(),
});

export const SessionPayloadSchema = z.object({
  sessionId: z.string(),
  ticker: z.string(),
  timeframe: z.string(),
  createdAt: z.string(),
});

export const SessionResponseSchema = z.array(SessionPayloadSchema);

export const AstroPayloadSchema = z.object({
  ticker: z.string(),
  date: z.string().optional(),
});

export const AstroResponseSchema = z.object({
  compositeScore: z.number(),
  signal: z.string(),
  interpretation: z.string(),
});

export const SSEEventSchema = z.object({
  type: z.enum(['snapshot', 'agents_live', 'ensemble', 'safety', 'regime', 'equity', 'watchlist', 'heartbeat']),
  payload: z.unknown(),
  timestamp: z.string(),
});

export const agentLiveSchema = AgentLiveSchema;
export const agentResultSchema = AgentResultSchema;
export const dashboardSnapshotSchema = DashboardSnapshotSchema;
export const sessionPayloadSchema = SessionPayloadSchema;
export const sessionResponseSchema = SessionResponseSchema;
export const astroPayloadSchema = AstroPayloadSchema;
export const astroResponseSchema = AstroResponseSchema;
