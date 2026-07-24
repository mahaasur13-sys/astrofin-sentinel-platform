import type { ReactNode } from 'react';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { ErrorFallback } from './ErrorFallback';

type WidgetStatus = 'loading' | 'error' | 'success';

interface WidgetWrapperProps {
  status: WidgetStatus;
  error?: Error | string;
  onRetry?: () => void;
  title?: string;
  className?: string;
  skeletonCount?: number;
  children: ReactNode;
}

export function WidgetWrapper({
  status,
  error,
  onRetry,
  title,
  className = '',
  skeletonCount = 1,
  children,
}: WidgetWrapperProps) {
  if (status === 'loading') {
    return (
      <div className={className}>
        {title && (
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-gray-400">
            {title}
          </h3>
        )}
        <div className="flex flex-col gap-3">
          {Array.from({ length: skeletonCount }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      </div>
    );
  }

  if (status === 'error' && error) {
    return (
      <div className={className}>
        {title && (
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-gray-400">
            {title}
          </h3>
        )}
        <ErrorFallback message={typeof error === 'string' ? error : error.message} onRetry={onRetry} />
      </div>
    );
  }

  return <div className={className}>{children}</div>;
}
