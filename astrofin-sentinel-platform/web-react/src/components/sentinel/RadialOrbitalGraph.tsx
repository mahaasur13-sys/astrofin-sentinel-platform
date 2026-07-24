'use client';

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart3, TrendingUp, MessageSquare, CandlestickChart, Globe,
  ShieldAlert, Newspaper, Layers, Bitcoin, Sparkles, Gem,
  ArrowLeftRight, Landmark, Loader2,
} from 'lucide-react';
import type { AgentLiveStatus } from '@/lib/sentinel-store';
import type { EnsembleResult } from '@/lib/agents';
import { memo } from "react";

interface RadialOrbitalGraphProps {
  agentStatuses: Record<string, AgentLiveStatus>;
  ensembleResult: EnsembleResult | null;
  isAnalyzing: boolean;
}

type AgentStatus = 'pending' | 'running' | 'complete' | 'error';

interface OrbitalNode {
  id: string;
  name: string;
  angle: number;
  radius: number;
  color: string;
  Icon: React.ComponentType<any>;
  status: AgentStatus;
  confidence: number;
  weight: number;
}

const ICON_MAP: Record<string, React.ComponentType<any>> = {
  fundamental: BarChart3,
  quant: TrendingUp,
  sentiment: MessageSquare,
  technical: CandlestickChart,
  macro: Globe,
  risk: ShieldAlert,
  news: Newspaper,
  options: Layers,
  crypto: Bitcoin,
  astrology: Sparkles,
  commodity: Gem,
  default: ArrowLeftRight,
};

const STATUS_COLORS: Record<AgentStatus, string> = {
  pending: '#fbbf24',
  running: '#60a5fa',
  complete: '#22c55e',
  error: '#ef4444',
};

const AGENT_PRESET = [
  { id: 'Fundamental', name: 'Fundamental', weight: 20, color: '#22c55e', iconKey: 'fundamental' },
  { id: 'Quant', name: 'Quant', weight: 20, color: '#3b82f6', iconKey: 'quant' },
  { id: 'Macro', name: 'Macro', weight: 15, color: '#8b5cf6', iconKey: 'macro' },
  { id: 'Options', name: 'Options', weight: 15, color: '#f97316', iconKey: 'options' },
  { id: 'Sentiment', name: 'Sentiment', weight: 10, color: '#ec4899', iconKey: 'sentiment' },
  { id: 'Technical', name: 'Technical', weight: 10, color: '#6366f1', iconKey: 'technical' },
  { id: 'Bull', name: 'Bull', weight: 5, color: '#dcfce7', iconKey: 'crypto' },
  { id: 'Bear', name: 'Bear', weight: 5, color: '#fee2e2', iconKey: 'commodity' },
  { id: 'Astro', name: 'Astro', weight: 5, color: '#e9d5ff', iconKey: 'astrology' },
  { id: 'Risk', name: 'Risk', weight: 0, color: '#cc241d', iconKey: 'risk' },
  { id: 'Insider', name: 'Insider', weight: 0, color: '#d79921', iconKey: 'news' },
  { id: 'Market', name: 'Market', weight: 0, color: '#087e8b', iconKey: 'default' },
];

