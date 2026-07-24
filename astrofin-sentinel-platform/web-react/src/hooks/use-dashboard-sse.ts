import { useEffect, useRef } from 'react';
import { useDashboardStore } from '@/stores/dashboard.store';
import type { DashboardSnapshot, AgentLive, EnsembleResult, SafetyGate, Regime, EquityPoint, WatchlistItem } from '@/types';
import { env } from '@/config/env';

const RECONNECT_BASE_MS = 1_000;
const RECONNECT_MAX_MS = 30_000;

interface SSERawEvent {
  type: string;
  payload: unknown;
  timestamp: string;
}

export function useDashboardSSE() {
  const store = useDashboardStore();
  const retries = useRef(0);
  const eventSource = useRef<EventSource | null>(null);

  useEffect(() => {
    let cancelled = false;
    let reconnectTimer: ReturnType<typeof setTimeout>;

    function connect() {
      if (cancelled) return;

      store.setConnectionStatus('connecting');

      const es = new EventSource(env.VITE_SSE_URL);
      eventSource.current = es;

      es.onopen = () => {
        retries.current = 0;
        store.setConnectionStatus('connected');
        store.setLastConnectedAt(new Date().toISOString());
      };

      es.onmessage = (e: MessageEvent) => {
        try {
          const raw: SSERawEvent = JSON.parse(e.data);

          switch (raw.type) {
            case 'snapshot': {
              const snapshot = raw.payload as DashboardSnapshot;
              store.setSnapshot(snapshot);
              store.setAgents(Object.values(snapshot.agents));
              store.setSafety(snapshot.safety);
              store.setRegime(snapshot.regime);
              store.setEquity(snapshot.equity);
              store.setWatchlist(snapshot.watchlist);
              store.setEnsemble(snapshot.ensemble);
              store.setLastUpdate(snapshot.timestamp);
              break;
            }
            case 'agents_live':
              store.setAgents(raw.payload as AgentLive[]);
              break;
            case 'ensemble':
              store.setEnsemble(raw.payload as EnsembleResult);
              break;
            case 'safety':
              store.setSafety(raw.payload as SafetyGate);
              break;
            case 'regime':
              store.setRegime(raw.payload as Regime);
              break;
            case 'equity':
              store.setEquity(raw.payload as EquityPoint[]);
              break;
            case 'watchlist':
              store.setWatchlist(raw.payload as WatchlistItem[]);
              break;
            case 'heartbeat': {
              const hb = raw.payload as { latency_ms?: number };
              if (hb.latency_ms) store.setLatencyMs(hb.latency_ms);
              break;
            }
          }
        } catch {
          // Malformed event — ignore, let reconnect handle it
        }
      };

      es.onerror = () => {
        es.close();
        eventSource.current = null;

        if (cancelled) return;

        store.setConnectionStatus('disconnected');

        const delay = Math.min(
          RECONNECT_BASE_MS * 2 ** retries.current,
          RECONNECT_MAX_MS,
        );
        retries.current += 1;

        reconnectTimer = setTimeout(connect, delay);
      };
    }

    connect();

    return () => {
      cancelled = true;
      clearTimeout(reconnectTimer);
      eventSource.current?.close();
      store.setConnectionStatus('disconnected');
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
}
