import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export interface AgentDecisionDetail {
  agent_name: string;
  signal: string;
  confidence: number;
  reasoning: string;
  rag_context?: string;
}

export interface SessionDetailResponse {
  session_id: string;
  symbol: string;
  start_time: string;
  end_time?: string;
  final_signal: string;
  final_pnl?: number;
  agent_decisions: AgentDecisionDetail[];
  broker_executed_price?: number;
  broker_slippage?: number;
  broker_fee?: number;
}


export interface SessionListItem {
  id: string;
  timestamp: string;
  symbol: string;
  signal: string;
  confidence: number;
  final_pnl?: number;
}

export interface SessionListResponse {
  items: SessionListItem[];
  total: number;
}

export const sessionApi = createApi({
  reducerPath: 'sessionApi',
  baseQuery: fetchBaseQuery({ baseUrl: '/api/v1' }),
  endpoints: (builder) => ({
    getSessionsList: builder.query<SessionListResponse, { skip?: number; limit?: number }>({
      query: ({ skip = 0, limit = 50 }) => `/sessions/?skip=${skip}&limit=${limit}`,
    }),
    getSessionDetails: builder.query<SessionDetailResponse, string>({
      query: (sessionId) => `/sessions/${sessionId}/details`,
    }),
  }),
});

export const { useGetSessionDetailsQuery, useGetSessionsListQuery } = sessionApi;
