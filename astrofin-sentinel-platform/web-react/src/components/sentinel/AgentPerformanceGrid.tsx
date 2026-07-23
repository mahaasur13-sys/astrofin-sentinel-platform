import { useState, useMemo } from 'react';

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

interface AgentPerformanceGridProps {
  agents: AgentPerformance[];
  onRunAgent?: (id: string) => void;
}

type SortKey = keyof AgentPerformance;
type SortDir = 'asc' | 'desc';

export default function AgentPerformanceGrid({ agents, onRunAgent }: AgentPerformanceGridProps) {
  const [sortKey, setSortKey] = useState<SortKey>('weight');
  const [sortDir, setSortDir] = useState<SortDir>('desc');

  const sorted = useMemo(() => {
    return [...agents].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDir === 'desc' ? bVal - aVal : aVal - bVal;
      }
      return sortDir === 'desc'
        ? String(bVal).localeCompare(String(aVal))
        : String(aVal).localeCompare(String(bVal));
    });
  }, [agents, sortKey, sortDir]);

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir((d) => (d === 'desc' ? 'asc' : 'desc'));
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const SortIcon = ({ active, dir }: { active: boolean; dir: SortDir }) => (
    <span style={{ opacity: active ? 1 : 0.3, fontSize: '0.65rem' }}>
      {active ? (dir === 'desc' ? ' ▼' : ' ▲') : ' ⇅'}
    </span>
  );

  return (
    <div className="glass-panel" style={{ overflow: 'hidden' }}>
      <div style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: 1 }}>
          Agent Performance — {agents.length} agents
        </h3>
        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
          Click column to sort
        </span>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)', borderTop: '1px solid var(--border)' }}>
              <Th onClick={() => handleSort('name')}>Agent <SortIcon active={sortKey === 'name'} dir={sortDir} /></Th>
              <Th onClick={() => handleSort('signal')}>Signal <SortIcon active={sortKey === 'signal'} dir={sortDir} /></Th>
              <Th onClick={() => handleSort('confidence')}>Conf <SortIcon active={sortKey === 'confidence'} dir={sortDir} /></Th>
              <Th onClick={() => handleSort('weight')}>Weight <SortIcon active={sortKey === 'weight'} dir={sortDir} /></Th>
              <Th onClick={() => handleSort('winRate')}>Win% <SortIcon active={sortKey === 'winRate'} dir={sortDir} /></Th>
              <Th onClick={() => handleSort('sharpe')}>Sharpe <SortIcon active={sortKey === 'sharpe'} dir={sortDir} /></Th>
              <Th onClick={() => handleSort('pnl')}>PnL% <SortIcon active={sortKey === 'pnl'} dir={sortDir} /></Th>
              <Th onClick={() => handleSort('status')}>Status <SortIcon active={sortKey === 'status'} dir={sortDir} /></Th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((agent) => (
              <tr
                key={agent.id}
                style={{ borderBottom: '1px solid rgba(30, 30, 46, 0.6)', transition: 'background 0.15s' }}
                onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--bg-hover)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
              >
                <Td>
                  <div style={{ fontWeight: 600 }}>{agent.name}</div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{agent.lastRun}</div>
                </Td>
                <Td>
                  <span className={`signal-badge signal-badge-${agent.signal}`}>
                    {agent.signal.replace('_', ' ').toUpperCase()}
                  </span>
                </Td>
                <Td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <div style={{ flex: 1, background: 'var(--bg-primary)', borderRadius: 3, height: 4 }}>
                      <div style={{
                        width: `${agent.confidence * 100}%`,
                        height: '100%',
                        background: `linear-gradient(90deg, var(--accent), transparent)`,
                        borderRadius: 3,
                      }} />
                    </div>
                    <span className="mono-value" style={{ fontSize: '0.72rem', minWidth: 36, textAlign: 'right' }}>
                      {(agent.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </Td>
                <Td className="mono-value" style={{ color: 'var(--accent)' }}>{(agent.weight * 100).toFixed(0)}%</Td>
                <Td className="mono-value">{agent.winRate.toFixed(0)}%</Td>
                <Td className="mono-value" style={{ color: agent.sharpe >= 1 ? 'var(--bull)' : agent.sharpe >= 0 ? 'var(--text-primary)' : 'var(--bear)' }}>
                  {agent.sharpe.toFixed(2)}
                </Td>
                <Td className="mono-value" style={{ color: agent.pnl >= 0 ? 'var(--bull)' : 'var(--bear)' }}>
                  {agent.pnl >= 0 ? '+' : ''}{agent.pnl.toFixed(1)}%
                </Td>
                <Td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{
                      width: 7, height: 7, borderRadius: '50%',
                      background: agent.status === 'active' ? 'var(--bull)' : agent.status === 'error' ? 'var(--bear)' : 'var(--text-muted)',
                    }} />
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{agent.status}</span>
                    {onRunAgent && (
                      <button
                        onClick={() => onRunAgent(agent.id)}
                        style={{
                          marginLeft: 'auto',
                          padding: '2px 8px',
                          background: 'transparent',
                          border: '1px solid var(--accent)',
                          borderRadius: 4,
                          color: 'var(--accent)',
                          fontSize: '0.65rem',
                          cursor: 'pointer',
                        }}
                      >
                        Run
                      </button>
                    )}
                  </div>
                </Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Th({ onClick, children }: { onClick: () => void; children: React.ReactNode }) {
  return (
    <th
      onClick={onClick}
      style={{
        padding: '10px 14px',
        textAlign: 'left',
        fontWeight: 600,
        fontSize: '0.7rem',
        color: 'var(--text-secondary)',
        textTransform: 'uppercase',
        letterSpacing: 0.5,
        cursor: 'pointer',
        userSelect: 'none',
        whiteSpace: 'nowrap',
      }}
    >
      {children}
    </th>
  );
}

function Td({ children, style, className }: { children: React.ReactNode; style?: React.CSSProperties; className?: string }) {
  return (
    <td style={{ padding: '10px 14px', ...style }}>
      {children}
    </td>
  );
}
export { AgentPerformanceGrid };
