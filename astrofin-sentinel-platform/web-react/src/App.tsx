import { useCallback, useEffect } from 'react';
import { useDashboardStore } from '@/stores/dashboard.store';
import { useDashboardSSE } from '@/hooks/use-dashboard-sse';
import { ErrorBoundary } from '@/components/shared/ErrorBoundary';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { StatusBar } from '@/components/layout/StatusBar';
import { DashboardGrid } from '@/components/dashboard/DashboardGrid';
import AstroMindChat from '@/components/astro/AstroMindChat';
import { X, ChevronUp } from 'lucide-react';

const MOBILE_BP = 1024;

function useMobileDetector(): boolean {
  const isMobile = useDashboardStore((s) => s.isMobile);
  const setIsMobile = useDashboardStore((s) => s.setIsMobile);

  useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BP - 1}px)`);
    const handler = (e: MediaQueryListEvent | MediaQueryList) => setIsMobile(e.matches);
    handler(mql);
    mql.addEventListener('change', handler);
    return () => mql.removeEventListener('change', handler);
  }, [setIsMobile]);

  return isMobile;
}

export function AppShell() {
  const {
    mobileDrawerOpen,
    bottomPanelOpen,
    activeView,
    isMobile,
    connectionStatus,
    latencyMs,
    setMobileDrawerOpen,
    setBottomPanelOpen,
  } = useDashboardStore((s) => ({
    mobileDrawerOpen: s.mobileDrawerOpen,
    bottomPanelOpen: s.bottomPanelOpen,
    activeView: s.activeView,
    isMobile: s.isMobile,
    connectionStatus: s.connectionStatus,
    latencyMs: s.latencyMs,
    setMobileDrawerOpen: s.setMobileDrawerOpen,
    setBottomPanelOpen: s.setBottomPanelOpen,
  }));

  useDashboardSSE();
  useMobileDetector();

  const toggleDrawer = useCallback(() => setMobileDrawerOpen(!mobileDrawerOpen), [mobileDrawerOpen, setMobileDrawerOpen]);
  const toggleBottom = useCallback(() => setBottomPanelOpen(!bottomPanelOpen), [bottomPanelOpen, setBottomPanelOpen]);

  return (
    <ErrorBoundary>
      <div className="flex h-screen flex-col bg-background text-foreground">
        <Header connectionStatus={connectionStatus} latencyMs={latencyMs} activeView={activeView} isMobile={isMobile} onMenuToggle={isMobile ? toggleDrawer : () => useDashboardStore.getState().toggleSidebar()} />

        <div className="flex flex-1 overflow-hidden">
          {isMobile ? (
            <Sidebar isOpen={mobileDrawerOpen} onClose={() => setMobileDrawerOpen(false)} />
          ) : (
            <Sidebar />
          )}

          <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
            <div className="flex-1 overflow-y-auto px-2 py-2 sm:px-4 sm:py-3">
              <ErrorBoundary>
                <DashboardGrid />
              </ErrorBoundary>
            </div>

            {isMobile ? (
              <>
                <button
                  type="button"
                  onClick={toggleBottom}
                  className="flex items-center justify-center gap-1.5 border-t border-border bg-card py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted sm:hidden"
                  aria-expanded={bottomPanelOpen}
                  aria-label="Toggle AstroMind panel"
                >
                  <ChevronUp className={`size-3.5 transition-transform ${bottomPanelOpen ? 'rotate-180' : ''}`} />
                  AstroMind
                </button>

                {bottomPanelOpen && (
                  <div className="fixed inset-x-0 bottom-0 z-50 max-h-[70vh] overflow-hidden rounded-t-xl border border-border bg-card shadow-2xl animate-slide-in">
                    <div className="flex items-center justify-between border-b border-border px-4 py-2">
                      <span className="text-xs font-semibold text-foreground">AstroMind</span>
                      <button
                        type="button"
                        onClick={() => setBottomPanelOpen(false)}
                        className="rounded-md p-1 text-muted-foreground hover:bg-muted"
                        aria-label="Close AstroMind"
                      >
                        <X className="size-4" />
                      </button>
                    </div>

                    <div className="h-[calc(70vh-44px)] overflow-y-auto p-3">
                      <ErrorBoundary>
                        <AstroMindChat variant="embedded" />
                      </ErrorBoundary>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <aside className="hidden w-80 shrink-0 border-l border-border bg-card p-3 lg:block" aria-label="AstroMind chat">
                <ErrorBoundary>
                  <AstroMindChat variant="embedded" />
                </ErrorBoundary>
              </aside>
            )}
          </main>
        </div>

        <StatusBar />
      </div>
    </ErrorBoundary>
  );
}

export default AppShell;
