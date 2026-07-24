import { useEffect } from 'react';
import { useUIStore } from '@/stores/ui.store';

export function useTheme() {
  const theme = useUIStore((s) => s.theme);
  const setTheme = useUIStore((s) => s.setTheme);

  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle('dark', theme === 'dark');
    root.classList.toggle('light', theme === 'light');

    try {
      localStorage.setItem('astrofin-theme', theme);
    } catch {
      // localStorage unavailable — no persistence
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  return { theme, toggleTheme } as const;
}
