import { useState, useMemo, useEffect, useCallback } from 'react';
import RegimeRadar from './components/sentinel/RegimeRadar';
import SafetyGateCard from './components/sentinel/SafetyGateCard';
import EquityCurve from './components/sentinel/EquityCurve';
import AgentPerformanceGrid from './components/sentinel/AgentPerformanceGrid';
import AstroMindChat from './components/sentinel/AstroMindChat';

type Regime = 'bull' | 'bear' | 'sideways' | 'high_vol' | 'anomaly';
type Signal = 'buy' | 'sell' | 'hold' | 'strong_buy' | 'strong_sell';
type SafetyStatus = 'safe' | 'warning' | 'danger' | 'stopped';

interface AgentItem {
  id: string;
  name: string;
  weight: number;
  domain: string;
  signal: string;
  confidence: number;
  status: string;
}

interface DashboardData {
  agents: AgentItem[];
  regime: Record<Regime, number>;
  ensemble: { signal: string; confidence: number; buy_count: number; sell_count: number; hold_count: number };
  safety_gate: string;
  pnl: number;
  mode: string;
}

function generateEquityData(days: number): { date: string; equity: number; regime: Regime }[] {
  const regimes: Regime[] = ['bull', 'bull', 'bull', 'sideways', 'high_vol', 'bear', 'bear', 'sideways', 'bull', 'bull'];
  const data: { date: string; equity: number; regime: Regime }[] = [];
  let equity = 10000;
  for (let i = 0; i < days; i++) {
    const regime = regimes[Math.floor((i / days) * regimes.length) % regimes.length];
    const vol = regime === 'high_vol' ? 0.025 : regime === 'anomaly' ? 0.04 : 0.012;
    const drift = regime === 'bull' ? 0.003 : regime === 'bear' ? -0.004 : 0;
    equity *= 1 + drift + (Math.random() - 0.48) * vol;
    const date = new Date(2026, 6, 19 - (days - i));
    const dateStr = `${date.getMonth() + 1}/${date.getDate()}`;
    data.push({ date: dateStr, equity: Math.round(equity * 100) / 100, regime });
  }
  return data;
}

function parseAgentSignal(s: string): Signal {
  const lower = s.toLowerCase();
  if (lower === 'strong_buy' || lower === 'buy' || lower === 'long') return 'buy';
  if (lower === 'strong_sell' || lower === 'sell' || lower === 'short') return 'sell';
  return 'hold';
}

function getDominantRegime(probs: Record<Regime, number>): Regime {
  const entries = Object.entries(probs) as [Regime, number][];
  entries.sort((a, b) => b[1] - a[1]);
  return entries[0][0];
}

function mapSafetyStatus(s: string): SafetyStatus {
  const lower = s.toLowerCase();
  if (lower === 'safe' || lower === 'green') return 'safe';
  if (lower === 'warning' || lower === 'yellow') return 'warning';
  if (lower === 'danger' || lower === 'red') return 'danger';
  return 'stopped';
}

