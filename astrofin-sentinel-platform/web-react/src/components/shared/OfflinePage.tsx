import { useState, useEffect, useCallback } from 'react';
import { WifiOff, RefreshCw } from 'lucide-react';

export function OfflinePage() {
  const [retrying, setRetrying] = useState(false);
  const [online, setOnline] = useState(navigator.onLine);

  useEffect(() => {
    const onOnline = () => setOnline(true);
    const onOffline = () => setOnline(false);
    window.addEventListener('online', onOnline);
    window.addEventListener('offline', onOffline);
    return () => {
      window.removeEventListener('online', onOnline);
      window.removeEventListener('offline', onOffline);
    };
  }, []);

  const retry = useCallback(() => {
    setRetrying(true);
    window.location.reload();
  }, []);

  if (online) return null;

  return (
    <div
      className="flex h-screen flex-col items-center justify-center bg-background px-4 text-center"
      role="alert"
      aria-live="assertive"
    >
      <div className="mb-6 rounded-full bg-muted p-6">
        <WifiOff className="size-12 text-muted-foreground" aria-hidden="true" />
      </div>

      <h1 className="mb-2 text-2xl font-bold text-foreground">
        No Internet Connection
      </h1>

      <p className="mb-8 max-w-sm text-sm text-muted-foreground">
        AstroFin Sentinel requires a connection to stream real-time agent
        signals and market data. Check your connection and try again.
      </p>

      <button
        type="button"
        onClick={retry}
        disabled={retrying}
        className="inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
        aria-label="Retry connection"
      >
        <RefreshCw className={`size-4 ${retrying ? 'animate-spin' : ''}`} aria-hidden="true" />
        {retrying ? 'Reconnecting…' : 'Retry'}
      </button>

      <p className="mt-6 text-xs text-muted-foreground">
        Offline mode is limited. Pages you previously visited may be available
        from cache.
      </p>
    </div>
  );
}
