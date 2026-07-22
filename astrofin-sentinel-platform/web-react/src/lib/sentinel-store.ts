/**
 * AstroFin Sentinel — Global state store with Zustand.
 * Manages analysis sessions, agent results, and real-time updates.
 */
'use client';

import { create } from 'zustand';
import {
  AgentType,
  AgentResult,
  EnsembleResult,
  AnalysisSession,
  AGENT_TYPES,
} from './agents';
import { AgentStatus, AgentStatusUpdate } from './sentinel-socket';

export interface AgentLiveStatus {
  agentType: AgentType;
  status: AgentStatus;
  result?: AgentResult;
  elapsedMs?: number;
  error?: string;
  startedAt?: number;
}

interface SentinelState {
  currentSessionId: string | null;
  currentTicker: string;
  currentTimeframe: string;
  isAnalyzing: boolean;

  agentStatuses: Record<string, AgentLiveStatus>;

  ensembleResult: EnsembleResult | null;

  sessions: AnalysisSession[];

  documentCount: number;

  startAnalysis: (ticker: string, timeframe: string) => void;
  setSessionId: (id: string) => void;
  updateAgentStatus: (update: AgentStatusUpdate) => void;
  setEnsembleResult: (result: EnsembleResult) => void;
  finishAnalysis: () => void;
  addSession: (session: AnalysisSession) => void;
  setDocumentCount: (count: number) => void;
  resetCurrent: () => void;
}

export const useSentinelStore = create<SentinelState>((set) => ({
  currentSessionId: null,
  currentTicker: '',
  currentTimeframe: '1d',
  isAnalyzing: false,
  agentStatuses: {},
  ensembleResult: null,
  sessions: [],
  documentCount: 0,

  startAnalysis: (ticker, timeframe) => {
    const statuses: Record<string, AgentLiveStatus> = {};
    AGENT_TYPES.forEach((type) => {
      statuses[type] = { agentType: type, status: 'pending' };
    });

    set({
      currentTicker: ticker,
      currentTimeframe: timeframe,
      isAnalyzing: true,
      agentStatuses: statuses,
      ensembleResult: null,
      currentSessionId: null,
    });
  },

  setSessionId: (id) => set({ currentSessionId: id }),

  updateAgentStatus: (update) => {
    const { agentType, status, result, elapsedMs, error } = update;
    set((state) => ({
      agentStatuses: {
        ...state.agentStatuses,
        [agentType]: {
          agentType: agentType as AgentType,
          status,
          result,
          elapsedMs,
          error,
          startedAt:
            status === 'running'
              ? Date.now()
              : state.agentStatuses[agentType]?.startedAt,
        },
      },
    }));
  },

  setEnsembleResult: (result) => set({ ensembleResult: result }),

  finishAnalysis: () => set({ isAnalyzing: false }),

  addSession: (session) =>
    set((state) => ({
      sessions: [session, ...state.sessions].slice(0, 50),
    })),

  setDocumentCount: (count) => set({ documentCount: count }),

  resetCurrent: () =>
    set({
      currentSessionId: null,
      currentTicker: '',
      currentTimeframe: '1d',
      isAnalyzing: false,
      agentStatuses: {},
      ensembleResult: null,
    }),
}));
