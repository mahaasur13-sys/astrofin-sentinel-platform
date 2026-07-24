import type { Regime } from './regime';

export type Ticker = string;
export type Timeframe = '1m' | '5m' | '15m' | '1H' | '4H' | '1D' | '1W';
export type DashboardMode = 'LIVE' | 'BACKTEST' | 'PAPER' | 'OPTIMIZE';

export interface EquityPoint {
  date: string;
  equity: number;
  regime: Regime;
}

export interface WatchlistItem {
  ticker: Ticker;
  changePercent: number;
}
