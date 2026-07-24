interface BudgetThreshold {
  metric: string;
  maxValue: number;
  unit: string;
  severity: 'error' | 'warn';
}

export const PERFORMANCE_BUDGET: BudgetThreshold[] = [
  { metric: 'main-bundle-gzip', maxValue: 180, unit: 'KB', severity: 'error' },
  { metric: 'LCP', maxValue: 2500, unit: 'ms', severity: 'error' },
  { metric: 'CLS', maxValue: 0.1, unit: 'score', severity: 'error' },
  { metric: 'INP', maxValue: 200, unit: 'ms', severity: 'error' },
  { metric: 'FCP', maxValue: 1800, unit: 'ms', severity: 'warn' },
  { metric: 'TTFB', maxValue: 800, unit: 'ms', severity: 'warn' },
  { metric: 'total-css-size', maxValue: 50, unit: 'KB', severity: 'warn' },
  { metric: 'total-js-size', maxValue: 350, unit: 'KB', severity: 'warn' },
  { metric: 'third-party-js-size', maxValue: 100, unit: 'KB', severity: 'error' },
];

export function checkBudget(
  metric: string,
  value: number,
): { pass: boolean; severity: 'error' | 'warn'; message: string } {
  const threshold = PERFORMANCE_BUDGET.find((b) => b.metric === metric);
  if (!threshold) {
    return { pass: true, severity: 'warn', message: `No budget defined for ${metric}` };
  }

  const pass = value <= threshold.maxValue;
  const sign = value > threshold.maxValue ? '>' : '≤';
  const message = `[Budget] ${metric}: ${value}${threshold.unit} ${sign} ${threshold.maxValue}${threshold.unit} [${pass ? 'PASS' : 'FAIL'}]`;

  return { pass, severity: threshold.severity, message };
}
