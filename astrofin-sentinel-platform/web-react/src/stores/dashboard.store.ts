import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type {
  AgentLive, DashboardSnapshot, EnsembleResult,
  SafetyGate, Regime, EquityPoint, WatchlistItem, ConnectionStatus,
} from '@/types';

interface DashboardState {
  connectionStatus: ConnectionStatus;
  lastConnectedAt: string | null;
  snapshot: DashboardSnapshot | null;
  agents: AgentLive[];
  ensemble: EnsembleResult | null;
  safety: SafetyGate | null;
  regime: Regime | null;
  equity: EquityPoint[];
  watchlist: WatchlistItem[];
  ticker: string;
  dashboardMode: 'LIVE' | 'BACKTEST' | 'PAPER' | 'OPTIMIZE';
  activeTab: string;
  activeView: string;
  sidebarCollapsed: boolean;
  mobileDrawerOpen: boolean;
  bottomPanelOpen: boolean;
  isMobile: boolean;
  latencyMs: number;
  uptime: string;
  lastUpdate: string | null;

  setConnectionStatus: (status: ConnectionStatus) => void;
  setLastConnectedAt: (ts: string) => void;
  setSnapshot: (snapshot: DashboardSnapshot) => void;
  setAgents: (agents: AgentLive[]) => void;
  setEnsemble: (ensemble: EnsembleResult) => void;
  setSafety: (safety: SafetyGate) => void;
  setRegime: (regime: Regime) => void;
  setEquity: (equity: EquityPoint[]) => void;
  setWatchlist: (watchlist: WatchlistItem[]) => void;
  setTicker: (ticker: string) => void;
  setDashboardMode: (mode: DashboardState['dashboardMode']) => void;
  setActiveTab: (tab: string) => void;
  setLatencyMs: (ms: number) => void;
  setUptime: (uptime: string) => void;
  setLastUpdate: (ts: string) => void;
  toggleSidebar: () => void;
  setActiveView: (view: string) => void;
  setMobileDrawerOpen: (open: boolean) => void;
  setBottomPanelOpen: (open: boolean) => void;
  setIsMobile: (mobile: boolean) => void;
  reset: () => void;
}

const initialState = {
  connectionStatus: 'disconnected' as ConnectionStatus,
  lastConnectedAt: null as string | null,
  snapshot: null as DashboardSnapshot | null,
  agents: [] as AgentLive[],
  ensemble: null as EnsembleResult | null,
  safety: null as SafetyGate | null,
  regime: null as Regime | null,
  equity: [] as EquityPoint[],
  watchlist: [] as WatchlistItem[],
  ticker: 'BTCUSDT',
  dashboardMode: 'LIVE' as const,
  activeTab: 'overview',
  activeView: 'overview',
  sidebarCollapsed: false,
  mobileDrawerOpen: false,
  bottomPanelOpen: false,
  isMobile: false,
  latencyMs: 0,
  uptime: '--',
  lastUpdate: null as string | null,
};

export const useDashboardStore = create<DashboardState>()(
  devtools(
    (set) => ({
      ...initialState,

      setConnectionStatus: (status) =>
        set({ connectionStatus: status }, false, 'connection/status'),

      setLastConnectedAt: (ts) =>
        set({ lastConnectedAt: ts }, false, 'connection/lastConnected'),

      setSnapshot: (snapshot) =>
        set({ snapshot }, false, 'data/snapshot'),

      setAgents: (agents) =>
        set({ agents }, false, 'data/agents'),

      setEnsemble: (ensemble) =>
        set({ ensemble }, false, 'data/ensemble'),

      setSafety: (safety) =>
        set({ safety }, false, 'data/safety'),

      setRegime: (regime) =>
        set({ regime }, false, 'data/regime'),

      setEquity: (equity) =>
        set({ equity }, false, 'data/equity'),

      setWatchlist: (watchlist) =>
        set({ watchlist }, false, 'data/watchlist'),

      setTicker: (ticker) =>
        set({ ticker }, false, 'ui/ticker'),

      setDashboardMode: (dashboardMode) =>
        set({ dashboardMode }, false, 'ui/mode'),

      setActiveTab: (activeTab) =>
        set({ activeTab }, false, 'ui/tab'),

      setLatencyMs: (latencyMs) =>
        set({ latencyMs }, false, 'metrics/latency'),

      setUptime: (uptime) =>
        set({ uptime }, false, 'metrics/uptime'),

      setLastUpdate: (lastUpdate) =>
        set({ lastUpdate }, false, 'metrics/lastUpdate'),

      toggleSidebar: () =>
        set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed }), false, 'ui/sidebar'),

      setActiveView: (activeView) =>
        set({ activeView, mobileDrawerOpen: false }, false, 'ui/activeView'),

      setMobileDrawerOpen: (open) =>
        set({ mobileDrawerOpen: open }, false, 'ui/mobileDrawer'),

      setBottomPanelOpen: (open) =>
        set({ bottomPanelOpen: open }, false, 'ui/bottomPanel'),

      setIsMobile: (isMobile) =>
        set({ isMobile }, false, 'ui/isMobile'),

      reset: () => set(initialState, false, 'data/reset'),
    }),
    { name: 'dashboard-store' },
  ),
);
