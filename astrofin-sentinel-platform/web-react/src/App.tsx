import { useState } from 'react';
import { Activity, Layers, Zap, TrendingUp, BarChart3, Settings, ChevronDown, Bell, Maximize2, Route, Hexagon, Cpu } from 'lucide-react';
import { RegimeRadar, type Regime } from '@/components/sentinel/RegimeRadar';
import { SafetyGateCard } from '@/components/sentinel/SafetyGateCard';
import { AgentPerformanceGrid } from '@/components/sentinel/AgentPerformanceGrid';
import { EquityCurve } from '@/components/sentinel/EquityCurve';
import { MetaRLEvolution } from '@/components/sentinel/MetaRLEvolution';
import { RegimeHeatmap } from '@/components/sentinel/RegimeHeatmap';
import SessionTable from '@/components/SessionTable';
import { useSentinelStream } from '@/hooks/use-sentinel-stream';

const modeTabs = ['LIVE', 'BACKTEST', 'PAPER', 'OPTIMIZE'] as const;
const timeframes = ['1m', '5m', '15m', '1H', '4H', '1D', '1W'] as const;
const watchlist = ['BTC-USD', 'ETH-USD', 'SPX', 'NDX', 'NVDA', 'AAPL', 'GC=F', 'CL=F'] as const;
const navItems = [
  { icon: Activity, label: 'Dashboard' },
  { icon: TrendingUp, label: 'Trading' },
  { icon: BarChart3, label: 'Analytics' },
  { icon: Layers, label: 'Agents' },
  { icon: Route, label: 'Backtest' },
  { icon: Settings, label: 'Settings' },
] as const;

