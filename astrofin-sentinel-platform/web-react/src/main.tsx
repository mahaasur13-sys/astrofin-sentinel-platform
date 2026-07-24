import './index.css';
import '@fontsource/jetbrains-mono';
import { StrictMode, Component, type ReactNode, type ErrorInfo } from 'react';
import { createRoot } from 'react-dom/client';
import { initSentry } from '@/lib/sentry';
import { featureFlags } from '@/lib/feature-flags';
import { initWebVitals } from '@/lib/web-vitals';
import App from './App';

/* ─── P0 Bootstrap instrumentation ─── */
console.log('[AstroFin] Bootstrap: Phase 0 start');

/* P0: Check mount point exists */
const rootEl = document.getElementById('root');
if (!rootEl) {
  console.error('[AstroFin] FATAL P0: #root element not found in DOM');
  document.body.innerHTML = (
    '<div style="display:flex;align-items:center;justify-content:center;'
    + 'height:100vh;background:#0a0a0f;color:#ff6b6b;font-family:monospace;'
    + 'padding:2rem;text-align:center">'
    + 'FATAL: #root element missing in index.html'
    + '</div>'
  );
  throw new Error('P0: Root mount point #root missing');
}
console.log('[AstroFin] P0 OK: #root element found');

/* P1: Feature Flags + Sentry + Web Vitals with try/catch isolation */
try {
  featureFlags.init();
  console.log('[AstroFin] Phase 0.1: Feature flags ready');
} catch (e) {
  console.error('[AstroFin] P1: Feature flags init failed:', e);
}

try {
  initSentry();
  console.log('[AstroFin] Phase 0.2: Sentry initialized');
} catch (e) {
  console.error('[AstroFin] P1: Sentry init failed:', e);
  // Set flag for later use — Sentry will capture all unhandled exceptions
}

try {
  initWebVitals();
  console.log('[AstroFin] Phase 0.3: Web Vitals monitoring started');
} catch (e) {
  console.error('[AstroFin] P1: Web Vitals init failed:', e);
  // Non-critical — dashboards still work without vitals
}

console.log('[AstroFin] Phase 0 complete');

/* ─── P3 diagnostic: verify Zustand stores are alive ─── */
try {
  import('@/stores/dashboard.store').then(({ useDashboardStore }) => {
    const state = useDashboardStore.getState();
    console.log('[AstroFin] P3 check: Zustand dashboard store ready',
      { connectionStatus: state.connectionStatus, ticker: state.ticker });
  });
} catch (e) {
  console.error('[AstroFin] P3: Zustand store init failed:', e);
}

/* ─── Root Error Boundary ─── */
class RootErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[AstroFin] Root render error:', error.message);
    console.error('[AstroFin] Component stack:', info.componentStack);

    import('@/lib/sentry')
      .then(({ captureError }) => {
        captureError(error, {
          componentStack: info.componentStack ?? 'unavailable',
          phase: 'root-bootstrap',
        });
      })
      .catch(() => {
        console.warn('[AstroFin] Sentry capture failed — logging to console');
      });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100vh',
            background: '#0a0a0f',
            color: '#e0e0ff',
            fontFamily: 'JetBrains Mono, monospace',
            padding: '2rem',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>⚠</div>
          <h1 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>
            Критическая ошибка загрузки
          </h1>
          <pre
            style={{
              maxWidth: '600px',
              overflow: 'auto',
              fontSize: '0.85rem',
              color: '#ff6b6b',
              background: 'rgba(255,107,107,0.1)',
              padding: '1rem',
              borderRadius: '8px',
              marginBottom: '1.5rem',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
            }}
          >
            {this.state.error?.message ?? 'Неизвестная ошибка'}
          </pre>
          <button
            type="button"
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.reload();
            }}
            style={{
              padding: '12px 24px',
              background: '#7b2cff',
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '1rem',
              fontWeight: 600,
            }}
          >
            Перезагрузить
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

/* ─── Mount ─── */
console.log('[AstroFin] Bootstrap: mounting <App /> via createRoot');

createRoot(rootEl).render(
  <StrictMode>
    <RootErrorBoundary>
      <App />
    </RootErrorBoundary>
  </StrictMode>,
);

console.log('[AstroFin] Bootstrap: render() called');
