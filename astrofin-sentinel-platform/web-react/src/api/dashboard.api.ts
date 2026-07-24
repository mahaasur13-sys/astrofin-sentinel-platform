import { get, post } from './client';
import { ENDPOINTS } from '@/config/api';
import {
  dashboardSnapshotSchema,
  agentLiveSchema,
  agentResultSchema,
  sessionPayloadSchema,
  sessionResponseSchema,
  astroResponseSchema,
} from '@/types/schemas';

export function fetchDashboardSnapshot() {
  return get(dashboardSnapshotSchema, ENDPOINTS.dashboard);
}

export function runAgent(agentId: string, prompt: string) {
  return post(agentResultSchema, ENDPOINTS.agentRun, { agentId, prompt });
}

export function analyzeAgent(name: string) {
  return get(agentLiveSchema, ENDPOINTS.agentAnalyze.replace(':agent', name));
}

export function fetchSessions(page = 1, limit = 20) {
  return get(sessionResponseSchema, `${ENDPOINTS.sessionsList}?page=${page}&limit=${limit}`);
}

export function fetchSessionDetail(sessionId: string) {
  return get(sessionPayloadSchema, ENDPOINTS.sessionDetail(sessionId));
}

export function postAstroInterpretation(payload: { ticker: string; date?: string }) {
  return post(astroResponseSchema, ENDPOINTS.astroInterpretation, payload);
}

export function fetchAstroAspects(payload: { ticker: string; date?: string }) {
  return post(astroResponseSchema, ENDPOINTS.astroAspects, payload);
}