export default function App() {
  const [mode, setMode] = useState<string>('LIVE');
  const [tf, setTf] = useState<string>('1D');
  const [ticker, setTicker] = useState('BTC-USD');
  const [showRightPanel, setShowRightPanel] = useState(true);

  const stream = useSentinelStream(true);
  const regime: Regime = stream.regime?.regime as Regime ?? 'bull';

  return (
    <div className="h-screen flex flex-col bg-[#0a0a0f] text-[#e0e0ff]">
      {/* === HEADER === */}
      <header className="zone-header z-30 flex items-center justify-between px-4 shrink-0">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Hexagon size={22} className="text-[#7b2cff] neon-logo-glow" />
            <div>
              <div className="text-sm font-bold tracking-wide" style={{ color: '#e0e0ff' }}>
                ASTROFIN <span style={{ color: '#7b2cff' }}>SENTINEL</span>
              </div>
              <div className="text-[8px] uppercase tracking-widest" style={{ color: '#8899aa' }}>
                Multi-Agent Platform
              </div>
            </div>
          </div>
          <div className="h-5 w-px" style={{ background: 'rgba(255,255,255,0.06)' }} />
          <div className="flex gap-1">
            {modeTabs.map(m => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`mode-pill ${m === mode ? `active-${m.toLowerCase()}` : 'inactive'}`}
              >
                {m}
              </button>
            ))}
          </div>
          <div className="h-5 w-px" style={{ background: 'rgba(255,255,255,0.06)' }} />
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold" style={{ color: '#00ff9d' }}>{ticker}</span>
            <ChevronDown size={12} style={{ color: '#8899aa' }} />
          </div>
          <div className="flex gap-0.5">
            {timeframes.map(t => (
              <button
                key={t}
                onClick={() => setTf(t)}
                className="text-[10px] font-mono px-1.5 py-0.5 rounded"
                style={{
                  color: t === tf ? '#e0e0ff' : '#8899aa',
                  background: t === tf ? 'rgba(123,44,255,0.12)' : 'transparent',
                }}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs" style={{ color: '#8899aa' }}>
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-[#00ff9d]" />
              <span className="font-mono" style={{ color: '#e0e0ff' }}>13</span>
            </div>
            <span className="text-[#8899aa]">agents</span>
          </div>
          <button className="hover:bg-white/5 p-1.5 rounded">
            <Bell size={15} style={{ color: '#8899aa' }} />
          </button>
          <button className="hover:bg-white/5 p-1.5 rounded">
            <Maximize2 size={15} style={{ color: '#8899aa' }} />
          </button>
          <button
            onClick={() => setShowRightPanel(!showRightPanel)}
            className="hover:bg-white/5 p-1.5 rounded"
          >
            <Route size={15} style={{ color: '#8899aa' }} />
          </button>
        </div>
      </header>

      {/* === MAIN LAYOUT === */}
      <div className="flex-1 flex overflow-hidden">
        {/* === LEFT SIDEBAR === */}
        <aside className="zone-sidebar shrink-0 flex flex-col panel-transition">
          <nav className="flex-1 py-3">
            {navItems.map(item => (
              <div
                key={item.label}
                className={`sidebar-nav-item flex items-center gap-3 px-4 py-2.5 cursor-pointer text-xs`}
                style={{ color: '#8899aa' }}
              >
                <item.icon size={15} />
                <span className="font-medium">{item.label}</span>
              </div>
            ))}
          </nav>

          <div className="p-3 border-t border-white/5">
            <div className="text-[9px] uppercase tracking-wider mb-2" style={{ color: '#8899aa' }}>Watchlist</div>
            {watchlist.map(t => (
              <div
                key={t}
                onClick={() => setTicker(t)}
                className={`watchlist-ticker flex items-center justify-between ${t === ticker ? 'active' : ''}`}
              >
                <span style={{ color: t === ticker ? '#e0e0ff' : '#8899aa' }}>{t}</span>
                <span
                  className="text-[9px] font-mono"
                  style={{ color: Math.random() > 0.4 ? '#00ff9d' : '#ff2d55' }}
                >
                  {Math.random() > 0.4 ? '+' : '-'}{Math.random().toFixed(2)}%
                </span>
              </div>
            ))}
          </div>

          <div className="px-3 pb-3">
            <div className="glass-card p-2 flex items-center gap-2 text-[10px]" style={{ color: '#8899aa' }}>
              <Cpu size={12} style={{ color: '#7b2cff' }} />
              <span>v1.0.0-ga</span>
              <span className="ml-auto font-mono" style={{ color: '#7b2cff' }}>664</span>
            </div>
          </div>
        </aside>

        {/* === CENTER CANVAS === */}
        <main className="flex-1 overflow-y-auto p-3">
          <div className="grid grid-cols-3 gap-3 mb-3">
            {/* Stats */}
            <div className="glass-card p-3 flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'rgba(0,255,157,0.08)' }}>
                <Hexagon size={18} style={{ color: '#00ff9d' }} />
              </div>
              <div>
                <div className="text-[9px] uppercase tracking-wider" style={{ color: '#8899aa' }}>Agents Online</div>
                <div className="text-sm font-bold font-mono" style={{ color: '#e0e0ff' }}>13</div>
              </div>
            </div>
            <div className="glass-card p-3 flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'rgba(0,184,255,0.08)' }}>
                <Zap size={18} style={{ color: '#00b8ff' }} />
              </div>
              <div>
                <div className="text-[9px] uppercase tracking-wider" style={{ color: '#8899aa' }}>Signals Today</div>
                <div className="text-sm font-bold font-mono" style={{ color: '#e0e0ff' }}>7</div>
              </div>
            </div>
            <div className="glass-card p-3 flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'rgba(123,44,255,0.08)' }}>
                <Activity size={18} style={{ color: '#7b2cff' }} />
              </div>
              <div>
                <div className="text-[9px] uppercase tracking-wider" style={{ color: '#8899aa' }}>Success Rate</div>
                <div className="text-sm font-bold font-mono" style={{ color: '#e0e0ff' }}>94.2%</div>
              </div>
            </div>
          </div>

          {/* Equity Curve */}
          <div className="mb-3 chart-reveal">
            <EquityCurve height={240} data={[{ date: "2026-01", equity: 100000, regime: "bull" as const }, { date: "2026-03", equity: 105000, regime: "bull" as const }, { date: "2026-05", equity: 112000, regime: "bull" as const }, { date: "2026-07", equity: 117510, regime: "bull" as const }]} />
          </div>

          {/* Mid Grid: Agent Grid + Regime */}
          <div className="grid grid-cols-3 gap-3 mb-3">
            <div className="col-span-2">
              <AgentPerformanceGrid agents={[]} />
            </div>
            <div className="flex flex-col gap-3">
              <RegimeRadar probabilities={{ bull: 0.7, bear: 0.1, sideways: 0.1, high_vol: 0.05, anomaly: 0.05 }} currentRegime={regime} compact={true} />
              <SafetyGateCard
                status="safe"
                riskPct={2.0}
                maxDrawdown={5.2}
                var95={3.1}
                leverage={1.5}
                triggers={[{ time: "1h ago", reason: "Max DD > 5%" }, { time: "30m ago", reason: "VaR > 3%" }]} />
            </div>
          </div>

          {/* Meta-RL + Heatmap */}
          <div className="grid grid-cols-2 gap-3 mb-3">
            <MetaRLEvolution generations={30} height={200} />
            <RegimeHeatmap selectedRegime={regime} height={220} />
          </div>

          {/* Session Table */}
          <SessionTable />
        </main>

        {/* === RIGHT PANEL === */}
        {showRightPanel && (
          <aside className="zone-right shrink-0 overflow-y-auto panel-transition">
            <div className="p-4">
              <div className="text-xs font-semibold uppercase tracking-wider mb-4" style={{ color: '#8899aa' }}>
                Ensemble Status
              </div>

              <div className="flex flex-col gap-3">
                {/* Ensemble Signal */}
                <div className="glass-card p-4 text-center">
                  <div className="text-[9px] uppercase tracking-wider mb-2" style={{ color: '#8899aa' }}>Current Signal</div>
                  <div className="text-2xl font-bold font-mono neon-glow-green mb-1">BUY</div>
                  <div className="text-xs" style={{ color: '#8899aa' }}>
                    Confidence <span className="font-mono" style={{ color: '#00ff9d' }}>82.4%</span>
                  </div>
                  <div className="mt-2 text-[10px] italic" style={{ color: '#8899aa' }}>
                    Strong consensus across Fundamental and Quant agents
                  </div>
                </div>

                {/* Ensemble Weights */}
                <div className="glass-card p-3">
                  <div className="text-[10px] uppercase tracking-wider mb-2" style={{ color: '#8899aa' }}>Ensemble Weights</div>
                  {[
                    { label: 'Fundamental', pct: 20, color: '#00ff9d' },
                    { label: 'Quant', pct: 20, color: '#00b8ff' },
                    { label: 'Macro', pct: 15, color: '#ffd000' },
                    { label: 'Options Flow', pct: 15, color: '#7b2cff' },
                    { label: 'Sentiment', pct: 10, color: '#ff2d55' },
                    { label: 'Technical', pct: 10, color: '#00b8ff' },
                    { label: 'Astro Block', pct: 16, color: '#7b2cff' },
                  ].map(w => (
                    <div key={w.label} className="flex items-center gap-2 mb-1">
                      <span className="text-[10px]" style={{ color: '#8899aa', width: 80 }}>{w.label}</span>
                      <div className="flex-1 h-1.5 rounded bg-white/5">
                        <div className="h-full rounded weight-bar" style={{ width: `${w.pct}%`, background: w.color }} />
                      </div>
                      <span className="text-[10px] font-mono" style={{ color: w.color, width: 24 }}>{w.pct}%</span>
                    </div>
                  ))}
                </div>

                {/* Recent Activity */}
                <div className="glass-card p-3">
                  <div className="text-[10px] uppercase tracking-wider mb-2" style={{ color: '#8899aa' }}>Agent Activity</div>
                  {[
                    { agent: 'Fundamental', time: '2s ago', signal: 'BUY', conf: 85 },
                    { agent: 'Quant', time: '4s ago', signal: 'BUY', conf: 92 },
                    { agent: 'Macro', time: '6s ago', signal: 'HOLD', conf: 65 },
                    { agent: 'Sentiment', time: '8s ago', signal: 'SELL', conf: 58 },
                    { agent: 'Technical', time: '10s ago', signal: 'HOLD', conf: 71 },
                  ].map(a => (
                    <div key={a.agent} className="flex items-center gap-2 py-1 text-[10px]">
                      <span className="w-1.5 h-1.5 rounded-full" style={{ background: a.signal === 'BUY' ? '#00ff9d' : a.signal === 'SELL' ? '#ff2d55' : '#ffd000' }} />
                      <span style={{ color: '#e0e0ff' }}>{a.agent}</span>
                      <span className={`signal-badge signal-badge-${a.signal.toLowerCase()}`}>{a.signal}</span>
                      <span className="ml-auto font-mono" style={{ color: '#8899aa' }}>{a.conf}%</span>
                      <span style={{ color: '#8899aa' }}>{a.time}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </aside>
        )}
      </div>

      {/* === FOOTER === */}
      <footer className="zone-footer shrink-0 flex items-center justify-between px-4 text-[9px]" style={{ color: '#8899aa' }}>
        <div className="flex items-center gap-4">
          <span>v1.0.0-ga • Hub-and-Spoke</span>
          <span className="w-1 h-1 rounded-full bg-[#00ff9d]" />
          <span className="font-mono">664 tests</span>
        </div>
        <div className="flex items-center gap-3">
          <span>Regime: <span className="font-mono" style={{ color: '#00ff9d' }}>BULL</span></span>
          <span>Latency: <span className="font-mono" style={{ color: '#e0e0ff' }}>234ms</span></span>
          <span>Uptime: <span className="font-mono" style={{ color: '#e0e0ff' }}>99.97%</span></span>
        </div>
      </footer>
    </div>
  );
}
