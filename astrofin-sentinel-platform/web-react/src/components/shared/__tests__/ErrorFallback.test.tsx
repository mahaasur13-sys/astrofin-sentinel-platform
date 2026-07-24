import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorFallback } from '@/components/shared/ErrorFallback';

describe('ErrorFallback', () => {
  it('should render error message', () => {
    render(<ErrorFallback message="Something went wrong" />);
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('should render retry button when onRetry provided', () => {
    const onRetry = () => {};
    render(<ErrorFallback message="Error" onRetry={onRetry} />);
    expect(screen.getByRole('button', { name: /повторить/i })).toBeInTheDocument();
  });

  it('should not render retry button when no onRetry', () => {
    render(<ErrorFallback message="Error" />);
    expect(screen.queryByRole('button', { name: /retry/i })).toBeNull();
  });

  it('should call onRetry when clicked', () => {
    let called = false;
    render(<ErrorFallback message="Error" onRetry={() => { called = true; }} />);
    fireEvent.click(screen.getByRole('button', { name: /повторить/i }));
    expect(called).toBe(true);
  });

  it('should have alert role', () => {
    render(<ErrorFallback message="Error" />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });
});
