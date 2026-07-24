import { type ReactNode } from 'react';
import { SkeletonCard } from './Skeleton';
import { ErrorFallback } from '@/components/shared/ErrorFallback';

interface WidgetStateProps {
  isLoading: boolean;
  error: string | null;
  children: ReactNode;
  onRetry?: () => void;
  loadingRows?: number;
  className?: string;
}

export function WidgetState({
  isLoading,
  error,
  children,
  onRetry,
  loadingRows = 1,
  className = '',
}: WidgetStateProps) {
  if (isLoading) {
    return (
      <div className={className}>
        {Array.from({ length: loadingRows }, (_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className={className}>
        <ErrorFallback message={error} onRetry={onRetry} />
      </div>
    );
  }

  return <>{children}</>;
}
