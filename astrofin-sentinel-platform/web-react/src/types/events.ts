import type { Regime, RegimeProbability } from './regime';
import type { SafetyStatus } from './safety';
import type { AgentId, AgentSignal, AgentLiveStatus } from './agents';

export interface SSERegimeEvent {
  type: 'regime';
  data: {
    regime: Regime;
    probabilities: RegimeProbability[];
    confidence: number;
  };
}

export interface SSESafetyEvent {
  type: 'safety';
  data: {
    status: SafetyStatus;
    maxDrawdown: number;
    dailyLoss: number;
    leverage: number;
  };
}

export interface SSEAgentEvent {
  type: 'agent';
  data: {
    agentType: AgentId;
    status: AgentLiveStatus;
    signal: AgentSignal;
    confidence: number;
    elapsedMs: number;
  };
}

export interface SSEEnsembleEvent {
  type: 'ensemble';
  data: {
    signal: AgentSignal;
    confidence: number;
    agentsSuccess: number;
    agentsFailed: number;
    agentsSkipped: number;
    totalElapsedMs: number;
  };
}

export type ParsedSSEEvent =
  | SSERegimeEvent
  | SSESafetyEvent
  | SSEAgentEvent
  | SSEEnsembleEvent;