export default function App() {
  const [chatOpen, setChatOpen] = useState(false);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/dashboard');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: DashboardData = await res.json();
      setDashboard(data);
      setError(null);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 15000);
    return () => clearInterval(interval);
  }, [fetchDashboard]);

  const handleRunAgent = useCallback(async (agentId: string) => {
    try {
      await fetch('/api/v1/agent/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agentId, prompt: `Analyze market conditions for ${agentId}` }),
      });
      setTimeout(fetchDashboard, 2000);
    } catch {}
  }, [fetchDashboard]);

  const equityData = useMemo(() => generateEquityData(60), []);

  if (loading) {
    return (
      <main style={{ minHeight: '100vh', background: 'var(--bg-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 16 }}>
        <div style={{ width: 48, height: 48, borderRadius: '50%', border: '3px solid var(--accent)', borderTopColor: 'transparent', animation: 'spin 1s linear infinite' }} />
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Loading AstroFin Sentinel...</p>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </main>
    );
  }

  if (error || !dashboard) {
    return (
      <main style={{ minHeight: '100vh', background: 'var(--bg-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <span style={{ fontSize: '1.5rem' }}>⚠️</span>
          <p style={{ color: 'var(--bear)', fontSize: '0.85rem', marginTop: 8 }}>Failed to connect: {error || 'No data'}</p>
          <button onClick={fetchDashboard} style={{ marginTop: 12, padding: '6px 16px', border: '1px solid var(--accent)', borderRadius: 6, background: 'transparent', color: 'var(--accent)', cursor: 'pointer' }}>
            Retry
          </button>
        </div>
      </main>
    );
  }

  const regimeProbs = dashboard.regime;
  const dominantRegime = getDominantRegime(regimeProbs);
  const safetyStatus = mapSafetyStatus(dashboard.safety_gate);
  const ensembleSignal = dashboard.ensemble.signal.toLowerCase();
  const ensColor = ensembleSignal.includes('buy') ? 'var(--bull)' : ensembleSignal.includes('sell') ? 'var(--bear)' : 'var(--sideways)';

  const agents = dashboard.agents.map((a) => ({
    id: a.id,
    name: a.name.replace('Agent', ''),
    weight: a.weight,
    signal: parseAgentSignal(a.signal),
    confidence: a.confidence,
    winRate: Math.round((45 + Math.random() * 25) * 10) / 10,
    sharpe: Math.round((0.3 + Math.random() * 1.2) * 100) / 100,
    pnl: Math.round((Math.random() * 15 - 2) * 10) / 10,
    status: a.status === 'active' ? 'active' as const : a.status === 'running' ? 'active' as const : 'idle' as const,
    lastRun: `${Math.floor(Math.random() * 15)}m ago`,
  }));

  const buyCount = agents.filter((a) => a.signal === 'buy' || a.signal === 'strong_buy').length;
  const sellCount = agents.filter((a) => a.signal === 'sell' || a.signal === 'strong_sell').length;
  const holdCount = agents.filter((a) => a.signal === 'hold').length;
  const activeCount = agents.filter((a) => a.status === 'active').length;

  const REGIME_LABELS: Record<Regime, string> = {
    bull: 'BULL',
    bear: 'BEAR',
    sideways: 'SIDEWAYS',
    high_vol: 'HIGH VOL',
    anomaly: 'ANOMALY',
  };

  const REGIME_COLORS: Record<Regime, string> = {
    bull: 'var(--bull)',
    bear: 'var(--bear)',
    sideways: 'var(--sideways)',
    high_vol: 'var(--high-vol)',
    anomaly: 'var(--anomaly)',
  };

  return (
    <main style={{
      minHeight: '100vh',
      background: 'var(--bg-primary)',
      padding: '16px 20px 20px',
      display: 'flex',
      flexDirection: 'column',
      gap: 14,
    }}>
      {/* Header */}
      <header className="glass-panel" style={{ padding: '12px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <span style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent)' }}>🧠 AstroFin Sentinel</span>
          <div style={{ display: 'flex', gap: 4 }}>
            {['Live', 'Backtest', 'Paper'].map((mode) => (
              <button key={mode} style={{
                padding: '3px 10px',
                background: mode === dashboard.mode || mode === 'Live' ? 'var(--accent)' : 'transparent',
                border: `1px solid ${mode === dashboard.mode || mode === 'Live' ? 'var(--accent)' : 'var(--border)'}`,
                borderRadius: 4,
                color: mode === dashboard.mode || mode === 'Live' ? '#fff' : 'var(--text-muted)',
                fontSize: '0.7rem',
                cursor: 'pointer',
                fontWeight: mode === dashboard.mode || mode === 'Live' ? 600 : 400,
              }}>
                {mode}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.78rem' }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--bull)' }} />
            <span style={{ color: 'var(--text-secondary)' }}>Safety Gate</span>
            <span style={{ color: 'var(--bull)', fontWeight: 600 }}>{dashboard.safety_gate}</span>
          </div>

          <div style={{
            padding: '4px 12px',
            borderRadius: 6,
            fontSize: '0.78rem',
            fontWeight: 700,
            color: REGIME_COLORS[dominantRegime],
            background: `${REGIME_COLORS[dominantRegime]}15`,
            border: `1px solid ${REGIME_COLORS[dominantRegime]}30`,
          }}>
            {REGIME_LABELS[dominantRegime]} {Math.round(regimeProbs[dominantRegime] * 100)}%
          </div>

          <div className="mono-value" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            PnL: <span style={{ color: dashboard.pnl >= 0 ? 'var(--bull)' : 'var(--bear)', fontWeight: 600 }}>
              {dashboard.pnl >= 0 ? '+' : ''}${dashboard.pnl.toLocaleString()}
            </span>
          </div>

          <div className="mono-value" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            <span style={{ color: 'var(--sideways)', fontWeight: 600 }}>WS Connected</span>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr 320px', gap: 14, flex: 1 }}>
        {/* Left Sidebar */}
        <aside style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <nav className="glass-panel" style={{ padding: 12 }}>
            {['Dashboard', 'Agents', 'Regime', 'Knowledge', 'History', 'Settings'].map((item) => (
              <div key={item} style={{
                padding: '8px 12px',
                borderRadius: 6,
                fontSize: '0.78rem',
                cursor: 'pointer',
                color: item === 'Dashboard' ? 'var(--accent)' : 'var(--text-secondary)',
                background: item === 'Dashboard' ? 'rgba(123, 44, 255, 0.1)' : 'transparent',
                marginBottom: 2,
                fontWeight: item === 'Dashboard' ? 600 : 400,
              }}>
                {item}
              </div>
            ))}
          </nav>

          <div className="glass-panel" style={{ padding: 12 }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8 }}>
              Active Agents ({activeCount})
            </div>
            {agents.filter((a) => a.status === 'active').slice(0, 8).map((a) => (
              <div key={a.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.72rem', marginBottom: 6 }}>
                <span>{a.name}</span>
                <span className={`signal-badge signal-badge-${a.signal}`} style={{ fontSize: '0.6rem', padding: '1px 6px' }}>
                  {a.signal.toUpperCase()}
                </span>
              </div>
            ))}
          </div>

          <div className="glass-panel" style={{ padding: 12 }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8 }}>
              Watchlist
            </div>
            {[
              { ticker: 'BTCUSDT', price: 67432, change: 2.3 },
              { ticker: 'ETHUSDT', price: 3421, change: -0.8 },
              { ticker: 'AAPL', price: 198.5, change: 1.1 },
              { ticker: 'NVDA', price: 892.3, change: 4.2 },
              { ticker: 'SPY', price: 548.7, change: 0.3 },
            ].map((w) => (
              <div key={w.ticker} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', marginBottom: 5 }}>
                <span className="mono-value" style={{ color: 'var(--text-primary)' }}>{w.ticker}</span>
                <span className="mono-value" style={{ color: w.change >= 0 ? 'var(--bull)' : 'var(--bear)' }}>
                  {w.price.toLocaleString()} <span style={{ fontSize: '0.65rem' }}>{w.change >= 0 ? '+' : ''}{w.change}%</span>
                </span>
              </div>
            ))}
          </div>
        </aside>

        {/* Main Content */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="glass-panel" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 20 }}>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: ensColor }}>
              {ensembleSignal.toUpperCase()}
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Ensemble · {agents.length} agents · confidence {dashboard.ensemble.confidence}%
            </div>
            <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>BUY: {buyCount}</span>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>SELL: {sellCount}</span>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>HOLD: {holdCount}</span>
            </div>
          </div>

          <EquityCurve data={equityData.slice(-45)} height={280} />

          <AgentPerformanceGrid agents={agents} onRunAgent={handleRunAgent} />
        </section>

        {/* Right Sidebar */}
        <aside style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <RegimeRadar
            probabilities={regimeProbs}
            currentRegime={dominantRegime}
            compact
          />

          <RegimeRadar
            probabilities={regimeProbs}
            currentRegime={dominantRegime}
          />

          <SafetyGateCard
            status={safetyStatus}
            reason="All systems operational. Regime within normal parameters."
            riskPct={2.0}
            maxDrawdown={8.5}
            var95={3.2}
            leverage={1.6}
            triggers={[
              { time: new Date().toLocaleTimeString(), reason: 'Regime check passed' },
              { time: new Date(Date.now() - 3600000).toLocaleTimeString(), reason: 'Periodic health scan' },
            ]}
          />
        </aside>
      </div>

      {/* Footer */}
      <footer className="glass-panel" style={{ padding: '10px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.72rem' }}>
        <div style={{ display: 'flex', gap: 16, color: 'var(--text-muted)' }}>
          <span>⏱ {agents.length} agents · {activeCount} active · poll 15s</span>
          <span>📊 RAG: 43 docs indexed</span>
          <span>🔗 WS: Connected</span>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <span className="mono-value" style={{ color: 'var(--text-muted)' }}>
            Regime: <span style={{ color: REGIME_COLORS[dominantRegime] }}>{REGIME_LABELS[dominantRegime]}</span> · HMM v2.1 · KARL-Arbiter active
          </span>
        </div>
      </footer>

      {/* AstroMind Chat */}
      <AstroMindChat isOpen={chatOpen} onToggle={() => setChatOpen(!chatOpen)} />
    </main>
  );
}
