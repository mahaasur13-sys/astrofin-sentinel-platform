import { useRef, useMemo } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';

interface AgentPerformance {
  id: string;
  name: string;
  weight: number;
  signal: 'buy' | 'sell' | 'hold' | 'strong_buy' | 'strong_sell';
  confidence: number;
  winRate: number;
  sharpe: number;
  pnl: number;
  status: 'active' | 'idle' | 'error';
  lastRun: string;
}

interface VirtualAgentGridProps {
  agents: AgentPerformance[];
  onRunAgent?: (id: string) => void;
  rowHeight?: number;
}

export function VirtualAgentGrid({ agents, onRunAgent, rowHeight = 48 }: VirtualAgentGridProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  const sorted = useMemo(() => [...agents].sort((a, b) => b.weight - a.weight), [agents]);

  const virtualizer = useVirtualizer({
    count: sorted.length,
    getScrollElement: () => containerRef.current,
    estimateSize: () => rowHeight,
    overscan: 5,
  });

  return (
    <div ref={containerRef} className="h-[400px] overflow-auto rounded-lg border border-border">
      <div style={{ height: virtualizer.getTotalSize(), position: 'relative' }}>
        {virtualizer.getVirtualItems().map((virtualRow) => {
          const agent = sorted[virtualRow.index];
          return (
            <div
              key={agent.id}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: virtualRow.size,
                transform: `translateY(${virtualRow.start}px)`,
              }}
              className="flex items-center gap-2 border-b border-border px-3 text-sm hover:bg-muted/50"
            >
              <span className="w-28 truncate font-mono text-xs text-foreground">{agent.name}</span>
              <span className="w-10 text-right text-xs text-muted-foreground">{agent.weight}%</span>
              <span
                className={`inline-flex min-w-[72px] justify-center rounded-full px-1.5 py-0.5 text-[10px] font-semibold ${
                  agent.signal.includes('buy') ? 'bg-emerald-500/15 text-emerald-400' :
                  agent.signal.includes('sell') ? 'bg-red-500/15 text-red-400' :
                  'bg-gray-500/15 text-gray-400'
                }`}
              >
                {agent.signal.toUpperCase()}
              </span>
              <span className="w-14 text-right text-xs text-muted-foreground">{agent.confidence}%</span>
              <span className="w-14 text-right text-xs text-muted-foreground">{agent.winRate}%</span>
              <span className={`ml-auto inline-flex h-1.5 w-1.5 rounded-full ${
                agent.status === 'active' ? 'bg-emerald-400' :
                agent.status === 'idle' ? 'bg-yellow-400' : 'bg-red-400'
              }`} />
              {onRunAgent && (
                <button
                  type="button"
                  onClick={() => onRunAgent(agent.id)}
                  className="ml-2 rounded bg-primary/10 px-2 py-0.5 text-[10px] text-primary hover:bg-primary/20"
                >
                  Run
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
