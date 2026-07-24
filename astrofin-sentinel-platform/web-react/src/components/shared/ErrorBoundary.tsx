import { Component, type ReactNode, type ErrorInfo } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, info: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    this.props.onError?.(error, info);
    console.error('[ErrorBoundary]', error.message, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback ?? (
          <div className="rounded-lg border border-red-500/30 bg-red-950/40 p-6 text-red-200">
            <h3 className="mb-2 text-lg font-semibold">Widget Error</h3>
            <p className="text-sm text-red-300/80">{this.state.error?.message ?? 'Unknown error'}</p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="mt-3 rounded bg-red-800 px-3 py-1.5 text-xs hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        )
      );
    }

    return this.props.children;
  }
}
