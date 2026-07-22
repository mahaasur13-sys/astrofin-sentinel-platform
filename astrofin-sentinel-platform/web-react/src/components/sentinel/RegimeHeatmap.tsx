'use client';

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import type { Regime } from './RegimeRadar';
import { REGIME_META } from './RegimeRadar';

export interface CorrelationCell {
  assetA: string;
  assetB: string;
  correlation: number;
  regime: Regime;
}

export interface RegimeHeatmapProps {
  data?: CorrelationCell[];
  assets?: string[];
  selectedRegime?: Regime;
  height?: number;
}

const ASSET_LIST = ['BTC', 'ETH', 'SPX', 'NDX', 'GOLD', 'OIL', 'EUR', 'JPY', 'TNX'];

function generateMockData(assets: string[], regime: Regime): CorrelationCell[] {
  const cells: CorrelationCell[] = [];
  const baseCorr: Record<Regime, number> = { bull: 0.3, bear: 0.6, sideways: 0.1, highvol: 0.7 };
  for (let i = 0; i < assets.length; i++) {
    for (let j = 0; j < assets.length; j++) {
      const base = baseCorr[regime];
      const corr = i === j ? 1 : base + (Math.random() - 0.5) * 0.5;
      cells.push({ assetA: assets[i], assetB: assets[j], correlation: Math.max(-1, Math.min(1, corr)), regime });
    }
  }
  return cells;
}

function corrToColor(corr: number): string {
  if (corr >= 0.8) return '#00ff9d';
  if (corr >= 0.5) return 'rgba(0,255,157,0.6)';
  if (corr >= 0.2) return 'rgba(0,255,157,0.25)';
  if (corr >= -0.2) return 'rgba(255,255,255,0.05)';
  if (corr >= -0.5) return 'rgba(255,45,85,0.25)';
  if (corr >= -0.8) return 'rgba(255,45,85,0.6)';
  return '#ff2d55';
}

export function RegimeHeatmap({ data, assets = ASSET_LIST, selectedRegime = 'bull', height = 280 }: RegimeHeatmapProps) {
  const heatmapData = useMemo(() => data ?? generateMockData(assets, selectedRegime), [data, assets, selectedRegime]);
  const cellSize = Math.floor(Math.min(28, (280 - 60) / assets.length));

  return (
    <div className="glass-card p-4 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: '#8899aa' }}>
          Correlation Heatmap
        </span>
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full" style={{ background: REGIME_META[selectedRegime].color }} />
          <span className="text-[9px]" style={{ color: REGIME_META[selectedRegime].color }}>
            {REGIME_META[selectedRegime].label}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2 text-[8px]" style={{ color: '#8899aa' }}>
        <span>-1.0</span>
        <div
          className="flex-1 h-2 rounded"
          style={{
            background: 'linear-gradient(to right, #ff2d55, rgba(255,45,85,0.6), rgba(255,255,255,0.05), rgba(0,255,157,0.25), rgba(0,255,157,0.6), #00ff9d)'
          }}
        />
        <span>+1.0</span>
      </div>

      <div className="overflow-auto" style={{ height }}>
        <div
          className="inline-grid gap-px"
          style={{ gridTemplateColumns: `48px repeat(${assets.length}, ${cellSize}px)` }}
        >
          <div />
          {assets.map(a => (
            <div
              key={`h-${a}`}
              className="text-[8px] font-mono text-center flex items-end justify-center"
              style={{ color: '#8899aa', height: 20 }}
            >
              <span className="rotate-0">{a}</span>
            </div>
          ))}

          {assets.map((assetA, i) => (
            <motion.div
              key={`row-${assetA}`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: i * 0.05 }}
              className="contents"
            >
              <div className="text-[8px] font-mono flex items-center justify-end pr-2" style={{ color: '#8899aa' }}>
                {assetA}
              </div>
              {assets.map((assetB, j) => {
                const cell = heatmapData.find(c => c.assetA === assetA && c.assetB === assetB);
                const corr = cell?.correlation ?? 0;
                const isDiag = i === j;
                return (
                  <motion.div
                    key={`cell-${assetA}-${assetB}`}
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: (i + j) * 0.02, type: 'spring', stiffness: 300 }}
                    className="rounded-sm flex items-center justify-center text-[7px] font-mono cursor-default"
                    style={{
                      width: cellSize,
                      height: cellSize,
                      background: corrToColor(corr),
                      color: isDiag ? '#e0e0ff' : Math.abs(corr) > 0.5 ? '#e0e0ff' : '#8899aa',
                      fontWeight: Math.abs(corr) > 0.5 ? 600 : 400,
                    }}
                    title={`${assetA} × ${assetB}: ${corr.toFixed(2)}`}
                  >
                    {isDiag ? '' : corr.toFixed(1)}
                  </motion.div>
                );
              })}
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default RegimeHeatmap;
