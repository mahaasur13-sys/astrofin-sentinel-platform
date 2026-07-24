import { useDashboardStore } from '@/stores/dashboard.store';

export function StatusBar() {
  const connectionStatus = useDashboardStore((s) => s.connectionStatus);
  const latencyMs = useDashboardStore((s) => s.latencyMs);
  const uptime = useDashboardStore((s) => s.uptime);
  const lastUpdate = useDashboardStore((s) => s.lastUpdate);
  const dashboardMode = useDashboardStore((s) => s.dashboardMode);
  const agents = useDashboardStore((s) => s.agents);

  const dotColor =
    connectionStatus === 'connected'
      ? 'text-emerald-500'
      : connectionStatus === 'connecting'
        ? 'text-amber-500'
        : 'text-red-500';

  return (
    <footer
      className="zone-footer flex shrink-0 items-center justify-between px-2 py-1 text-[10px] text-gray-500 sm:px-4 sm:py-1.5 sm:text-[11px]"
      role="contentinfo"
      aria-label="Строка состояния"
    >
      <div className="flex items-center gap-2 sm:gap-4 flex-wrap">
        <span>
          <span className="hidden sm:inline">Mode: </span>
          <span className="font-mono text-gray-300">{dashboardMode}</span>
        </span>
        <span>
          <span className="hidden sm:inline">Agents: </span>
          <span className="font-mono text-gray-300">{agents.length}</span>
        </span>
        <span className="hidden sm:inline">
          Latency:{' '}
          <span className="font-mono text-gray-300">{latencyMs}ms</span>
        </span>
      </div>

      <div className="flex items-center gap-2 sm:gap-4 flex-wrap">
        <span className="hidden sm:inline">
          Uptime:{' '}
          <span className="font-mono text-gray-300">{uptime}</span>
        </span>
        {lastUpdate && (
          <span>
            <span className="hidden sm:inline">Updated: </span>
            <span className="font-mono text-gray-300">
              {new Date(lastUpdate).toLocaleTimeString()}
            </span>
          </span>
        )}
        <span className={`font-mono uppercase ${dotColor}`} aria-live="polite">
          ● {connectionStatus}
        </span>
      </div>
    </footer>
  );
}
