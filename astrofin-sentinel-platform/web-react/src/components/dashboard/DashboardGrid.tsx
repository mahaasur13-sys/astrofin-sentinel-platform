import { useMemo, type ReactNode } from 'react';
import { WidgetState } from '@/components/ui/WidgetState';
import { useDashboardStore } from '@/stores/dashboard.store';

interface DashboardGridProps {
  children?: ReactNode;
}

interface WidgetSlot {
  id: string;
  colSpan: 'full' | 'half' | 'third';
  isLoading: boolean;
  error: string | null;
  onRetry?: () => void;
  content: ReactNode;
}

export function DashboardGrid({ children }: DashboardGridProps) {
  const snapshot = useDashboardStore((s) => s.snapshot);
  const agentsError = !snapshot ? 'No data available' : null;

  const widgets: WidgetSlot[] = useMemo(() => {
    if (!children) return [];
    const childArr = Array.isArray(children) ? children : [children];
    return childArr
      .filter(Boolean)
      .map((child, i) => ({
        id: `widget-${i}`,
        colSpan: (i === 0 ? 'full' : i <= 3 ? 'half' : 'third') as WidgetSlot['colSpan'],
        isLoading: false,
        error: agentsError,
        content: child,
      }));
  }, [children, agentsError]);

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4" role="main">
      {widgets.map((widget) => (
        <div
          key={widget.id}
          className={
            widget.colSpan === 'full'
              ? 'sm:col-span-2 lg:col-span-3 xl:col-span-4'
              : widget.colSpan === 'half'
                ? 'lg:col-span-2'
                : ''
          }
        >
          <WidgetState
            isLoading={widget.isLoading}
            error={widget.error}
            onRetry={widget.onRetry}
            loadingRows={widget.colSpan === 'full' ? 2 : 1}
          >
            <div className="rounded-xl border border-border bg-card p-3 sm:p-4">
              {widget.content}
            </div>
          </WidgetState>
        </div>
      ))}
    </div>
  );
}
