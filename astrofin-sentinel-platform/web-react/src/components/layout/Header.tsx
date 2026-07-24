import type { ReactNode } from 'react';
import { Activity, Menu, PanelLeftClose, PanelLeft } from 'lucide-react';
import type { ConnectionStatus } from '@/types';

interface HeaderProps {
  connectionStatus: ConnectionStatus;
  latencyMs: number;
  activeView: string;
  isMobile: boolean;
  onMenuToggle: () => void;
  children?: ReactNode;
}

export function Header({ connectionStatus, latencyMs, activeView, isMobile, onMenuToggle }: HeaderProps) {
  const sidebarCollapsed = false;

  return (
    <header className="flex h-12 shrink-0 items-center gap-3 border-b border-border bg-card px-3 sm:px-4" role="banner">
      {/* Mobile hamburger */}
      <button
        onClick={onMenuToggle}
        className="inline-flex items-center justify-center rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground lg:hidden"
        aria-label="Toggle navigation menu"
      >
        <Menu className="size-5" />
      </button>

      {/* Desktop collapse toggle */}
      <button
        onClick={onMenuToggle}
        className="hidden items-center justify-center rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground lg:inline-flex"
        aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {sidebarCollapsed ? <PanelLeft className="size-4" /> : <PanelLeftClose className="size-4" />}
      </button>

      <div className="flex items-center gap-2">
        <Activity className="size-5 text-primary" />
        <span className="hidden text-sm font-semibold sm:inline">AstroFin</span>
        <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-primary">
          {activeView}
        </span>
      </div>

      <div className="ml-auto flex items-center gap-2 sm:gap-3">
        {latencyMs > 0 && (
          <span className="hidden text-xs text-muted-foreground sm:inline">{latencyMs}ms</span>
        )}
        <div className="flex items-center gap-1.5">
          <span
            className={`size-2 rounded-full ${
              connectionStatus === 'connected'
                ? 'bg-green-500'
                : connectionStatus === 'connecting'
                  ? 'bg-yellow-500'
                  : 'bg-red-500/60'
            }`}
            aria-label={`Connection status: ${connectionStatus}`}
          />
          <span className="hidden text-xs text-muted-foreground sm:inline">
            {connectionStatus}
          </span>
        </div>
      </div>
    </header>
  );
}
