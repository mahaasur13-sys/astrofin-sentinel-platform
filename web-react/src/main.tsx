import { Component, StrictMode } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { createRoot } from 'react-dom/client';
import { Provider } from 'react-redux';
import { store } from './app/store';
import App from './App';
import './index.css';

/* ------------------------------------------------------------------ *
 * P0 — Bootstrap instrumentation
 * ------------------------------------------------------------------ *
 * Каждый этап загрузки логируется с префиксом [AstroFin], чтобы при
 * "чёрном экране" можно было по консоли (F12) определить, на каком
 * шаге всё оборвалось. Если логов [AstroFin] нет вовсе — проблема до
 * выполнения JS (HTML/CSP/сборка Vite).
 * ------------------------------------------------------------------ */
const log = (msg: string, ...rest: unknown[]) =>
  console.log(`[AstroFin] ${msg}`, ...rest);

/**
 * Bare-metal fallback UI без React — используется, когда React вообще
 * не может смонтироваться (нет mount point, критический сбой рендера).
 */
function renderFatalFallback(title: string, detail: string) {
  const html = `
    <div style="min-height:100vh;display:flex;align-items:center;justify-content:center;
                background:#0a0612;color:#e6e0f0;font-family:system-ui,sans-serif;padding:24px;">
      <div style="max-width:640px;text-align:center;">
        <div style="font-size:2.5rem;margin-bottom:12px;">⚠️</div>
        <h1 style="font-size:1.2rem;margin:0 0 8px;color:#c084fc;">${title}</h1>
        <p style="font-size:0.85rem;color:#a99cc0;line-height:1.6;white-space:pre-wrap;">${detail}</p>
        <button id="astrofin-reload"
          style="margin-top:20px;padding:8px 20px;border:1px solid #7b2cff;border-radius:8px;
                 background:#7b2cff;color:#fff;font-size:0.85rem;cursor:pointer;">
          Перезагрузить
        </button>
      </div>
    </div>`;
  document.body.innerHTML = html;
  const btn = document.getElementById('astrofin-reload');
  if (btn) btn.addEventListener('click', () => window.location.reload());
}

/* ------------------------------------------------------------------ *
 * P4 — RootErrorBoundary
 * ------------------------------------------------------------------ *
 * Ловит любые ошибки рендера в дереве React и показывает fallback
 * вместо чёрного экрана: сообщение, стек и кнопку «Перезагрузить».
 * ------------------------------------------------------------------ */
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  info: ErrorInfo | null;
}

class RootErrorBoundary extends Component<{ children: ReactNode }, ErrorBoundaryState> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null, info: null };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[AstroFin] Root render error:', error, info);
    this.setState({ error, info });
  }

  handleReload = () => {
    // Сброс состояния + полная перезагрузка (на случай застрявшего кэша)
    this.setState({ hasError: false, error: null, info: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      const { error, info } = this.state;
      return (
        <div
          style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#0a0612',
            color: '#e6e0f0',
            fontFamily: 'system-ui, sans-serif',
            padding: 24,
          }}
        >
          <div style={{ maxWidth: 720, width: '100%' }}>
            <div style={{ fontSize: '2.5rem', textAlign: 'center', marginBottom: 12 }}>⚠️</div>
            <h1 style={{ fontSize: '1.2rem', textAlign: 'center', margin: '0 0 8px', color: '#c084fc' }}>
              Ошибка приложения
            </h1>
            <p style={{ fontSize: '0.9rem', textAlign: 'center', color: '#f87171', marginBottom: 16 }}>
              {error?.message || 'Неизвестная ошибка рендера'}
            </p>
            {(error?.stack || info?.componentStack) && (
              <pre
                style={{
                  fontSize: '0.7rem',
                  color: '#a99cc0',
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  borderRadius: 8,
                  padding: 12,
                  maxHeight: 260,
                  overflow: 'auto',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {error?.stack}
                {info?.componentStack}
              </pre>
            )}
            <div style={{ textAlign: 'center', marginTop: 20 }}>
              <button
                onClick={this.handleReload}
                style={{
                  padding: '8px 20px',
                  border: '1px solid #7b2cff',
                  borderRadius: 8,
                  background: '#7b2cff',
                  color: '#fff',
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                }}
              >
                Перезагрузить
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/* ------------------------------------------------------------------ *
 * Bootstrap
 * ------------------------------------------------------------------ */
function bootstrap() {
  log('Phase 0 start');

  // P0 — Mount point check: без #root React смонтироваться не сможет.
  const rootEl = document.getElementById('root');
  if (!rootEl) {
    console.error('[AstroFin] Fatal: mount point #root not found');
    renderFatalFallback(
      'Не найден элемент #root',
      'HTML-страница загрузилась без контейнера #root. Проверьте index.html и корректность сборки Vite.',
    );
    return;
  }
  log('Phase 0.1: mount point OK');

  let root: ReturnType<typeof createRoot>;
  try {
    root = createRoot(rootEl);
    log('Phase 0.2: React root created');
  } catch (e) {
    console.error('[AstroFin] Fatal: createRoot failed', e);
    renderFatalFallback(
      'Не удалось инициализировать React',
      String((e as Error)?.message ?? e),
    );
    return;
  }

  log('Phase 0 complete');
  log('Bootstrap: mounting <App />');

  try {
    root.render(
      <StrictMode>
        <RootErrorBoundary>
          <Provider store={store}>
            <App />
          </Provider>
        </RootErrorBoundary>
      </StrictMode>,
    );
    log('Bootstrap: render() called');
  } catch (e) {
    // Синхронные ошибки во время render() (до того как ErrorBoundary успеет смонтироваться)
    console.error('[AstroFin] Fatal: initial render threw', e);
    renderFatalFallback('Сбой при первом рендере', String((e as Error)?.message ?? e));
  }
}

bootstrap();
