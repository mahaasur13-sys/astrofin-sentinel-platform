import { create } from 'zustand';

type Theme = 'light' | 'dark';

interface UIState {
  sidebarOpen: boolean;
  rightPanelOpen: boolean;
  theme: Theme;
  activeSection: string;

  toggleSidebar: () => void;
  toggleRightPanel: () => void;
  setTheme: (t: Theme) => void;
  toggleTheme: () => void;
  setActiveSection: (s: string) => void;
}

function getSystemTheme(): Theme {
  try {
    if (typeof window !== 'undefined' && window.matchMedia) {
      return window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light';
    }
  } catch {
    // matchMedia unavailable — default to dark
  }
  return 'dark';
}

export const useUIStore = create<UIState>()((set) => ({
  sidebarOpen: true,
  rightPanelOpen: false,
  theme: getSystemTheme(),
  activeSection: 'overview',

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  toggleRightPanel: () => set((s) => ({ rightPanelOpen: !s.rightPanelOpen })),
  setTheme: (theme) => set({ theme }),
  toggleTheme: () => set((s) => ({ theme: s.theme === 'dark' ? 'light' : 'dark' })),
  setActiveSection: (activeSection) => set({ activeSection }),
}));
