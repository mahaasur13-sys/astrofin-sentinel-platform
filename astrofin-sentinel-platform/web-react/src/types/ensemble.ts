import type { AgentSignal } from './agents';

export interface EnsembleResult {
  signal: AgentSignal;
  confidence: number;
  reasoning: string;
  agentsSuccess: number;
  agentsFailed: number;
  agentsSkipped: number;
  totalElapsedMs: number;
  traceparent?: string;
}

export interface EnsembleWeightEntry {
  label: string;
  pct: number;
  color: string;
}
