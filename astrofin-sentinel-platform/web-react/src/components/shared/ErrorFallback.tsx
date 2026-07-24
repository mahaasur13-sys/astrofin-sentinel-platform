import { RefreshCw, AlertTriangle } from 'lucide-react';

interface ErrorFallbackProps {
  message: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorFallback({ message, onRetry, className = '' }: ErrorFallbackProps) {
  return (
    <div
      role="alert"
      className={`flex flex-col items-center justify-center gap-3 rounded-xl border border-red-500/20 bg-red-500/5 p-6 text-center ${className}`}
    >
      <AlertTriangle className="size-8 text-red-400" aria-hidden="true" />
      <p className="text-sm text-muted-foreground">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 rounded-lg bg-red-500/10 px-4 py-2 text-sm font-medium text-red-400 transition-colors hover:bg-red-500/20"
          aria-label="Повторить загрузку"
        >
          <RefreshCw className="size-4" aria-hidden="true" />
          Retry
        </button>
      )}
    </div>
  );
}
