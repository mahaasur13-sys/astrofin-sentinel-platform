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
