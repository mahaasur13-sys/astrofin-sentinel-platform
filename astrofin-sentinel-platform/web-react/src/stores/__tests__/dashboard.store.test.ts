import { describe, it, expect, beforeEach } from 'vitest';
import { useDashboardStore } from '@/stores/dashboard.store';

describe('dashboardStore', () => {
  beforeEach(() => {
    useDashboardStore.getState().reset();
  });

  describe('initial state', () => {
    it('should have disconnected status', () => {
      const { connectionStatus } = useDashboardStore.getState();
      expect(connectionStatus).toBe('disconnected');
    });

    it('should have default ticker BTCUSDT', () => {
      expect(useDashboardStore.getState().ticker).toBe('BTCUSDT');
    });

    it('should have LIVE mode', () => {
      expect(useDashboardStore.getState().dashboardMode).toBe('LIVE');
    });

    it('should have empty agents array', () => {
      expect(useDashboardStore.getState().agents).toEqual([]);
    });

    it('should have empty equity array', () => {
      expect(useDashboardStore.getState().equity).toEqual([]);
    });

    it('should have sidebar not collapsed', () => {
      expect(useDashboardStore.getState().sidebarCollapsed).toBe(false);
    });

    it('should have mobileDrawer not open', () => {
      expect(useDashboardStore.getState().mobileDrawerOpen).toBe(false);
    });

    it('should have default activeView overview', () => {
      expect(useDashboardStore.getState().activeView).toBe('overview');
    });
  });

  describe('actions', () => {
    it('should set connection status', () => {
      useDashboardStore.getState().setConnectionStatus('connected');
      expect(useDashboardStore.getState().connectionStatus).toBe('connected');
    });

    it('should set ticker', () => {
      useDashboardStore.getState().setTicker('ETHUSDT');
      expect(useDashboardStore.getState().ticker).toBe('ETHUSDT');
    });

    it('should toggle sidebar', () => {
      expect(useDashboardStore.getState().sidebarCollapsed).toBe(false);
      useDashboardStore.getState().toggleSidebar();
      expect(useDashboardStore.getState().sidebarCollapsed).toBe(true);
      useDashboardStore.getState().toggleSidebar();
      expect(useDashboardStore.getState().sidebarCollapsed).toBe(false);
    });

    it('should set active view and close drawer', () => {
      useDashboardStore.getState().setMobileDrawerOpen(true);
      useDashboardStore.getState().setActiveView('agents');
      expect(useDashboardStore.getState().activeView).toBe('agents');
      expect(useDashboardStore.getState().mobileDrawerOpen).toBe(false);
    });

    it('should set dashboard mode', () => {
      useDashboardStore.getState().setDashboardMode('BACKTEST');
      expect(useDashboardStore.getState().dashboardMode).toBe('BACKTEST');
    });

    it('should set latency and uptime', () => {
      useDashboardStore.getState().setLatencyMs(42);
      useDashboardStore.getState().setUptime('03:14:15');
      expect(useDashboardStore.getState().latencyMs).toBe(42);
      expect(useDashboardStore.getState().uptime).toBe('03:14:15');
    });

    it('should reset to initial state', () => {
      useDashboardStore.getState().setTicker('XRPUSDT');
      useDashboardStore.getState().setConnectionStatus('connected');
      useDashboardStore.getState().setActiveView('agents');
      useDashboardStore.getState().reset();
      expect(useDashboardStore.getState().ticker).toBe('BTCUSDT');
      expect(useDashboardStore.getState().connectionStatus).toBe('disconnected');
      expect(useDashboardStore.getState().activeView).toBe('overview');
    });
  });

  describe('selectors', () => {
    it('should select connection status', () => {
      const status = useDashboardStore.getState().connectionStatus;
      expect(['connected', 'disconnected', 'connecting', 'error']).toContain(status);
    });

    it('should select active view', () => {
      useDashboardStore.getState().setActiveView('radar');
      expect(useDashboardStore.getState().activeView).toBe('radar');
    });

    it('should select isMobile flag', () => {
      useDashboardStore.getState().setIsMobile(true);
      expect(useDashboardStore.getState().isMobile).toBe(true);
    });
  });
});
