/**
 * AstroFin Sentinel — WebSocket client for real-time agent status.
 * Connects via socket.io through Caddy gateway.
 */
'use client';

import { io, Socket } from 'socket.io-client';
import type { AgentResult } from './agents';

export type AgentStatus = 'pending' | 'running' | 'complete' | 'error';

export interface AgentStatusUpdate {
  sessionId: string;
  agentType: string;
  status: AgentStatus;
  result?: AgentResult;
  elapsedMs?: number;
  error?: string;
}

export interface AnalysisStartEvent {
  sessionId: string;
  ticker: string;
  timeframe: string;
  agents: string[];
  timestamp: number;
}

export interface AnalysisCompleteEvent {
  sessionId: string;
  signal: string;
  confidence: number;
  reasoning: string;
  agentsSuccess: number;
  agentsFailed: number;
  agentsSkipped: number;
  totalElapsedMs: number;
  traceparent?: string;
}

type StatusHandler = (update: AgentStatusUpdate) => void;
type StartHandler = (event: AnalysisStartEvent) => void;
type CompleteHandler = (event: AnalysisCompleteEvent) => void;

class SentinelSocket {
  private socket: Socket | null = null;
  private statusHandlers: StatusHandler[] = [];
  private startHandlers: StartHandler[] = [];
  private completeHandlers: CompleteHandler[] = [];
  private connected = false;

  connect(): Socket {
    if (this.socket?.connected) return this.socket;

    this.socket = io('/?XTransformPort=3032', {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
    });

    this.socket.on('connect', () => {
      console.log('[SentinelWS] Connected');
      this.connected = true;
    });

    this.socket.on('disconnect', () => {
      console.log('[SentinelWS] Disconnected');
      this.connected = false;
    });

    this.socket.on('agent:status', (update: AgentStatusUpdate) => {
      this.statusHandlers.forEach((h) => h(update));
    });

    this.socket.on('analysis:start', (event: AnalysisStartEvent) => {
      this.startHandlers.forEach((h) => h(event));
    });

    this.socket.on('analysis:complete', (event: AnalysisCompleteEvent) => {
      this.completeHandlers.forEach((h) => h(event));
    });

    return this.socket;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  subscribeSession(sessionId: string) {
    this.socket?.emit('subscribe:session', { sessionId });
  }

  unsubscribeSession(sessionId: string) {
    this.socket?.emit('unsubscribe:session', { sessionId });
  }

  onAgentStatus(handler: StatusHandler) {
    this.statusHandlers.push(handler);
    return () => {
      this.statusHandlers = this.statusHandlers.filter((h) => h !== handler);
    };
  }

  onAnalysisStart(handler: StartHandler) {
    this.startHandlers.push(handler);
    return () => {
      this.startHandlers = this.startHandlers.filter((h) => h !== handler);
    };
  }

  onAnalysisComplete(handler: CompleteHandler) {
    this.completeHandlers.push(handler);
    return () => {
      this.completeHandlers = this.completeHandlers.filter((h) => h !== handler);
    };
  }

  isConnected(): boolean {
    return this.connected;
  }
}

export const sentinelSocket = new SentinelSocket();
