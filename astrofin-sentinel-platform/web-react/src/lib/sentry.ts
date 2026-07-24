import * as Sentry from '@sentry/browser';

let initialized = false;

export function initSentry(): void {
  if (initialized) return;

  const dsn = import.meta.env.VITE_SENTRY_DSN;
  if (!dsn) {
    if (import.meta.env.DEV) {
      console.log('[Sentry] DSN not set — skipping');
    }
    return;
  }

  Sentry.init({
    dsn,
    environment: import.meta.env.MODE,
    release: import.meta.env.VITE_APP_VERSION ?? 'dev',
    tracesSampleRate: import.meta.env.PROD ? 0.1 : 1.0,
    replaysSessionSampleRate: 0.01,
    replaysOnErrorSampleRate: 1.0,
    beforeSend(event) {
      // Strip PII: remove user-agent, IP, referrer
      if (event.request) {
        delete event.request.headers?.['User-Agent'];
        delete event.request.headers?.Referer;
      }
      // Redact sensitive path segments
      if (event.request?.url) {
        event.request.url = event.request.url.replace(
          /(token|key|secret|password|auth)=[^&\s]+/gi,
          '$1=[REDACTED]',
        );
      }
      return event;
    },
  });

  initialized = true;
  console.log('[Sentry] Initialized');
}

export function captureError(
  error: Error,
  context?: Record<string, unknown>,
): void {
  if (!initialized) {
    console.warn('[Sentry] Not initialized, logging to console:', error.message);
    return;
  }
  Sentry.captureException(error, {
    extra: {
      ...context,
      timestamp: new Date().toISOString(),
    },
  });
}

export function isInitialized(): boolean {
  return initialized;
}
