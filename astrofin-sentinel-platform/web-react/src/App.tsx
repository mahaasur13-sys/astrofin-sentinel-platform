import * as React from 'react';
import { Container, Typography, Box, Grid } from '@mui/material';
import SessionTable from './components/SessionTable';
import ContextDrawer from './components/ContextDrawer';
import RegimeRadar from './components/sentinel/RegimeRadar';
import EquityCurve from './components/sentinel/EquityCurve';
import SafetyGateCard from './components/sentinel/SafetyGateCard';
import AgentPerformanceGrid from './components/sentinel/AgentPerformanceGrid';
import type { Regime } from './components/sentinel/RegimeRadar';

const PANEL_STYLE: React.CSSProperties = {
  background: '#0d0d14',
  border: '1px solid rgba(255,255,255,0.06)',
  borderRadius: 12,
  padding: 16,
};

// Mock data matching component interfaces
const MOCK_REGIME_PROBS: Record<Regime, number> = { bull: 0.42, bear: 0.15, sideways: 0.28, high_vol: 0.10, anomaly: 0.05 };

const MOCK_EQUITY_DATA = Array.from({ length: 100 }, (_, i) => ({
  timestamp: Date.now() - (100 - i) * 3600000,
  equity: 100000 + Math.sin(i * 0.1) * 5000 + i * 200,
  regime: (['bull', 'bear', 'sideways', 'high_vol', 'anomaly'] as Regime[])[i % 5],
}));

const MOCK_AGENTS = [
  { id: 'fundamental', name: 'Fundamental', weight: 0.20, signal: 'buy' as const, confidence: 0.85, winRate: 0.72, sharpe: 1.8, pnl: 12500, status: 'active' as const, lastRun: '2026-07-22T12:00:00Z' },
  { id: 'quant', name: 'Quant', weight: 0.20, signal: 'strong_buy' as const, confidence: 0.92, winRate: 0.78, sharpe: 2.1, pnl: 18400, status: 'active' as const, lastRun: '2026-07-22T12:01:00Z' },
  { id: 'macro', name: 'Macro', weight: 0.15, signal: 'hold' as const, confidence: 0.65, winRate: 0.68, sharpe: 1.4, pnl: 8900, status: 'active' as const, lastRun: '2026-07-22T12:00:00Z' },
  { id: 'sentiment', name: 'Sentiment', weight: 0.10, signal: 'sell' as const, confidence: 0.58, winRate: 0.55, sharpe: 0.9, pnl: -3200, status: 'idle' as const, lastRun: '2026-07-22T11:55:00Z' },
  { id: 'technical', name: 'Technical', weight: 0.10, signal: 'hold' as const, confidence: 0.71, winRate: 0.62, sharpe: 1.2, pnl: 5600, status: 'active' as const, lastRun: '2026-07-22T12:00:00Z' },
];

export default function App() {
  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#0a0a0f', color: '#e0e0ff' }}>
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ color: '#e0e0ff' }}>
          AstroFin Sentinel V5 — Command Center
        </Typography>

        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 8 }}>
            <Box sx={{ height: 400, width: '100%', mb: 3 }}>
              <SessionTable />
            </Box>
            <Box sx={PANEL_STYLE}>
              <EquityCurve data={MOCK_EQUITY_DATA} height={260} />
            </Box>
            <Box sx={{ mt: 3 }}>
              <AgentPerformanceGrid agents={MOCK_AGENTS} />
            </Box>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <Box sx={{ ...PANEL_STYLE, mb: 3 }}>
              <Typography variant="subtitle2" sx={{ color: '#8899aa', mb: 2, textTransform: 'uppercase', letterSpacing: 1 }}>
                Market Regime
              </Typography>
              <RegimeRadar probabilities={MOCK_REGIME_PROBS} currentRegime="bull" />
            </Box>
            <Box sx={PANEL_STYLE}>
              <SafetyGateCard status="safe" riskPct={2.0} maxDrawdown={-5.2} var95={-3.1} leverage={1.5} />
            </Box>
          </Grid>
        </Grid>

        <ContextDrawer />
      </Container>
    </Box>
  );
}
