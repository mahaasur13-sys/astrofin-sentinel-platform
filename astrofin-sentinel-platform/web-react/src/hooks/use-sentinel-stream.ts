'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
type RegimeProbability = { regime: string; probability: number }

export interface RegimeUpdate {
  regime: string;
  probabilities: RegimeProbability[];
  confidence: number;
}

export interface SafetyUpdate {
  status: string;
  maxDrawdown: number;
  dailyLoss: number;
  leverage: number;
}

export interface AgentStreamUpdate {
  agentType: string;
  status: string;
  signal: string;
  confidence: number;
  elapsedMs: number;
}

export interface EnsembleStreamUpdate {
  signal: string;
  confidence: number;
  agentsSuccess: number;
  agentsFailed: number;
  agentsSkipped: number;
  totalElapsedMs: number;
}

export interface SentinelStreamState {
  connected: boolean;
  regime: RegimeUpdate | null;
  safety: SafetyUpdate | null;
  lastAgentUpdate: AgentStreamUpdate | null;
  lastEnsembleUpdate: EnsembleStreamUpdate | null;
  eventCount: number;
  error: string | null;
}

export function useSentinelStream(enabled: boolean = true) {
  const [state, setState] = useState<SentinelStreamState>({
    connected: false,
    regime: null,
    safety: null,
    lastAgentUpdate: null,
    lastEnsembleUpdate: null,
    eventCount: 0,
    error: null,
  });

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttempts = useRef(0);
  const isMounted = useRef(true);

  const connect = useCallback(() => {
    if (!enabled || !isMounted.current) return;

    try {
      const es = new EventSource('/api/stream');
      eventSourceRef.current = es;

      es.onopen = () => {
        reconnectAttempts.current = 0;
        if (isMounted.current) {
          setState((prev) => ({ ...prev, connected: true, error: null }));
        }
      };

      es.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);

          setState((prev) => {
            const newState: SentinelStreamState = { ...prev, eventCount: prev.eventCount + 1 };

            switch (parsed.type) {
              case 'regime':
                newState.regime = parsed.data as RegimeUpdate;
                break;
              case 'safety':
                newState.safety = parsed.data as SafetyUpdate;
                break;
              case 'agent':
                newState.lastAgentUpdate = parsed.data as AgentStreamUpdate;
                break;
              case 'ensemble':
                newState.lastEnsembleUpdate = parsed.data as EnsembleStreamUpdate;
                break;
            }

            return newState;
          });
        } catch (parseError) {
          console.warn('SSE parse error:', parseError);
        }
      };

      es.onerror = () => {
        es.close();
        eventSourceRef.current = null;
        if (isMounted.current) {
          setState((prev) => ({ ...prev, connected: false, error: 'Connection lost' }));
        }

        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectAttempts.current++;

        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      };
    } catch (err) {
      if (isMounted.current) {
        setState((prev) => ({ ...prev, error: String(err) }));
      }
    }
  }, [enabled]);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    setState((prev) => ({ ...prev, connected: false }));
  }, []);

  useEffect(() => {
    isMounted.current = true;
    if (enabled) {
      connect();
    } else {
      disconnect();
    }
    return () => {
      isMounted.current = false;
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  return state;
}
