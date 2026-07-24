export const API_BASE = '/api/v1';

export const ENDPOINTS = {
  dashboard:    `${API_BASE}/dashboard`,
  agentRun:     `${API_BASE}/agent/run`,
  agentAnalyze: `${API_BASE}/agent/analyze`,
  sessionsList: `${API_BASE}/sessions`,
  sessionDetail: (id: string) => `${API_BASE}/sessions/${id}/details`,
  astroInterpretation: `${API_BASE}/astro/interpretation`,
  astroAspects: `${API_BASE}/astro/aspects`,
  stream:       '/api/v1/stream',
  health:       '/health',
} as const;
