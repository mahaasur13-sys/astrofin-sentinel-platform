'use client';

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Area,
} from 'recharts';
import { Dna } from 'lucide-react';

export interface MetaRLGeneration {
  generation: number;
  fitness: number;
  avgSharpe: number;
  maxDrawdown: number;
  winRate: number;
  populationSize: number;
  bestStrategy: string;
}

interface GenData {
  gen: number;
  fitness: number;
  avgReward: number;
  diversity: number;
  bestFitness: number;
}

export interface MetaRLEvolutionProps {
  generations?: number | MetaRLGeneration[];
  height?: number;
  compact?: boolean;
}

function generateMockGenerations(count: number): GenData[] {
  const data: GenData[] = [];
  let fitness = 0.45;
  let bestFitness = 0.45;
  for (let i = 1; i <= count; i++) {
    const improvement = Math.random() * 0.04 - 0.008;
    fitness = Math.min(0.95, Math.max(0.3, fitness + improvement));
    bestFitness = Math.max(bestFitness, fitness);
    data.push({
      gen: i,
      fitness: Math.round(fitness * 1000) / 1000,
      avgReward: Math.round((0.3 + Math.random() * 0.4) * 1000) / 1000,
      diversity: Math.round((0.6 - fitness * 0.4 + Math.random() * 0.1) * 1000) / 1000,
      bestFitness: Math.round(bestFitness * 1000) / 1000,
    });
  }
  return data;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ payload: GenData }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="glass-card px-3 py-2 text-xs" style={{ background: 'rgba(18,18,26,0.95)' }}>
      <div className="font-mono mb-1" style={{ color: '#8899aa' }}>Gen {d.gen}</div>
      <div style={{ color: '#00ff9d' }}>
        Fitness: <span className="font-mono font-bold">{(d.fitness * 100).toFixed(1)}%</span>
      </div>
      <div style={{ color: '#7b2cff' }}>
        Best: <span className="font-mono">{(d.bestFitness * 100).toFixed(1)}%</span>
      </div>
      <div style={{ color: '#00b8ff' }}>
        Avg Reward: <span className="font-mono">{(d.avgReward * 100).toFixed(1)}%</span>
      </div>
      <div style={{ color: '#ffd000' }}>
        Diversity: <span className="font-mono">{(d.diversity * 100).toFixed(1)}%</span>
      </div>
    </div>
  );
}

export function MetaRLEvolution({
  generations = 30,
  height,
  compact = false,
}: MetaRLEvolutionProps) {
  const data = useMemo(() => {
    if (Array.isArray(generations)) {
      return generations.map((g, i) => ({
        gen: g.generation,
        fitness: g.fitness,
        avgReward: g.avgSharpe,
        diversity: 1 - g.fitness,
        bestFitness: i === 0
          ? g.fitness
          : Math.max(g.fitness, ...generations.slice(0, i).map(p => p.fitness)),
      }));
    }
    return generateMockGenerations(generations);
  }, [generations]);

  const latestGen = data.length > 0 ? data[data.length - 1] : null;
  const chartHeight = height ?? (compact ? 120 : 200);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-4"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Dna className="size-3.5" style={{ color: '#7b2cff' }} />
          <h3 className="text-xs font-semibold uppercase tracking-wider" style={{ color: '#8899aa' }}>
            Meta-RL Evolution
          </h3>
        </div>
        {!compact && latestGen && (
          <div className="flex items-center gap-3 text-[10px]">
            <span style={{ color: '#8899aa' }}>
              Gen <span className="font-mono" style={{ color: '#e0e0ff' }}>{latestGen.gen}</span>
            </span>
            <span style={{ color: '#8899aa' }}>
              Fitness{' '}
              <span className="font-mono" style={{ color: '#00ff9d' }}>
                {(latestGen.bestFitness * 100).toFixed(1)}%
              </span>
            </span>
          </div>
        )}
      </div>

      <ResponsiveContainer width="100%" height={chartHeight}>
        <LineChart data={data} margin={{ top: 4, right: 12, left: 4, bottom: 4 }}>
          <defs>
            <linearGradient id="fitnessGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#7b2cff" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#7b2cff" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="bestFitGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00ff9d" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#00ff9d" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
          <XAxis dataKey="gen" stroke="#8899aa" fontSize={9} tickLine={false} />
          <YAxis
            domain={[0.2, 1]}
            stroke="#8899aa"
            fontSize={9}
            tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
          />
          {!compact && <Tooltip content={<CustomTooltip />} />}
          <Area
            type="monotone"
            dataKey="bestFitness"
            stroke="#00ff9d"
            strokeWidth={1.5}
            fill="url(#bestFitGrad)"
            animationDuration={800}
          />
          <Area
            type="monotone"
            dataKey="fitness"
            stroke="#7b2cff"
            strokeWidth={2}
            fill="url(#fitnessGrad)"
            animationDuration={600}
          />
          {!compact && (
            <Line
              type="monotone"
              dataKey="diversity"
              stroke="#ffd000"
              strokeWidth={1}
              strokeDasharray="4 2"
              dot={false}
              animationDuration={1000}
            />
          )}
        </LineChart>
      </ResponsiveContainer>

      {!compact && (
        <div className="flex items-center gap-4 mt-2 text-[9px]">
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 rounded" style={{ background: '#7b2cff' }} />
            Fitness
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 rounded" style={{ background: '#00ff9d' }} />
            Best
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 rounded" style={{ background: '#ffd000' }} />
            Diversity
          </span>
        </div>
      )}
    </motion.div>
  );
}

export default MetaRLEvolution;
