import { useDashboardStore } from '@/stores/dashboard.store';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Users,
  History,
  Crosshair,
  Brain,
  TrendingUp,
  Settings,
  ChevronLeft,
  ChevronRight,
  X,
} from 'lucide-react';

const NAV_ITEMS: { id: string; label: string; Icon: typeof LayoutDashboard }[] = [
  { id: 'overview', label: 'Overview', Icon: LayoutDashboard },
  { id: 'agents', label: 'Agents', Icon: Users },
  { id: 'sessions', label: 'Sessions', Icon: History },
  { id: 'radar', label: 'Radar', Icon: Crosshair },
  { id: 'astromind', label: 'AstroMind', Icon: Brain },
  { id: 'pnl', label: 'P&L', Icon: TrendingUp },
  { id: 'settings', label: 'Settings', Icon: Settings },
];

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const sidebarCollapsed = useDashboardStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useDashboardStore((s) => s.toggleSidebar);
  const activeView = useDashboardStore((s) => s.activeView);
  const setActiveView = useDashboardStore((s) => s.setActiveView);

  return (
    <>
      {typeof isOpen === 'boolean' && isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside
        className={cn(
          'flex flex-col border-r border-white/10 bg-[#0c0c16] transition-all duration-300',
          typeof isOpen === 'boolean'
            ? cn(
                'fixed inset-y-0 left-0 z-50 w-64 lg:relative lg:z-0',
                isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
              )
            : sidebarCollapsed
              ? 'w-16'
              : 'w-56',
        )}
        role="navigation"
        aria-label="Main navigation"
      >
        <div className="flex items-center justify-between border-b border-white/10 px-3 py-3.5 lg:py-3">
          {sidebarCollapsed && typeof isOpen === 'undefined' ? null : (
            <span className="text-sm font-semibold text-gray-300 tracking-wide">
              Navigation
            </span>
          )}

          {typeof isOpen === 'boolean' ? (
            <button
              onClick={onClose}
              className="rounded-md p-1.5 text-gray-400 hover:bg-white/10 hover:text-white lg:hidden"
              aria-label="Close navigation menu"
            >
              <X className="size-4" aria-hidden="true" />
            </button>
          ) : (
            <button
              onClick={toggleSidebar}
              className="hidden lg:inline-flex rounded-md p-1 text-gray-500 hover:bg-white/10 hover:text-white"
              aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {sidebarCollapsed ? (
                <ChevronRight className="size-4" aria-hidden="true" />
              ) : (
                <ChevronLeft className="size-4" aria-hidden="true" />
              )}
            </button>
          )}
        </div>

        <nav className="flex-1 space-y-0.5 px-2 py-2">
          {NAV_ITEMS.map(({ id, label, Icon }) => {
            const isActive = activeView === id;
            return (
              <button
                key={id}
                onClick={() => setActiveView(id)}
                className={cn(
                  'flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-indigo-500/20 text-indigo-300'
                    : 'text-gray-400 hover:bg-white/5 hover:text-gray-200',
                )}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon
                  className={cn('size-4 shrink-0', isActive ? 'text-indigo-400' : 'text-gray-500')}
                  aria-hidden="true"
                />
                {(sidebarCollapsed && typeof isOpen === 'undefined') || sidebarCollapsed ? null : (
                  <span className="truncate">{label}</span>
                )}
              </button>
            );
          })}
        </nav>

        <div className="border-t border-white/10 px-3 py-3">
          {sidebarCollapsed && typeof isOpen === 'undefined' ? null : (
            <div className="flex items-center gap-1.5">
              <span className="size-1.5 rounded-full bg-emerald-400" aria-hidden="true" />
              <span className="text-xs text-gray-500">System online</span>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
