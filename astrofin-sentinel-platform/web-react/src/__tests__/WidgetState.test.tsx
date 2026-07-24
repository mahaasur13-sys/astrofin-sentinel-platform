import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WidgetState } from '@/components/ui/WidgetState';

describe('WidgetState', () => {
  it('renders loading skeletons when isLoading', () => {
    render(
      <WidgetState isLoading error={null}>
        <div>Content</div>
      </WidgetState>,
    );
    expect(screen.queryByText('Content')).not.toBeInTheDocument();
    const skeletons = document.querySelectorAll('[aria-busy="true"]');
    expect(skeletons.length).toBeGreaterThanOrEqual(1);
  });

  it('renders error fallback when error is set', () => {
    render(
      <WidgetState isLoading={false} error="Failed to load">
        <div>Content</div>
      </WidgetState>,
    );
    expect(screen.getByText('Failed to load')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('renders children on success', () => {
    render(
      <WidgetState isLoading={false} error={null}>
        <div>Widget Content</div>
      </WidgetState>,
    );
    expect(screen.getByText('Widget Content')).toBeInTheDocument();
  });

  it('renders multiple loading rows', () => {
    render(
      <WidgetState isLoading error={null} loadingRows={3}>
        <div>Content</div>
      </WidgetState>,
    );
    const skeletons = document.querySelectorAll('[aria-busy="true"]');
    expect(skeletons.length).toBe(3);
  });
});
