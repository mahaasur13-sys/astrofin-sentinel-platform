import { useMemo } from 'react';
import { memo } from "react";

type Regime = 'bull' | 'bear' | 'sideways' | 'high_vol' | 'anomaly';

interface EquityPoint {
  date: string;
  equity: number;
  regime: Regime;
}

interface EquityCurveProps {
  data: EquityPoint[];
  height?: number;
}

const REGIME_COLORS: Record<Regime, string> = {
  bull: 'rgba(0, 255, 157, 0.15)',
  bear: 'rgba(255, 45, 85, 0.15)',
  sideways: 'rgba(0, 184, 255, 0.08)',
  high_vol: 'rgba(255, 208, 0, 0.12)',
  anomaly: 'rgba(255, 42, 109, 0.18)',
};

export default function EquityCurve({ data, height = 260 }: EquityCurveProps) {
  const { path, regimeBands, minEq, maxEq, yRange } = useMemo(() => {
    if (data.length < 2) return { path: '', regimeBands: [], minEq: 0, maxEq: 1, yRange: 1 };

    const eqValues = data.map((d) => d.equity);
    const min = Math.min(...eqValues);
    const max = Math.max(...eqValues);
    const range = max - min || 1;

    const w = 1000;
    const h = 200;
    const padding = 10;
    const plotH = h - padding * 2;

    const scaleX = (i: number) => padding + (i / (data.length - 1)) * (w - padding * 2);
    const scaleY = (v: number) => padding + (1 - (v - min) / range) * plotH;

    const pathPoints = data.map((d, i) => `${i === 0 ? 'M' : 'L'} ${scaleX(i).toFixed(1)} ${scaleY(d.equity).toFixed(1)}`);
    const polyPoints = data.map((d, i) => `${scaleX(i).toFixed(1)},${scaleY(d.equity).toFixed(1)}`);

    const bands: Array<{ x: number; w: number; color: string }> = [];
    let currentRegime = data[0].regime;
    let bandStart = 0;

    for (let i = 1; i <= data.length; i++) {
      if (i === data.length || data[i].regime !== currentRegime) {
        bands.push({
          x: scaleX(bandStart),
          w: scaleX(i - 1) - scaleX(bandStart),
          color: REGIME_COLORS[currentRegime],
        });
        if (i < data.length) {
          currentRegime = data[i].regime;
          bandStart = i;
        }
      }
    }

    return { path: pathPoints.join(' '), regimeBands: bands, minEq: min, maxEq: max, yRange: range };
  }, [data]);

  const startEq = data[0]?.equity ?? 0;
  const endEq = data[data.length - 1]?.equity ?? 0;
  const pnl = endEq - startEq;
  const pnlPct = startEq ? ((pnl / startEq) * 100) : 0;

  return (
    <div className="glass-panel" style={{ padding: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h3 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: 1 }}>
          Equity Curve
        </h3>
        <div style={{ display: 'flex', gap: 16 }}>
          <span className="mono-value" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Start: ${startEq.toFixed(0)}
          </span>
          <span className="mono-value" style={{ fontSize: '0.8rem', fontWeight: 600, color: pnl >= 0 ? 'var(--bull)' : 'var(--bear)' }}>
            {pnl >= 0 ? '+' : ''}{pnlPct.toFixed(2)}%
          </span>
        </div>
      </div>

      <div style={{ position: 'relative', height }}>
        <svg
          viewBox="0 0 1000 200"
          preserveAspectRatio="none"
          style={{ width: '100%', height: '100%' }}
        >
          {regimeBands.map((b, i) => (
            <rect key={i} x={b.x} y={0} width={b.w} height={200} fill={b.color} />
          ))}

          <path
            d={path}
            fill="none"
            stroke="var(--accent)"
            strokeWidth={2}
            strokeLinejoin="round"
            strokeLinecap="round"
          />

          <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.3} />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity={0.02} />
          </linearGradient>

          <path
            d={`${path} L 990 200 L 10 200 Z`}
            fill="url(#eqGrad)"
          />
        </svg>

        <div style={{
          position: 'absolute',
          bottom: 8,
          left: 0,
          right: 0,
          display: 'flex',
          justifyContent: 'center',
          gap: 14,
          fontSize: '0.65rem',
        }}>
          {(['bull', 'bear', 'sideways', 'high_vol', 'anomaly'] as Regime[]).map((r) => (
            <span key={r} style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--text-muted)' }}>
              <span style={{
                width: 10, height: 10, borderRadius: 3,
                background: REGIME_COLORS[r].replace('0.1', '0.6').replace('0.08', '0.5').replace('0.12', '0.6').replace('0.18', '0.7'),
              }} />
              {r.replace('_', ' ').toUpperCase()}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

