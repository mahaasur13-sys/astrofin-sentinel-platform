export type Regime = 'bull' | 'bear' | 'sideways' | 'high_vol' | 'anomaly';

export interface RegimeProbability {
  regime: Regime;
  probability: number;
}

export interface RegimeUpdate {
  regime: Regime;
  probabilities: RegimeProbability[];
  confidence: number;
}

export const REGIME_LABELS: Record<Regime, string> = {
  bull: 'BULL',
  bear: 'BEAR',
  sideways: 'SIDEWAYS',
  high_vol: 'HIGH VOL',
  anomaly: 'ANOMALY',
};

export const REGIME_COLORS: Record<Regime, string> = {
  bull: '#00ff9d',
  bear: '#ff2d55',
  sideways: '#00b8ff',
  high_vol: '#ffd000',
  anomaly: '#ff2a6d',
};

export const REGIME_DESCRIPTIONS: Record<Regime, string> = {
  bull: 'Бычий тренд',
  bear: 'Медвежий тренд',
  sideways: 'Флэт / Боковик',
  high_vol: 'Высокая волатильность',
  anomaly: 'Аномалия рынка',
};
