import { onCLS, onLCP, onINP, onFCP, onTTFB, type Metric } from 'web-vitals';

const VITALS_ENDPOINT = '/api/v1/metrics/vitals';

interface VitalRecord {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  delta: number;
  timestamp: number;
}

const buffer: VitalRecord[] = [];
let flushTimer: ReturnType<typeof setTimeout> | null = null;
let lastFlush = 0;
const FLUSH_INTERVAL_MS = 30_000;

function flush(): void {
  if (buffer.length === 0) return;
  const batch = buffer.splice(0);
  lastFlush = Date.now();

  if (import.meta.env.DEV) {
    console.debug('[WebVitals] Batch:', batch.map((v) => `${v.name}=${v.value}(${v.rating})`).join(', '));
    return;
  }

  fetch(VITALS_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ vitals: batch, timestamp: Date.now() }),
    keepalive: true,
  }).catch(() => {
    // Beacon failed — silently drop
  });
}

function scheduleFlush(): void {
  if (flushTimer) return;
  flushTimer = setTimeout(() => {
    flushTimer = null;
    flush();
  }, FLUSH_INTERVAL_MS);
}

let initialized = false;

export function initWebVitals(): void {
  if (initialized) return;
  initialized = true;

  const handleMetric = (metric: Metric) => {
    const record: VitalRecord = {
      name: metric.name,
      value: metric.value,
      rating: metric.rating as VitalRecord['rating'],
      delta: metric.delta,
      timestamp: Date.now(),
    };

    buffer.push(record);
    scheduleFlush();

    // Log first meaningful paint immediately
    if (metric.name === 'FCP' || metric.name === 'LCP') {
      console.info(`[WebVitals] ${metric.name}: ${metric.value.toFixed(1)} (${metric.rating})`);
    }
  };

  onCLS(handleMetric);
  onLCP(handleMetric);
  onINP(handleMetric);
  onFCP(handleMetric);
  onTTFB(handleMetric);

  // Flush before page unload
  window.addEventListener('beforeunload', flush);
  window.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') flush();
  });

  console.info('[WebVitals] Monitoring started');
}

export function getVitalBuffer(): readonly VitalRecord[] {
  return buffer;
}
