export type SafetyStatus = 'safe' | 'warning' | 'danger' | 'stopped';

export interface SafetyTrigger {
  time: string;
  reason: string;
}

export interface SafetyGate {
  status: SafetyStatus;
  riskPct: number;
  maxDrawdown: number;
  var95: number;
  leverage: number;
  triggers: SafetyTrigger[];
}

export interface SafetyUpdate {
  status: SafetyStatus;
  maxDrawdown: number;
  dailyLoss: number;
  leverage: number;
}
