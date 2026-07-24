import { useDashboardStore } from '@/stores/dashboard.store';
import { RegimeRadar } from '@/components/sentinel/RegimeRadar';
import { SafetyGateCard } from '@/components/sentinel/SafetyGateCard';
import type { Regime } from '@/types';

interface RightPanelProps {
  compact?: boolean;
}

export default function RightPanel({ compact = false }: RightPanelProps) {
  const regime = useDashboardStore((s) => s.regime);
  const safety = useDashboardStore((s) => s.safety);

  const regimeRadar = regime
    ? {
        probabilities: {
          bull: 0.7,
          bear: 0.1,
          sideways: 0.1,
          high_vol: 0.05,
          anomaly: 0.05,
        } as Record<Regime, number>,
        currentRegime: regime,
      }
    : {
        probabilities: { bull: 1, bear: 0, sideways: 0, high_vol: 0, anomaly: 0 } as Record<Regime, number>,
        currentRegime: 'bull' as Regime,
      };

  const safetyProps = safety
    ? {
        status: safety.status,
        riskPct: safety.riskPct,
        maxDrawdown: safety.maxDrawdown,
        var95: safety.var95,
        leverage: safety.leverage,
        triggers: safety.triggers,
      }
    : undefined;

  if (compact) {
    return (
      <div className="flex flex-col gap-3 p-2">
        <RegimeRadar {...regimeRadar} compact />
        {safetyProps && <SafetyGateCard {...safetyProps} />}
      </div>
    );
  }

  return (
    <aside className="hidden lg:flex fixed right-0 top-0 z-20 h-screen w-80 flex-col border-l border-white/10 bg-[#0a0a12] overflow-y-auto">
      <div className="flex items-center gap-2 border-b border-white/10 px-4 py-3.5">
        <span className="text-xs font-semibold uppercase tracking-wider text-gray-600">
          Details
        </span>
      </div>
      <div className="flex-1 p-3 space-y-3">
        <RegimeRadar {...regimeRadar} />
        {safetyProps && <SafetyGateCard {...safetyProps} />}
      </div>
    </aside>
  );
}
