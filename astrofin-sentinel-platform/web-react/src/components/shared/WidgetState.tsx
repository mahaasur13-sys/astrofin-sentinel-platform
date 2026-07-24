import { AlertTriangle, RefreshCw } from 'lucide-react';
import type { ReactNode } from 'react';

interface WidgetStateProps {
  loading: boolean;
  error: string | null;
  isEmpty?: boolean;
  emptyMessage?: string;
  skeleton?: ReactNode;
  children: ReactNode;
  onRetry?: () => void;
  retryLabel?: string;
}

export function WidgetState({
  loading,
  error,
  isEmpty = false,
  emptyMessage = 'No data available',
  skeleton,
  children,
  onRetry,
  retryLabel = 'Retry',
}: WidgetStateProps) {
  if (loading && skeleton) {
    return <>{skeleton}</>;
  }

  if (loading) {
    return (
      <div className="flex min-h-[120px] items-center justify-center text-muted-foreground" role="status" aria-label="Loading">
        <div className="size-6 animate-spin rounded-full border-2 border-muted-foreground/30 border-t-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="flex min-h-[120px] flex-col items-center justify-center gap-2 rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-center"
        role="alert"
      >
        <AlertTriangle className="size-6 text-destructive" />
        <p className="text-sm text-destructive-foreground">{error}</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center gap-1.5 rounded-md bg-destructive px-3 py-1.5 text-xs font-medium text-destructive-foreground transition-colors hover:bg-destructive/90"
            aria-label={retryLabel}
          >
            <RefreshCw className="size-3" />
            {retryLabel}
          </button>
        )}
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className="flex min-h-[80px] items-center justify-center text-sm text-muted-foreground">
        {emptyMessage}
      </div>
    );
  }

  return <>{children}</>;
}
