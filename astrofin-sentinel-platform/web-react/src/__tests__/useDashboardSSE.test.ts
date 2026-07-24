import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useDashboardStore } from '@/stores/dashboard.store';

describe('useDashboardSSE', () => {
  let mockES: { close: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    useDashboardStore.setState({
      connectionStatus: 'disconnected',
      lastConnectedAt: null,
      snapshot: null,
      agents: [],
      ensemble: null,
      safety: null,
      regime: null,
      equity: [],
      watchlist: [],
      ticker: 'BTCUSDT',
      dashboardMode: 'LIVE',
      activeTab: 'overview',
      activeView: 'overview',
      sidebarCollapsed: false,
      mobileDrawerOpen: false,
      bottomPanelOpen: false,
      isMobile: false,
      latencyMs: 0,
      uptime: '--',
      lastUpdate: null,
    });

    mockES = { close: vi.fn() };

    function MockEventSource() {
      const es = { ...mockES };
      setTimeout(() => {
        if (typeof (es as any).onopen === 'function') (es as any).onopen();
      }, 0);
      return es;
    }

    vi.stubGlobal('EventSource', vi.fn().mockImplementation(MockEventSource));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('sets connection status to connected on open', async () => {
    const { useDashboardSSE } = await import('@/hooks/use-dashboard-sse');

    renderHook(() => useDashboardSSE());

    await waitFor(() => {
      expect(useDashboardStore.getState().connectionStatus).toBe('connected');
    });
  });

  it('closes EventSource on unmount', async () => {
    const { useDashboardSSE } = await import('@/hooks/use-dashboard-sse');

    const { unmount } = renderHook(() => useDashboardSSE());

    await waitFor(() => {
      expect(useDashboardStore.getState().connectionStatus).toBe('connected');
    });

    unmount();

    expect(mockES.close).toHaveBeenCalled();
    expect(useDashboardStore.getState().connectionStatus).toBe('disconnected');
  });

  it('processes snapshot SSE messages', async () => {
    const { useDashboardSSE } = await import('@/hooks/use-dashboard-sse');

    const { result } = renderHook(() => useDashboardSSE());

    // Simulate receiving a message
    await waitFor(() => {
      expect(useDashboardStore.getState().connectionStatus).toBe('connected');
    });

    // Use the EventSource instance to dispatch a message
    const esCalls = (globalThis.EventSource as unknown as ReturnType<typeof vi.fn>).mock;
    const instances = esCalls?.results?.map((r: { value: any }) => r.value) ?? [];
    const es = instances[instances.length - 1];

    if (es && typeof es.onmessage === 'function') {
      act(() => {
        es.onmessage({
          data: JSON.stringify({
            type: 'snapshot',
            payload: {
              agents: { quant: { agentId: 'quant', signal: 'BUY', confidence: 0.8, status: 'active' } },
              ensemble: { decision: 'BUY', confidence: 0.75 },
              safety: { status: 'ALLOWED', riskLevel: 'LOW' },
              regime: { id: 'bull', probability: 0.9 },
              equity: [{ timestamp: '2026-01-01', value: 10000 }],
              watchlist: [{ symbol: 'BTCUSDT', price: 50000 }],
              timestamp: new Date().toISOString(),
            },
            timestamp: new Date().toISOString(),
          }),
        });
      });
    }

    await waitFor(() => {
      const s = useDashboardStore.getState();
      expect(s.agents.length).toBeGreaterThan(0);
    });
  });
});