export default function RadialOrbitalGraph({
  agentStatuses,
  ensembleResult,
  isAnalyzing,
}: RadialOrbitalGraphProps) {
  const { nodes, centerSignal, centerConfidence, bullPct, bearPct, activeCount, totalCount } = useMemo(() => {
    const resultNodes: OrbitalNode[] = [];
    let bullSum = 0;
    let bearSum = 0;
    let activeCnt = 0;

    const signal = ensembleResult?.signal;
    const confidence = ensembleResult?.confidence ?? 0;

    for (let i = 0; i < AGENT_PRESET.length; i++) {
      const preset = AGENT_PRESET[i];
      const status = agentStatuses[preset.id];
      const nodeStatus: AgentStatus = status?.status ?? 'pending';
      const nodeConfidence = status?.result?.confidence ?? 0;

      if (nodeStatus === 'complete' || nodeStatus === 'running') activeCnt++;

      const signalDir = status?.result?.signal ?? 'HOLD';
      if (signalDir === 'BUY') bullSum += preset.weight;
      if (signalDir === 'SELL') bearSum += preset.weight;

      resultNodes.push({
        id: preset.id,
        name: preset.name,
        angle: (i / AGENT_PRESET.length) * 360,
        radius: 80 + preset.weight * 1.5,
        color: preset.color,
        Icon: ICON_MAP[preset.iconKey] ?? ICON_MAP.default,
        status: nodeStatus,
        confidence: nodeConfidence,
        weight: preset.weight,
      });
    }

    const totalWeight = bullSum + bearSum;
    const bullPct = totalWeight > 0 ? (bullSum / totalWeight) * 100 : 50;
    const bearPct = totalWeight > 0 ? (bearSum / totalWeight) * 100 : 50;

    return {
      nodes: resultNodes,
      centerSignal: signal ?? 'HOLD',
      centerConfidence: confidence,
      bullPct,
      bearPct,
      activeCount: activeCnt,
      totalCount: resultNodes.length,
    };
  }, [agentStatuses, ensembleResult]);

  const centerColor =
    centerSignal === 'BUY' ? '#22c55e' : centerSignal === 'SELL' ? '#ef4444' : '#fbbf24';

  return (
    <div
      className="zone-card flex flex-col"
      style={{ minHeight: 280, overflow: 'hidden' }}
    >
      <div className="zone-title">Orbital Agent Board</div>

      <div
        className="flex-1 flex items-center justify-center relative"
        style={{ minHeight: 220 }}
      >
        {/* Orbital rings */}
        <motion.div
          className="absolute rounded-full border opacity-20"
          style={{
            width: 120,
            height: 120,
            borderColor: 'var(--border)',
          }}
          animate={{ rotate: isAnalyzing ? 360 : 0 }}
          transition={{ repeat: Infinity, duration: 20, ease: 'linear' }}
        />
        <motion.div
          className="absolute rounded-full border opacity-10"
          style={{
            width: 180,
            height: 180,
            borderColor: 'var(--border)',
          }}
          animate={{ rotate: isAnalyzing ? -360 : 0 }}
          transition={{ repeat: Infinity, duration: 30, ease: 'linear' }}
        />

        {/* Center — consensus signal */}
        <div
          className="absolute flex flex-col items-center justify-center z-20"
          style={{ width: 90, height: 90 }}
        >
          <div
            className="rounded-full flex flex-col items-center justify-center"
            style={{
              width: 80,
              height: 80,
              background: `radial-gradient(circle, ${centerColor}33, transparent)`,
              border: `2px solid ${centerColor}`,
            }}
          >
            {isAnalyzing ? (
              <Loader2 className="animate-spin" size={22} color={centerColor} />
            ) : (
              <>
                <span className="text-xs font-bold" style={{ color: centerColor, lineHeight: 1 }}>
                  {centerSignal}
                </span>
                <span className="text-[10px] font-mono" style={{ color: 'var(--text-muted)' }}>
                  {Math.round(centerConfidence * 100)}%
                </span>
              </>
            )}
          </div>
        </div>

        {/* Orbital nodes */}
        {nodes.map((node) => {
          const angleRad = (node.angle * Math.PI) / 180;
          const x = Math.cos(angleRad) * node.radius;
          const y = Math.sin(angleRad) * node.radius;
          const dotColor = STATUS_COLORS[node.status];
          const isActive = node.status === 'running';

          return (
            <motion.div
              key={node.id}
              className="absolute flex flex-col items-center"
              style={{
                left: `calc(50% + ${x}px)`,
                top: `calc(50% + ${y}px)`,
                transform: 'translate(-50%, -50%)',
              }}
              animate={isActive ? { scale: [1, 1.15, 1] } : {}}
              transition={{ repeat: Infinity, duration: 1.5 }}
            >
              <div
                className="relative rounded-full flex items-center justify-center"
                style={{
                  width: 32,
                  height: 32,
                  background: `${node.color}22`,
                  border: `1.5px solid ${node.color}`,
                }}
                title={`${node.name} (${node.weight}%) — ${node.status}`}
              >
                <node.Icon className="size-3.5" style={{ color: node.color }} />
              </div>
              <div
                className="absolute rounded-full"
                style={{
                  width: 6,
                  height: 6,
                  background: dotColor,
                  top: -4,
                  right: -4,
                  boxShadow: isActive ? `0 0 6px ${dotColor}` : 'none',
                }}
              />
              <span
                className="text-[9px] font-mono mt-0.5 leading-tight whitespace-nowrap"
                style={{ color: 'var(--text-muted)' }}
              >
                {node.weight > 0 ? `${node.weight}%` : ''}
              </span>
            </motion.div>
          );
        })}
      </div>

      {/* Bottom legend */}
      <div className="flex items-center justify-between px-3 pb-2 gap-2">
        <div className="flex items-center gap-1.5">
          <div className="flex items-center gap-1">
            <span
              className="inline-block rounded-full"
              style={{ width: 6, height: 6, background: STATUS_COLORS.complete }}
            />
            <span className="text-[10px] font-mono" style={{ color: 'var(--text-muted)' }}>
              {activeCount}/{totalCount} active
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono" style={{ color: '#22c55e' }}>
            B {Math.round(bullPct)}%
          </span>
          <div
            className="h-1 rounded-full"
            style={{
              width: 40,
              background: 'var(--border)',
              overflow: 'hidden',
            }}
          >
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${bullPct}%`,
                background: '#22c55e',
              }}
            />
          </div>
          <span className="text-[10px] font-mono" style={{ color: '#ef4444' }}>
            S {Math.round(bearPct)}%
          </span>
        </div>
      </div>
    </div>
  );
}

