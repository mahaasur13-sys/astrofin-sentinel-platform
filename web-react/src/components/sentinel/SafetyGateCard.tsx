import { useState } from 'react';

type SafetyStatus = 'safe' | 'warning' | 'danger' | 'stopped';

interface SafetyGateCardProps {
  status: SafetyStatus;
  reason?: string;
  riskPct: number;
  maxDrawdown: number;
  var95: number;
  leverage: number;
  triggers?: Array<{ time: string; reason: string }>;
}

const STATUS_META: Record<SafetyStatus, { label: string; color: string; glow: string; icon: string }> = {
  safe: { label: 'SAFE', color: 'var(--bull)', glow: 'neon-glow-bull', icon: '🟢' },
  warning: { label: 'WARNING', color: 'var(--high-vol)', glow: '', icon: '🟡' },
  danger: { label: 'DANGER', color: 'var(--bear)', glow: 'neon-glow-bear', icon: '🔴' },
  stopped: { label: 'STOPPED', color: 'var(--anomaly)', glow: 'emergency-pulse', icon: '⛔' },
};

export default function SafetyGateCard({
  status, reason, riskPct, maxDrawdown, var95, leverage, triggers = [],
}: SafetyGateCardProps) {
  const [emergency, setEmergency] = useState(status === 'stopped');
  const meta = STATUS_META[emergency ? 'stopped' : status];

  const handleEmergencyStop = () => {
    setEmergency(true);
  };

  const handleRelease = () => {
    setEmergency(false);
  };

  return (
    <div className={`glass-panel ${meta.glow}`} style={{ padding: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h3 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: 1 }}>
          Safety Gate
        </h3>
        <span style={{
          fontSize: '0.75rem',
          fontWeight: 700,
          color: meta.color,
          background: `${meta.color}15`,
          padding: '4px 10px',
          borderRadius: 20,
          border: `1px solid ${meta.color}30`,
        }}>
          {meta.icon} {meta.label}
        </span>
      </div>

      {reason && (
        <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: 14, lineHeight: 1.5 }}>
          {reason}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
        <MetricBox label="Risk %" value={`${riskPct.toFixed(1)}%`} color={riskPct > 2 ? 'var(--bear)' : 'var(--text-primary)'} />
        <MetricBox label="Max DD" value={`${maxDrawdown.toFixed(1)}%`} color={maxDrawdown > 10 ? 'var(--bear)' : 'var(--text-primary)'} />
        <MetricBox label="VaR 95" value={`${var95.toFixed(1)}%`} color="var(--high-vol)" />
        <MetricBox label="Leverage" value={`${leverage.toFixed(1)}×`} color={leverage > 2 ? 'var(--bear)' : 'var(--text-primary)'} />
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        {!emergency ? (
          <button
            onClick={handleEmergencyStop}
            className="emergency-pulse"
            style={{
              flex: 1,
              padding: '10px 16px',
              background: 'rgba(255, 42, 109, 0.15)',
              border: '1px solid var(--anomaly)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--anomaly)',
              fontWeight: 700,
              fontSize: '0.8rem',
              cursor: 'pointer',
              textTransform: 'uppercase',
              letterSpacing: 1,
              transition: 'background 0.2s',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255, 42, 109, 0.28)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255, 42, 109, 0.15)'; }}
          >
            ⚡ Emergency Stop
          </button>
        ) : (
          <button
            onClick={handleRelease}
            style={{
              flex: 1,
              padding: '10px 16px',
              background: 'rgba(0, 255, 157, 0.12)',
              border: '1px solid var(--bull)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--bull)',
              fontWeight: 700,
              fontSize: '0.8rem',
              cursor: 'pointer',
              textTransform: 'uppercase',
              letterSpacing: 1,
            }}
          >
            ✓ Release Stop
          </button>
        )}
      </div>

      {triggers.length > 0 && (
        <div style={{ marginTop: 14, borderTop: '1px solid var(--border)', paddingTop: 12 }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase' }}>
            Recent Triggers
          </div>
          {triggers.slice(0, 3).map((t, i) => (
            <div key={i} style={{ display: 'flex', gap: 8, fontSize: '0.72rem', marginBottom: 4 }}>
              <span className="mono-value" style={{ color: 'var(--text-muted)' }}>{t.time}</span>
              <span style={{ color: 'var(--text-secondary)' }}>{t.reason}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MetricBox({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="glass-card" style={{ padding: '10px 12px' }}>
      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 2 }}>{label}</div>
      <div className="mono-value" style={{ fontSize: '1.05rem', fontWeight: 600, color }}>{value}</div>
    </div>
  );
}
