import { useMemo } from 'react';

type Regime = 'bull' | 'bear' | 'sideways' | 'high_vol' | 'anomaly';


interface RegimeRadarProps {
  probabilities: Record<Regime, number>;
  currentRegime: Regime;
  compact?: boolean;
}

const REGIME_META: Record<Regime, { label: string; color: string; description: string }> = {
  bull: { label: 'BULL', color: 'var(--bull)', description: 'Бычий тренд' },
  bear: { label: 'BEAR', color: 'var(--bear)', description: 'Медвежий тренд' },
  sideways: { label: 'SIDEWAYS', color: 'var(--sideways)', description: 'Флэт / Боковик' },
  high_vol: { label: 'HIGH VOL', color: 'var(--high-vol)', description: 'Высокая волатильность' },
  anomaly: { label: 'ANOMALY', color: 'var(--anomaly)', description: 'Аномалия рынка' },
};

function DonutSegment({
  cx,
  cy,
  r,
  innerR,
  startAngle,
  endAngle,
  color,
}: {
  cx: number; cy: number; r: number; innerR: number;
  startAngle: number; endAngle: number; color: string;
}) {
  if (endAngle - startAngle < 0.001) return null;
  const outerStartX = cx + r * Math.cos(startAngle);
  const outerStartY = cy + r * Math.sin(startAngle);
  const outerEndX = cx + r * Math.cos(endAngle);
  const outerEndY = cy + r * Math.sin(endAngle);
  const innerStartX = cx + innerR * Math.cos(startAngle);
  const innerStartY = cy + innerR * Math.sin(startAngle);
  const innerEndX = cx + innerR * Math.cos(endAngle);
  const innerEndY = cy + innerR * Math.sin(endAngle);
  const largeArc = endAngle - startAngle > Math.PI ? 1 : 0;

  return (
    <path
      d={`M ${outerStartX.toFixed(2)} ${outerStartY.toFixed(2)}
          A ${r} ${r} 0 ${largeArc} 1 ${outerEndX.toFixed(2)} ${outerEndY.toFixed(2)}
          L ${innerEndX.toFixed(2)} ${innerEndY.toFixed(2)}
          A ${innerR} ${innerR} 0 ${largeArc} 0 ${innerStartX.toFixed(2)} ${innerStartY.toFixed(2)}
          Z`}
      fill={color}
      opacity={0.85}
      stroke="var(--bg-panel)"
      strokeWidth={1.5}
    />
  );
}

export default function RegimeRadar({ probabilities, currentRegime, compact = false }: RegimeRadarProps) {
  const size = compact ? 180 : 280;
  const cx = size / 2;
  const cy = size / 2;
  const r = compact ? 70 : 110;
  const innerR = compact ? 40 : 65;

  const segments = useMemo(() => {
    const entries = Object.entries(probabilities) as [Regime, number][];
    const total = entries.reduce((sum, [, p]) => sum + p, 0) || 1;
    let currentAngle = -Math.PI / 2;

    return entries.map(([regime, prob]) => {
      const startAngle = currentAngle;
      const sweep = (prob / total) * 2 * Math.PI;
      currentAngle += sweep;
      return { regime, startAngle, endAngle: currentAngle, prob, color: REGIME_META[regime].color };
    });
  }, [probabilities]);

  const currentMeta = REGIME_META[currentRegime];
  const currentProb = probabilities[currentRegime];

  const bars = (Object.entries(probabilities) as [Regime, number][])
    .sort(([, a], [, b]) => b - a);

  if (compact) {
    return (
      <div className="glass-card" style={{ padding: 12, textAlign: 'center' }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {segments.map((seg) => (
            <DonutSegment
              key={seg.regime}
              cx={cx} cy={cy} r={r} innerR={innerR}
              startAngle={seg.startAngle} endAngle={seg.endAngle} color={seg.color}
            />
          ))}
          <text x={cx} y={cy - 6} textAnchor="middle" fill="var(--text-primary)" fontSize={18} fontWeight={700}>
            {currentMeta.label}
          </text>
          <text x={cx} y={cy + 14} textAnchor="middle" fill="var(--text-secondary)" fontSize={12}>
            {(currentProb * 100).toFixed(0)}%
          </text>
        </svg>
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ padding: 20 }}>
      <h3 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 16, textTransform: 'uppercase', letterSpacing: 1 }}>
        Regime Radar — HMM
      </h3>
      <div style={{ display: 'flex', gap: 24, alignItems: 'center' }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {segments.map((seg) => (
            <DonutSegment
              key={seg.regime}
              cx={cx} cy={cy} r={r} innerR={innerR}
              startAngle={seg.startAngle} endAngle={seg.endAngle} color={seg.color}
            />
          ))}
          <text x={cx} y={cy - 10} textAnchor="middle" fill="var(--text-primary)" fontSize={28} fontWeight={700}>
            {currentMeta.label}
          </text>
          <text x={cx} y={cy + 14} textAnchor="middle" fill={currentMeta.color} fontSize={20} fontWeight={600}>
            {(currentProb * 100).toFixed(0)}%
          </text>
        </svg>

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 10 }}>
          {bars.map(([regime, prob]) => {
            const meta = REGIME_META[regime];
            const isCurrent = regime === currentRegime;
            return (
              <div key={regime} style={{ opacity: isCurrent ? 1 : 0.5 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: isCurrent ? 700 : 400, color: meta.color }}>
                    {meta.label}
                    {isCurrent && ' ◀'}
                  </span>
                  <span className="mono-value" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                    {(prob * 100).toFixed(0)}%
                  </span>
                </div>
                <div style={{ background: 'var(--bg-primary)', borderRadius: 4, height: 6, overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${Math.max(prob * 100, 2)}%`,
                      height: '100%',
                      background: `linear-gradient(90deg, ${meta.color}, transparent)`,
                      borderRadius: 4,
                      transition: 'width 0.6s ease',
                    }}
                  />
                </div>
              </div>
            );
          })}
          <div style={{ marginTop: 4, fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            {currentMeta.description} · confidence {(currentProb * 100).toFixed(0)}%
          </div>
        </div>
      </div>
    </div>
  );
}
